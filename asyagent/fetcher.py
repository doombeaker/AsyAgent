from __future__ import annotations

import urllib.request
import urllib.error

from .errors import FetchError


def fetch_source(url: str, *, timeout: int, max_bytes: int) -> str:
    scheme = url.split("://", 1)[0].lower() if "://" in url else ""
    if scheme not in ("http", "https"):
        raise FetchError(f"unsupported URL scheme: {scheme!r}")

    req = urllib.request.Request(url, headers={"User-Agent": "asyagent/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            declared = resp.headers.get("Content-Length")
            if declared and declared.isdigit() and int(declared) > max_bytes:
                raise FetchError(
                    f"remote file too large ({int(declared)} > {max_bytes} bytes)",
                    detail=url,
                )
            data = resp.read(max_bytes + 1)
            if len(data) > max_bytes:
                raise FetchError(
                    f"remote file too large (> {max_bytes} bytes)", detail=url
                )
    except urllib.error.HTTPError as e:
        raise FetchError(f"remote returned HTTP {e.code}", detail=str(e.reason)) from e
    except urllib.error.URLError as e:
        raise FetchError(f"failed to fetch URL: {e.reason}", detail=url) from e
    except TimeoutError as e:
        raise FetchError(f"fetch timed out after {timeout}s", detail=url) from e

    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = data.decode("latin-1")
        except Exception as e:
            raise FetchError("remote file is not valid text", detail=url) from e

    if content_type and content_type not in (
        "",
        "text/plain",
        "text/x-asy",
        "text/y-asy",
        "application/octet-stream",
        "text/markdown",
    ) and not content_type.startswith("text/"):
        raise FetchError(
            f"unexpected remote content-type: {content_type}", detail=url
        )

    return text
