from __future__ import annotations

import json
import os
import shutil
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import __version__
from .compiler import MIME_BY_EXT, SUPPORTED_FORMATS, compile_source, select_or_bundle
from .config import Settings
from .errors import (
    AsyAgentError,
    BadRequest,
    EmptyInput,
    InvalidInput,
    ServerBusy,
    UnsupportedFormat,
)
from .fetcher import fetch_source
from .storage import LocalStorage, StorageBackend, make_storage


def ensure_skillutils(settings: Settings) -> None:
    if not settings.install_skillutils:
        return
    home = os.environ.get("HOME") or os.path.expanduser("~")
    asy_dir = os.path.join(home, ".asy")
    os.makedirs(asy_dir, exist_ok=True)
    dest = os.path.join(asy_dir, "skillutils.asy")
    if os.path.exists(dest):
        return
    src = os.path.join(os.path.dirname(__file__), "assets", "skillutils.asy")
    if os.path.exists(src):
        try:
            shutil.copyfile(src, dest)
        except OSError:
            pass


class RenderContext:
    __slots__ = (
        "fmt", "mode", "encoding", "input_mode", "dpi",
        "timeout", "storage_prefix", "storage_bucket",
        "filename", "disposition", "content_type",
    )

    def __init__(self, settings: Settings, headers) -> None:
        def h(name: str) -> str:
            v = headers.get(name)
            return v.strip() if v else ""

        self.content_type = (headers.get("Content-Type") or "").lower()

        self.fmt = (h("X-Asy-Format") or _format_from_accept(headers) or settings.default_format).lower()
        mode = (h("X-Asy-Mode") or settings.default_mode).lower()
        if mode not in ("inline", "url"):
            mode = settings.default_mode
        self.mode = mode
        enc = (h("X-Asy-Encoding") or settings.default_encoding).lower()
        if enc not in ("binary", "base64"):
            enc = "binary"
        self.encoding = enc
        inm = (h("X-Asy-Input") or "auto").lower()
        if inm not in ("source", "url", "auto"):
            inm = "auto"
        self.input_mode = inm
        dpi = settings.default_dpi
        dh = h("X-Asy-Dpi")
        if dh:
            try:
                dpi = max(1, min(4096, int(dh)))
            except ValueError:
                pass
        self.dpi = dpi
        timeout = settings.compile_timeout
        th = h("X-Asy-Timeout")
        if th:
            try:
                timeout = max(1, min(settings.max_timeout, int(th)))
            except ValueError:
                pass
        self.timeout = timeout
        self.storage_prefix = h("X-Asy-Storage-Prefix") or None
        self.storage_bucket = h("X-Asy-Storage-Bucket") or None
        self.filename = h("X-Asy-Filename") or None
        disp = h("X-Asy-Disposition").lower()
        if disp not in ("inline", "attachment"):
            disp = "inline"
        self.disposition = disp


def _format_from_accept(headers) -> str:
    accept = headers.get("Accept") or ""
    accept = accept.lower()
    mapping = {
        "application/pdf": "pdf",
        "image/svg+xml": "svg",
        "image/svg": "svg",
        "application/postscript": "eps",
        "image/png": "png",
        "image/jpeg": "jpg",
    }
    for mime, fmt in mapping.items():
        if mime in accept:
            return fmt
    return ""


