#!/usr/bin/env python3
"""Asymptote render client for an asyagent HTTP service.

Sends Asymptote source code to a ``/v1/render`` endpoint (the asyagent
service described in vendor/asyagent_README.md) and saves the rendered
output as SVG / PDF / PNG to a file.

Design goals
------------
* **Pure standard library** — no ``pip install``, runs on Python 3.10+.
  Matches the zero-dependency philosophy of asyagent itself, so the skill
  can invoke it on any machine without setup.
* **Inline binary mode only.** This skill's server uses local storage,
  so URL mode is irrelevant, and base64 JSON responses add a needless
  encoding layer. The request body is sent as ``text/plain`` (the
  simplest, most common body type — matches the canonical curl in the
  README), and the response is raw bytes with a format-appropriate
  Content-Type.
* **Rich error reporting for agent debugging.** AsyRenderError subclasses
  encode the HTTP status, asyagent error code, server message, compiler
  ``detail`` (the most useful field for fixing broken source), and the
  ``x-fn-trace-id`` request trace. The stringified error is a multi-line
  report written to stderr so a calling skill agent can read it and act.

Configuration
-------------
* ``ASY_BASE_URL`` (env) or ``--base-url`` — asyagent base URL.
  Default: ``https://fnfcbfs7sh.fn.6scloud.com``.
* ``ASY_API_KEY`` (env) or ``--api-key`` — bearer token. **Required.**
  Never hardcode credentials in this file; pass them in.

Exit codes
----------
0  success
1  unexpected/internal error
2  configuration error (missing key, bad format, no source, file not found)
3  network error (DNS, connection refused, timeout, TLS)
4  HTTP error (4xx/5xx from server — auth, compile, bad request, server fault)
5  output write error (could not save the rendered file)

Usage examples
--------------
    # Render a file to SVG (default format), default output path
    asy_render.py -f diagram.asy

    # Render inline source to PDF at a specific path
    asy_render.py -s 'size(5cm); draw(unitcircle);' -F pdf -o circle.pdf

    # Pipe source over stdin, write PNG to stdout (binary)
    cat diagram.asy | asy_render.py -F png -o - > diagram.png

    # Same, but a skill agent can also import the function directly:
    #   from asy_render import render
    #   result = render("size(5cm); draw(unitcircle);", format="svg", out="c.svg")
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_BASE_URL = "https://fnfcbfs7sh.fn.6scloud.com"
DEFAULT_FORMAT = "svg"

# The skill only needs these three output formats. The asyagent server itself
# also supports eps/jpg/jpeg, but we deliberately restrict the surface here to
# keep the CLI simple and the validation tight.
SUPPORTED_FORMATS: Tuple[str, ...] = ("svg", "pdf", "png")

EXTENSION = {"svg": ".svg", "pdf": ".pdf", "png": ".png"}
MIME_BY_FORMAT = {
    "svg": "image/svg+xml",
    "pdf": "application/pdf",
    "png": "image/png",
}

# Distinct exit codes let a calling skill branch on failure category.
EXIT_OK = 0
EXIT_INTERNAL = 1
EXIT_CONFIG = 2
EXIT_NETWORK = 3
EXIT_HTTP = 4
EXIT_OUTPUT = 5


# ---------------------------------------------------------------------------
# Error hierarchy
# ---------------------------------------------------------------------------

class AsyRenderError(Exception):
    """Base class for all render-client failures."""


class AsyConfigError(AsyRenderError):
    """Invalid client configuration: missing key, bad format, no source, etc."""


class AsyNetworkError(AsyRenderError):
    """Transport-level failure: DNS, connection refused, timeout, TLS error."""


class AsyOutputError(AsyRenderError):
    """The render succeeded but the output file could not be written."""


class AsyHTTPError(AsyRenderError):
    """The server returned a non-2xx HTTP response.

    Carries every piece of diagnostic information the server exposes so a
    calling skill agent can read ``str(self)`` on stderr and decide what to
    fix: the source code (compile errors), the request (bad format), the
    credentials (auth), or just retry (server fault).
    """

    def __init__(
        self,
        *,
        status: int,
        reason: Optional[str],
        body: str,
        headers,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        error_detail: Optional[str] = None,
        trace_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        fmt: Optional[str] = None,
        source_len: Optional[int] = None,
    ) -> None:
        self.status = status
        self.reason = reason
        self.body = body
        self.headers = headers
        self.error_code = error_code
        self.error_message = error_message
        self.error_detail = error_detail
        self.trace_id = trace_id
        self.endpoint = endpoint
        self.format = fmt
        self.source_len = source_len
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        label = self.error_message or self.reason or "request failed"
        code_part = f" [error code: {self.error_code}]" if self.error_code else ""
        lines = [
            f"Asymptote rendering failed: {label} (HTTP {self.status}{code_part})",
        ]
        if self.endpoint:
            lines.append(f"  Endpoint:        {self.endpoint}")
        if self.trace_id:
            lines.append(f"  Trace ID:        {self.trace_id}")
        if self.format:
            lines.append(f"  Output format:   {self.format}")
        if self.source_len is not None:
            lines.append(f"  Source size:     {self.source_len} bytes")

        if self.error_detail:
            lines.append("  Server detail:")
            for line in str(self.error_detail).rstrip("\n").splitlines() or ["(empty)"]:
                lines.append(f"    {line}")
        elif self.body and self.body != self.error_message:
            lines.append("  Response body:")
            for line in self.body.rstrip("\n").splitlines() or ["(empty)"]:
                lines.append(f"    {line}")

        hint = self._hint()
        if hint:
            lines.append(f"  Hint: {hint}")
        return "\n".join(lines)

    def _hint(self) -> str:
        if self.status in (401, 403):
            return (
                "authentication/authorization failed — verify your API key "
                "(ASY_API_KEY env var or --api-key) is correct and not expired"
            )
        if self.status == 404:
            return (
                "endpoint not found — check --base-url / ASY_BASE_URL points to "
                "the asyagent service and that /v1/render is exposed"
            )
        if self.status == 413:
            return "source body too large — trim the Asymptote source"
        if self.status == 422 or self.error_code == "compile_failed":
            return (
                "the Asymptote source failed to compile — read the compiler "
                "output above; it reports the exact file, line, and column"
            )
        if self.error_code == "unsupported_format":
            return "requested output format is not supported — use svg, pdf, or png"
        if 500 <= self.status < 600:
            return (
                "server-side error — retry briefly; if it persists the asyagent "
                "service may be overloaded or misconfigured"
            )
        if 400 <= self.status < 500:
            return "client request was rejected — see the server detail above"
        return ""


class AsyAuthError(AsyHTTPError):
    """401/403 — authentication or authorization failed."""


class AsyCompileError(AsyHTTPError):
    """422 — Asymptote source failed to compile."""


class AsyServerError(AsyHTTPError):
    """5xx — server fault."""


class AsyBadRequestError(AsyHTTPError):
    """Other 4xx — malformed or unsupported request (not auth, not compile)."""


def _classify_http_error(status: int, error_code: Optional[str]):
    """Pick the most specific AsyHTTPError subclass for a given response."""
    if status in (401, 403):
        return AsyAuthError
    if status == 422 or error_code == "compile_failed":
        return AsyCompileError
    if 500 <= status < 600:
        return AsyServerError
    return AsyBadRequestError


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass
class RenderResult:
    """Successful render output."""

    format: str
    mime: str
    data: bytes
    size: int
    filename: Optional[str] = None
    files: int = 1
    elapsed: float = 0.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_error_body(body_bytes: bytes) -> Tuple[Optional[str], Optional[str], Optional[str], str]:
    """Parse an HTTP error response into (code, message, detail, raw_text).

    asyagent emits a JSON envelope:
        {"error": {"code": "...", "message": "...", "detail": "..."}}
    but the gateway in front returns plain bodies like ``"Access forbidden"``
    (a quoted JSON string) on 403. We handle both, plus non-JSON bodies, and
    never raise — error parsing must itself be robust.
    """
    raw_text = body_bytes.decode("utf-8", errors="replace").strip()
    if not raw_text:
        return None, None, None, raw_text
    try:
        parsed = json.loads(raw_text)
    except (ValueError, json.JSONDecodeError):
        return None, None, None, raw_text

    if isinstance(parsed, dict) and isinstance(parsed.get("error"), dict):
        err = parsed["error"]
        code = err.get("code") if isinstance(err.get("code"), str) else None
        message = err.get("message") if isinstance(err.get("message"), str) else None
        detail = err.get("detail")
        if detail is not None and not isinstance(detail, str):
            try:
                detail = json.dumps(detail, ensure_ascii=False)
            except (TypeError, ValueError):
                detail = str(detail)
        return code, message, detail, raw_text

    if isinstance(parsed, str):
        return None, parsed, None, raw_text

    # Any other JSON shape — fall back to the raw text as the message.
    return None, raw_text, None, raw_text


def _parse_filename_from_disposition(value: str) -> Optional[str]:
    """Extract the filename from a Content-Disposition header value."""
    if not value:
        return None
    for part in value.split(";"):
        part = part.strip()
        if part.lower().startswith("filename="):
            token = part[len("filename="):].strip()
            if len(token) >= 2 and token[0] in "\"'" and token[-1] == token[0]:
                token = token[1:-1]
            return token or None
    return None


# ---------------------------------------------------------------------------
# Core render function
# ---------------------------------------------------------------------------

def render(
    source: str,
    *,
    format: str = DEFAULT_FORMAT,
    out: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    dpi: Optional[int] = None,
    timeout: Optional[int] = None,
    filename: Optional[str] = None,
    connect_timeout: float = 30.0,
) -> RenderResult:
    """Render Asymptote ``source`` and (optionally) save it to ``out``.

    Parameters
    ----------
    source:
        Asymptote source code. Must be non-empty.
    format:
        One of ``svg``, ``pdf``, ``png``. Default ``svg``.
    out:
        Output file path. ``None`` skips writing to disk — the caller can
        read the bytes from ``result.data`` directly. ``"-"`` writes raw
        bytes to stdout instead of a file.
    api_key:
        Bearer token. Falls back to ``$ASY_API_KEY``. Required.
    base_url:
        asyagent base URL. Falls back to ``$ASY_BASE_URL``, then
        :data:`DEFAULT_BASE_URL`.
    dpi:
        DPI for PNG output (passed via ``X-Asy-Dpi``). ``None`` uses the
        server default (150).
    timeout:
        Compile timeout in seconds (``X-Asy-Timeout``). ``None`` = server default.
    filename:
        Suggested filename (``X-Asy-Filename``).
    connect_timeout:
        Client-side HTTP socket timeout in seconds.

    Returns
    -------
    RenderResult
        Includes the raw bytes, detected format/mime, and elapsed time.

    Raises
    ------
    AsyConfigError, AsyNetworkError, AsyHTTPError (and subclasses),
    AsyOutputError — see module docstring for the hierarchy.
    """
    # --- validate inputs --------------------------------------------------
    if format not in SUPPORTED_FORMATS:
        raise AsyConfigError(
            f"unsupported output format {format!r} — supported: "
            f"{', '.join(SUPPORTED_FORMATS)}"
        )
    if source is None or source == "":
        raise AsyConfigError("empty Asymptote source — nothing to render")

    base_url = (base_url or os.environ.get("ASY_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
    api_key = api_key or os.environ.get("ASY_API_KEY")
    if not api_key:
        raise AsyConfigError(
            "missing API key — set the ASY_API_KEY environment variable or "
            "pass --api-key"
        )

    # --- build the request ------------------------------------------------
    url = f"{base_url}/v1/render"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "text/plain",
        "X-Asy-Format": format,
        "Accept": MIME_BY_FORMAT[format],
    }
    if dpi is not None:
        try:
            headers["X-Asy-Dpi"] = str(int(dpi))
        except (TypeError, ValueError):
            raise AsyConfigError(f"invalid dpi value: {dpi!r}") from None
    if timeout is not None:
        try:
            headers["X-Asy-Timeout"] = str(int(timeout))
        except (TypeError, ValueError):
            raise AsyConfigError(f"invalid timeout value: {timeout!r}") from None
    if filename:
        headers["X-Asy-Filename"] = filename

    body = source.encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers=headers, method="POST"
    )

    # --- send it ----------------------------------------------------------
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=connect_timeout) as resp:
            status = getattr(resp, "status", 200)
            resp_headers = resp.headers
            data = resp.read()
    except urllib.error.HTTPError as exc:
        # 4xx / 5xx — server returned an error envelope (or gateway text).
        try:
            err_body_bytes = exc.read()
        except Exception:
            err_body_bytes = b""
        code, msg, detail, raw_text = _parse_error_body(err_body_bytes)
        resp_headers = exc.headers
        trace_id = resp_headers.get("x-fn-trace-id") if resp_headers else None
        err_cls = _classify_http_error(exc.code, code)
        raise err_cls(
            status=exc.code,
            reason=exc.reason,
            body=raw_text,
            headers=resp_headers,
            error_code=code,
            error_message=msg,
            error_detail=detail,
            trace_id=trace_id,
            endpoint=f"POST {url}",
            fmt=format,
            source_len=len(body),
        ) from None
    except urllib.error.URLError as exc:
        reason = exc.reason
        reason_text = reason if isinstance(reason, str) else str(reason)
        if isinstance(reason, TimeoutError) or "timed out" in reason_text.lower():
            raise AsyNetworkError(
                f"network timeout contacting {url} after {connect_timeout}s: "
                f"{reason_text}"
            ) from None
        raise AsyNetworkError(
            f"network error contacting {url}: {reason_text}"
        ) from None
    except OSError as exc:
        # Covers connection resets, TLS handshake failures, etc.
        raise AsyNetworkError(
            f"network error contacting {url}: {type(exc).__name__}: {exc}"
        ) from None

    elapsed = time.monotonic() - start

    # --- success path: validate + persist ---------------------------------
    if not 200 <= status < 300:
        code, msg, detail, raw_text = _parse_error_body(data)
        raise AsyHTTPError(
            status=status,
            reason=getattr(resp, "reason", None),
            body=raw_text,
            headers=resp_headers,
            error_code=code,
            error_message=msg,
            error_detail=detail,
            trace_id=resp_headers.get("x-fn-trace-id") if resp_headers else None,
            endpoint=f"POST {url}",
            fmt=format,
            source_len=len(body),
        )
    if not data:
        raise AsyHTTPError(
            status=status,
            reason="empty response body",
            body="",
            headers=resp_headers,
            endpoint=f"POST {url}",
            fmt=format,
            source_len=len(body),
        )

    fmt_actual = (resp_headers.get("x-asy-format") or format).lower()
    if fmt_actual not in SUPPORTED_FORMATS:
        # Server returned a format we didn't ask for / don't support.
        raise AsyHTTPError(
            status=status,
            reason=f"unexpected format in response: {fmt_actual!r}",
            body="",
            headers=resp_headers,
            endpoint=f"POST {url}",
            fmt=format,
            source_len=len(body),
        )

    content_type = (resp_headers.get("content-type") or "").split(";")[0].strip()
    mime = content_type or MIME_BY_FORMAT.get(fmt_actual, "application/octet-stream")

    try:
        files_count = int(resp_headers.get("x-asy-files", "1"))
    except (TypeError, ValueError):
        files_count = 1

    disp_filename = _parse_filename_from_disposition(
        resp_headers.get("content-disposition", "")
    )

    result = RenderResult(
        format=fmt_actual,
        mime=mime,
        data=data,
        size=len(data),
        filename=disp_filename,
        files=files_count,
        elapsed=elapsed,
    )

    # --- write output (unless stdout mode) --------------------------------
    if out is not None and out != "-":
        out_path = _resolve_output_path(out, fmt_actual, filename)
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(data)
        except OSError as exc:
            raise AsyOutputError(
                f"failed to write output to {out_path}: {type(exc).__name__}: {exc}"
            ) from None
        result.filename = result.filename or out_path.name

    return result


def _resolve_output_path(out: str, fmt: str, requested_filename: Optional[str]) -> Path:
    """Resolve a user-provided ``--out`` value to a concrete file path."""
    path = Path(out)
    if path.is_dir():
        stem = requested_filename or "asy-output"
        return path / f"{stem}{EXTENSION[fmt]}"
    # No extension and path doesn't already exist as a file: append .<fmt>
    # so e.g. ``-o diagram`` becomes ``diagram.svg`` for svg output.
    if path.suffix == "" and not path.exists():
        return path.with_suffix(EXTENSION[fmt])
    return path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _read_source(args: argparse.Namespace) -> str:
    if args.file:
        path = Path(args.file)
        if not path.is_file():
            raise AsyConfigError(f"source file not found: {args.file}")
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            raise AsyConfigError(
                f"could not read source file {args.file}: {type(exc).__name__}: {exc}"
            ) from None
    if args.source is not None:
        return args.source
    # No --file / --source: read from stdin.
    raw = sys.stdin.read()
    if isinstance(raw, bytes):
        try:
            raw = raw.decode("utf-8")
        except UnicodeDecodeError:
            raise AsyConfigError("stdin input is not valid UTF-8") from None
    return raw


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="asy_render",
        description=(
            "Render Asymptote source to SVG/PDF/PNG via an asyagent HTTP "
            "service. Source is read from --file, --source, or stdin (in "
            "that order). Output goes to --out (default ./asy-output.<fmt>); "
            "use '--out -' to write raw bytes to stdout."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Environment:\n"
            f"  ASY_BASE_URL   asyagent base URL (default: {DEFAULT_BASE_URL})\n"
            "  ASY_API_KEY    bearer token (required)\n\n"
            "Exit codes:\n"
            "  0 success   1 internal   2 config   3 network   4 http   5 output\n\n"
            "Examples:\n"
            "  asy_render.py -f diagram.asy                      # -> asy-output.svg\n"
            "  asy_render.py -s 'size(5cm); draw(unitcircle);' -F pdf -o circle.pdf\n"
            "  cat diagram.asy | asy_render.py -F png -o - > diagram.png\n"
        ),
    )
    src = parser.add_mutually_exclusive_group()
    src.add_argument("-f", "--file", help="path to an .asy source file")
    src.add_argument(
        "-s", "--source",
        help="inline Asymptote source string (takes precedence over stdin)",
    )
    parser.add_argument(
        "-o", "--out",
        help=(
            "output file path; a directory or extension-less name gets "
            "'.<fmt>' appended; '-' writes raw bytes to stdout"
        ),
    )
    parser.add_argument(
        "-F", "--format", choices=SUPPORTED_FORMATS, default=DEFAULT_FORMAT,
        help=f"output format (default: {DEFAULT_FORMAT})",
    )
    parser.add_argument(
        "--dpi", type=int, default=None,
        help="DPI for PNG raster output (default: server default 150)",
    )
    parser.add_argument(
        "--timeout", type=int, default=None,
        help="compile timeout in seconds, sent to the server (X-Asy-Timeout)",
    )
    parser.add_argument(
        "--connect-timeout", type=float, default=30.0,
        help="client-side HTTP socket timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("ASY_BASE_URL", DEFAULT_BASE_URL),
        help=f"asyagent base URL (env: ASY_BASE_URL; default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--api-key", default=os.environ.get("ASY_API_KEY"),
        help="API key / bearer token (env: ASY_API_KEY)",
    )
    parser.add_argument(
        "--filename", default=None,
        help="suggested filename sent to the server (X-Asy-Filename)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="print extra diagnostics to stderr",
    )
    return parser


def main(argv: Optional[list] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Stage 1: read the source — failures here are config errors.
    try:
        source = _read_source(args)
    except AsyConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_CONFIG

    # Stage 2: render + persist.
    try:
        result = render(
            source,
            format=args.format,
            # CLI default: ./asy-output.<ext>. (render() keeps out=None as
            # "no write" for library callers; CLI fills the default here.)
            out=args.out or f"asy-output{EXTENSION[args.format]}",
            api_key=args.api_key,
            base_url=args.base_url,
            dpi=args.dpi,
            timeout=args.timeout,
            filename=args.filename,
            connect_timeout=args.connect_timeout,
        )
    except AsyConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_CONFIG
    except AsyNetworkError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_NETWORK
    except AsyHTTPError as exc:
        # AsyHTTPError already formats a rich multi-line report.
        print(str(exc), file=sys.stderr)
        return EXIT_HTTP
    except AsyOutputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_OUTPUT
    except AsyRenderError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_INTERNAL
    except Exception as exc:  # noqa: BLE001 — last-resort guard for the skill.
        print(
            f"unexpected error: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return EXIT_INTERNAL

    # Stage 3: success — emit bytes/metadata.
    if args.out == "-":
        try:
            sys.stdout.buffer.write(result.data)
            sys.stdout.buffer.flush()
        except BrokenPipeError:
            pass
        except OSError as exc:
            print(f"error: failed writing to stdout: {exc}", file=sys.stderr)
            return EXIT_OUTPUT
        if args.verbose:
            print(
                f"rendered {result.size} bytes ({result.format}/{result.mime}) "
                f"in {result.elapsed:.2f}s -> stdout",
                file=sys.stderr,
            )
        return EXIT_OK

    # File output (render() already wrote it). Report the path on stderr so a
    # calling skill agent can locate the artifact deterministically.
    out_path = _resolve_output_path(
        args.out or f"asy-output{EXTENSION[result.format]}",
        result.format,
        args.filename,
    )
    print(
        f"OK: wrote {out_path} ({result.size} bytes, {result.format}/{result.mime}, "
        f"{result.files} file(s), {result.elapsed:.2f}s)",
        file=sys.stderr,
    )
    if args.verbose:
        if result.filename:
            print(f"  server filename: {result.filename}", file=sys.stderr)
        print(f"  source size:     {len(source)} bytes", file=sys.stderr)
        # Keep stdout clean of binary; verbose is metadata-only on stderr.
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
