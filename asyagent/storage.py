from __future__ import annotations

import os
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone

from . import sigv4
from .compiler import CompiledFile
from .config import Settings
from .errors import MissingStorage, StorageError


def _unique_key(prefix: str, ext: str, filename_hint: str | None) -> str:
    prefix = prefix or ""
    if not prefix.endswith("/") and prefix != "":
        prefix += "/"
    if filename_hint:
        hint = os.path.basename(filename_hint.strip())
        if hint and "." in hint:
            base, _ = os.path.splitext(hint)
            name = f"{base}.{ext.lstrip('.')}"
        else:
            name = f"{uuid.uuid4().hex}.{ext.lstrip('.')}"
    else:
        name = f"{uuid.uuid4().hex}.{ext.lstrip('.')}"
    return prefix + name


class StorageBackend:
    name = "base"

    def upload(
        self, file: CompiledFile, *, key_prefix: str, filename_hint: str | None
    ) -> tuple[str, str]:
        raise NotImplementedError

    def presign(
        self, key: str, *, mime: str, expires: int
    ) -> str | None:
        return None

    def health(self) -> dict:
        return {"backend": self.name, "ok": True}


class NoStorage(StorageBackend):
    name = "none"

    def upload(
        self, file: CompiledFile, *, key_prefix: str, filename_hint: str | None
    ) -> tuple[str, str]:
        raise MissingStorage(
            "object storage is disabled (ASYAGENT_STORAGE=none); cannot return a URL"
        )

    def health(self) -> dict:
        return {"backend": self.name, "ok": False, "reason": "disabled"}


class LocalStorage(StorageBackend):
    name = "local"

    def __init__(self, settings: Settings) -> None:
        self.local_dir = os.path.abspath(settings.local_dir)
        self.base_url = settings.local_base_url or "http://127.0.0.1:8787"
        os.makedirs(self.local_dir, exist_ok=True)

    def _path_for(self, key: str) -> str:
        safe = os.path.normpath(os.path.join(self.local_dir, key))
        if not safe.startswith(self.local_dir + os.sep) and safe != self.local_dir:
            raise StorageError("invalid storage key", detail=key)
        return safe

    def upload(
        self, file: CompiledFile, *, key_prefix: str, filename_hint: str | None
    ) -> tuple[str, str]:
        ext = file.ext
        if file.ext == "zip":
            ext = "zip"
        key = _unique_key((key_prefix or "files/"), file.ext, filename_hint)
        if not key.startswith("files/") and not (key_prefix or "").startswith("/"):
            pass
        dest = self._path_for(key)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(file.data)
        url = f"{self.base_url.rstrip('/')}/files/{urllib.parse.quote(key, safe='/')}"
        return url, key

    def health(self) -> dict:
        return {
            "backend": self.name,
            "ok": os.path.isdir(self.local_dir) and os.access(self.local_dir, os.W_OK),
            "dir": self.local_dir,
        }