class App:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        ensure_skillutils(settings)
        self.storage: StorageBackend = make_storage(settings)
        self.sem = threading.BoundedSemaphore(max(1, settings.max_workers))

    def render(self, ctx: RenderContext, body: bytes) -> tuple[int, bytes, str, dict]:
        source = self._resolve_source(ctx, body)

        if ctx.storage_bucket or ctx.storage_prefix:
            overridden = self.settings.with_overrides(
                storage_prefix=ctx.storage_prefix,
                storage_bucket=ctx.storage_bucket,
            )
            storage = make_storage(overridden)
        else:
            storage = self.storage

        if ctx.fmt not in SUPPORTED_FORMATS:
            raise UnsupportedFormat(
                f"unsupported format: {ctx.fmt!r}",
                detail=f"supported: {', '.join(SUPPORTED_FORMATS)}",
            )

        acquired = self.sem.acquire(timeout=5)
        if not acquired:
            raise ServerBusy("server is busy, try again later")
        try:
            files = compile_source(
                source,
                fmt=ctx.fmt,
                dpi=ctx.dpi,
                timeout=ctx.timeout,
                asy_bin=self.settings.asy_bin,
                gs_bin=self.settings.gs_bin,
                tmp_dir=self.settings.tmp_dir,
            )
        finally:
            self.sem.release()

        result = select_or_bundle(files)

        if ctx.mode == "url":
            url, key = storage.upload(
                result, key_prefix=ctx.storage_prefix or "", filename_hint=ctx.filename
            )
            payload = {
                "ok": True,
                "mode": "url",
                "format": result.ext,
                "mime": result.mime,
                "count": 1,
                "url": url,
                "key": key,
                "size": result.size,
                "urls": [{"url": url, "key": key, "mime": result.mime, "size": result.size}],
            }
            headers = {
                "Content-Type": "application/json",
                "X-Asy-Result-Url": url,
                "X-Asy-Format": result.ext,
            }
            return 200, json.dumps(payload).encode("utf-8"), "application/json", headers

        if ctx.encoding == "base64":
            import base64

            payload = {
                "ok": True,
                "mode": "inline",
                "encoding": "base64",
                "format": result.ext,
                "mime": result.mime,
                "count": 1,
                "size": result.size,
                "data": base64.b64encode(result.data).decode("ascii"),
            }
            headers = {
                "Content-Type": "application/json",
                "X-Asy-Format": result.ext,
            }
            return 200, json.dumps(payload).encode("utf-8"), "application/json", headers

        filename = ctx.filename or f"asyagent-output.{result.ext}"
        disposition = f'{ctx.disposition}; filename="{urllib.parse.quote(filename)}"'
        headers = {
            "Content-Type": result.mime,
            "Content-Length": str(len(result.data)),
            "Content-Disposition": disposition,
            "X-Asy-Format": result.ext,
            "X-Asy-Files": "1",
            "Cache-Control": "no-store",
        }
        return 200, result.data, result.mime, headers

    def _resolve_source(self, ctx: RenderContext, body: bytes) -> str:
        content_type = ctx.content_type
        text = body.decode("utf-8", "replace")

        url_value: str | None = None
        source_value: str | None = None

        if "application/json" in content_type:
            try:
                obj = json.loads(text) if text.strip() else {}
            except json.JSONDecodeError as e:
                raise InvalidInput("invalid JSON body", detail=str(e))
            if not isinstance(obj, dict):
                raise InvalidInput("JSON body must be an object")
            url_value = obj.get("url")
            source_value = obj.get("source")
            if url_value is None and source_value is None:
                raise InvalidInput('JSON body must contain "source" or "url"')
        else:
            mode = ctx.input_mode
            if mode == "auto":
                stripped = text.strip()
                first_line = stripped.splitlines()[0] if stripped else ""
                if first_line.startswith(("http://", "https://")) and " " not in first_line:
                    mode = "url"
                else:
                    mode = "source"
            if mode == "url":
                url_value = text.strip().splitlines()[0] if text.strip() else ""
            else:
                source_value = text

        if url_value is not None:
            if not url_value:
                raise EmptyInput("empty URL")
            return fetch_source(url_value, timeout=self.settings.fetch_timeout, max_bytes=self.settings.max_fetch_bytes)

        if source_value is None:
            source_value = ""
        if not source_value.strip():
            raise EmptyInput("empty Asymptote source")
        return source_value


class Handler(BaseHTTPRequestHandler):
    server_version = f"asyagent/{__version__}"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        return

    @property
    def app(self) -> App:
        return self.server.app  # type: ignore[attr-defined]

    def _send(self, status: int, body: bytes, content_type: str, headers: dict | None = None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if headers:
            for k, v in headers.items():
                self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _send_json(self, status: int, obj, extra: dict | None = None):
        body = json.dumps(obj).encode("utf-8")
        self._send(status, body, "application/json", extra)

    def _send_error(self, err: AsyAgentError):
        self._send_json(err.status, err.to_dict())

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path == "/" or path == "":
            info = {
                "service": "asyagent",
                "version": __version__,
                "description": "Compile Asymptote (*.asy) sources to vector/raster graphics over HTTP.",
                "formats": list(SUPPORTED_FORMATS),
                "storage": self.app.storage.health(),
                "defaults": {
                    "format": self.app.settings.default_format,
                    "mode": self.app.settings.default_mode,
                    "encoding": self.app.settings.default_encoding,
                    "dpi": self.app.settings.default_dpi,
                },
                "endpoints": {
                    "render": "POST /v1/render",
                    "health": "GET /healthz",
                },
            }
            return self._send_json(200, info)
        if path == "/healthz":
            health = self.app.storage.health()
            ok = bool(health.get("ok"))
            return self._send_json(200 if ok else 503, {"status": "ok" if ok else "degraded", **health})
        if path.startswith("/files/"):
            return self._serve_file(path[len("/files/"):])
        return self._send_error(BadRequest("not found", detail=path))

    def do_HEAD(self):
        self.do_GET()

    def _serve_file(self, rel: str):
        if not isinstance(self.app.storage, LocalStorage):
            return self._send_error(BadRequest("file serving requires ASYAGENT_STORAGE=local"))
        rel = urllib.parse.unquote(rel)
        base = self.app.storage.local_dir
        safe = os.path.normpath(os.path.join(base, rel))
        if not (safe == base or safe.startswith(base + os.sep)):
            return self._send_error(BadRequest("invalid path"))
        if not os.path.isfile(safe):
            return self._send_error(BadRequest("file not found", detail=rel))
        ext = os.path.splitext(rel)[1].lower().lstrip(".")
        mime = MIME_BY_EXT.get(ext, "application/octet-stream")
        with open(safe, "rb") as f:
            data = f.read()
        self._send(200, data, mime, {"Cache-Control": "public, max-age=86400", "Content-Disposition": f'inline; filename="{os.path.basename(rel)}"'})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path not in ("/v1/render", "/render"):
            return self._send_error(BadRequest("not found", detail=path))

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self._send_error(BadRequest("invalid Content-Length"))
        if length < 0:
            return self._send_error(BadRequest("negative Content-Length"))
        if length > self.app.settings.max_source_bytes + 1024:
            return self._send_error(
                BadRequest(
                    f"request body too large ({length} > {self.app.settings.max_source_bytes + 1024} bytes)",
                )
            )
        body = self.rfile.read(length) if length > 0 else b""

        ctx = RenderContext(self.app.settings, self.headers)
        try:
            status, data, mime, headers = self.app.render(ctx, body)
            self._send(status, data, mime, headers)
        except AsyAgentError as e:
            self._send_error(e)
        except Exception as e:  # noqa: BLE001
            err = AsyAgentError("internal error", detail=repr(e))
            self._send_error(err)


def build_server(settings: Settings) -> ThreadingHTTPServer:
    app = App(settings)
    server = ThreadingHTTPServer((settings.host, settings.port), Handler)
    server.app = app  # type: ignore[attr-defined]
    server.daemon_threads = True
    return server


def run(settings: Settings) -> None:
    server = build_server(settings)
    print(f"asyagent {__version__} listening on http://{settings.host}:{settings.port}")
    print(f"  storage backend: {app_name(server.app)}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down...")
    finally:
        server.server_close()


def app_name(app: App) -> str:
    return app.storage.name