class S3Storage(StorageBackend):
    name = "s3"

    def __init__(self, settings: Settings) -> None:
        if not settings.s3_bucket:
            raise MissingStorage("S3 backend requires S3_BUCKET")
        if not settings.s3_access_key or not settings.s3_secret_key:
            raise MissingStorage("S3 backend requires AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        self.settings = settings
        self.bucket = settings.s3_bucket
        host, port, use_tls = self._parse_endpoint(settings)
        self.host = host
        self.port = port
        self.use_tls = use_tls

    @staticmethod
    def _parse_endpoint(settings: Settings) -> tuple[str, int | None, bool]:
        endpoint = settings.s3_endpoint
        use_tls = settings.s3_use_tls
        if endpoint:
            ep = endpoint.strip()
            if "://" in ep:
                scheme, rest = ep.split("://", 1)
                use_tls = scheme.lower() == "https"
            else:
                rest = ep
            host, _, port_s = rest.partition(":")
            host = host.strip().rstrip("/")
            port = int(port_s) if port_s.strip().isdigit() else None
            return host, port, use_tls
        if settings.s3_region == "us-east-1":
            return "s3.amazonaws.com", None, True
        return f"s3.{settings.s3_region}.amazonaws.com", None, True

    def _netloc(self) -> str:
        if self.port is None:
            return self.host
        default = 443 if self.use_tls else 80
        return self.host if self.port == default else f"{self.host}:{self.port}"

    def _request_path(self, key: str) -> str:
        if self.settings.s3_url_style == "virtual":
            return "/" + urllib.parse.quote(key, safe="/")
        return f"/{self.bucket}/" + urllib.parse.quote(key, safe="/")

    def _public_url(self, key: str) -> str:
        base = self.settings.s3_public_base_url
        if base:
            return f"{base.rstrip('/')}/{key}"
        scheme = "https" if self.use_tls else "http"
        if self.settings.s3_url_style == "virtual":
            netloc = self._netloc()
            virtual_host = f"{self.bucket}.{netloc}"
            return f"{scheme}://{virtual_host}/{key}"
        return f"{scheme}://{self._netloc()}/{self.bucket}/{key}"

    def upload(
        self, file: CompiledFile, *, key_prefix: str, filename_hint: str | None
    ) -> tuple[str, str]:
        s = self.settings
        key = _unique_key(s.s3_prefix, file.ext, filename_hint)
        path = self._request_path(key)
        url = ("https" if self.use_tls else "http") + "://" + self._netloc() + path

        headers, _, _, _ = sigv4.sign_request(
            method="PUT",
            host=self.host,
            port=self.port,
            path=path,
            query={},
            extra_headers={"content-type": file.mime},
            body=file.data,
            access_key=s.s3_access_key,
            secret_key=s.s3_secret_key,
            security_token=s.s3_security_token,
            region=s.s3_region,
            service="s3",
            use_tls=self.use_tls,
        )
        req_headers = {
            "Authorization": headers["authorization"],
            "x-amz-date": headers["x-amz-date"],
            "x-amz-content-sha256": headers["x-amz-content-sha256"],
            "Content-Type": file.mime,
            "Content-Length": str(len(file.data)),
        }
        if s.s3_security_token:
            req_headers["x-amz-security-token"] = s.s3_security_token

        req = urllib.request.Request(url, data=file.data, method="PUT", headers=req_headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                if resp.status >= 300:
                    body = resp.read().decode("utf-8", "replace")
                    raise StorageError(f"S3 PUT failed: HTTP {resp.status}", detail=body)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:2000]
            raise StorageError(f"S3 PUT failed: HTTP {e.code}", detail=body) from e
        except urllib.error.URLError as e:
            raise StorageError(f"S3 PUT network error: {e.reason}", detail=str(e)) from e

        if s.s3_presign:
            url = self.presign(key, mime=file.mime, expires=s.s3_presign_expires) or url
        else:
            url = self._public_url(key)
        return url, key

    def presign(self, key: str, *, mime: str, expires: int) -> str | None:
        s = self.settings
        path = self._request_path(key)
        return sigv4.presign_url(
            method="GET",
            host=self.host,
            port=self.port,
            path=path,
            query={},
            headers_to_sign={},
            access_key=s.s3_access_key,
            secret_key=s.s3_secret_key,
            security_token=s.s3_security_token,
            region=s.s3_region,
            service="s3",
            expires=expires,
            use_tls=self.use_tls,
            date=datetime.now(timezone.utc),
        )

    def health(self) -> dict:
        return {
            "backend": self.name,
            "ok": True,
            "bucket": self.bucket,
            "endpoint": self.s3_endpoint_display(),
            "region": self.settings.s3_region,
            "url_style": self.settings.s3_url_style,
            "presign": self.settings.s3_presign,
        }

    def s3_endpoint_display(self) -> str:
        scheme = "https" if self.use_tls else "http"
        return f"{scheme}://{self._netloc()}"


def make_storage(settings: Settings) -> StorageBackend:
    backend = settings.storage_backend
    if backend in ("none", "off", "disabled"):
        return NoStorage()
    if backend in ("local", "file", "fs"):
        return LocalStorage(settings)
    if backend in ("s3", "object"):
        return S3Storage(settings)
    raise MissingStorage(f"unknown storage backend: {backend!r}")
