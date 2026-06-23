from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def _env_or_none(name: str) -> str | None:
    v = os.environ.get(name)
    return v if v not in (None, "") else None


def _int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


@dataclass
class Settings:
    host: str
    port: int
    max_workers: int
    compile_timeout: int
    max_timeout: int
    fetch_timeout: int
    max_source_bytes: int
    max_fetch_bytes: int
    asy_bin: str
    gs_bin: str
    default_format: str
    default_mode: str
    default_encoding: str
    default_dpi: int
    tmp_dir: str | None

    storage_backend: str
    local_dir: str
    local_base_url: str | None

    s3_endpoint: str | None
    s3_region: str
    s3_bucket: str | None
    s3_prefix: str
    s3_access_key: str | None
    s3_secret_key: str | None
    s3_security_token: str | None
    s3_url_style: str
    s3_public_base_url: str | None
    s3_presign: bool
    s3_presign_expires: int
    s3_use_tls: bool

    @classmethod
    def from_env(cls) -> "Settings":
        host = _env("ASYAGENT_HOST", "0.0.0.0")
        port = _int("ASYAGENT_PORT", 8787)
        default_format = _env("ASYAGENT_DEFAULT_FORMAT", "pdf").lower()
        default_mode = _env("ASYAGENT_DEFAULT_MODE", "inline").lower()
        default_encoding = _env("ASYAGENT_DEFAULT_ENCODING", "binary").lower()

        backend = _env("ASYAGENT_STORAGE", "local").lower()
        s3_endpoint = _env_or_none("S3_ENDPOINT") or _env_or_none("AWS_ENDPOINT_URL")
        s3_region = _env("AWS_REGION", _env("AWS_DEFAULT_REGION", "us-east-1"))
        s3_url_style = _env("S3_URL_STYLE", _env("S3_PATH_STYLE", "path")).lower()
        if s3_url_style not in ("path", "virtual"):
            s3_url_style = "path"

        local_base_url = _env_or_none("ASYAGENT_LOCAL_BASE_URL")
        if local_base_url is None:
            local_base_url = f"http://{host if host != '0.0.0.0' else '127.0.0.1'}:{port}"

        return cls(
            host=host,
            port=port,
            max_workers=_int("ASYAGENT_MAX_WORKERS", 16),
            compile_timeout=_int("ASYAGENT_COMPILE_TIMEOUT", 60),
            max_timeout=_int("ASYAGENT_MAX_TIMEOUT", 300),
            fetch_timeout=_int("ASYAGENT_FETCH_TIMEOUT", 20),
            max_source_bytes=_int("ASYAGENT_MAX_SOURCE_BYTES", 1_048_576),
            max_fetch_bytes=_int("ASYAGENT_MAX_FETCH_BYTES", 5_242_880),
            asy_bin=_env("ASYAGENT_ASY_BIN", "asy"),
            gs_bin=_env("ASYAGENT_GS_BIN", "gs"),
            default_format=default_format,
            default_mode=default_mode,
            default_encoding=default_encoding,
            default_dpi=_int("ASYAGENT_DEFAULT_DPI", 150),
            tmp_dir=_env_or_none("ASYAGENT_TMP_DIR"),
            storage_backend=backend,
            local_dir=_env("ASYAGENT_LOCAL_DIR", "./storage"),
            local_base_url=local_base_url,
            s3_endpoint=s3_endpoint,
            s3_region=s3_region,
            s3_bucket=_env_or_none("S3_BUCKET"),
            s3_prefix=_env("S3_PREFIX", "asyagent/"),
            s3_access_key=_env_or_none("AWS_ACCESS_KEY_ID"),
            s3_secret_key=_env_or_none("AWS_SECRET_ACCESS_KEY"),
            s3_security_token=_env_or_none("AWS_SESSION_TOKEN")
            or _env_or_none("AWS_SECURITY_TOKEN"),
            s3_url_style=s3_url_style,
            s3_public_base_url=_env_or_none("S3_PUBLIC_BASE_URL"),
            s3_presign=_bool("S3_PRESIGN", False),
            s3_presign_expires=_int("S3_PRESIGN_EXPIRES", 3600),
            s3_use_tls=_bool("S3_USE_TLS", True),
        )

    def with_overrides(
        self,
        *,
        storage_prefix: str | None = None,
        storage_bucket: str | None = None,
    ) -> "Settings":
        return Settings(
            host=self.host,
            port=self.port,
            max_workers=self.max_workers,
            compile_timeout=self.compile_timeout,
            max_timeout=self.max_timeout,
            fetch_timeout=self.fetch_timeout,
            max_source_bytes=self.max_source_bytes,
            max_fetch_bytes=self.max_fetch_bytes,
            asy_bin=self.asy_bin,
            gs_bin=self.gs_bin,
            default_format=self.default_format,
            default_mode=self.default_mode,
            default_encoding=self.default_encoding,
            default_dpi=self.default_dpi,
            tmp_dir=self.tmp_dir,
            storage_backend=self.storage_backend,
            local_dir=self.local_dir,
            local_base_url=self.local_base_url,
            s3_endpoint=self.s3_endpoint,
            s3_region=self.s3_region,
            s3_bucket=storage_bucket or self.s3_bucket,
            s3_prefix=storage_prefix or self.s3_prefix,
            s3_access_key=self.s3_access_key,
            s3_secret_key=self.s3_secret_key,
            s3_security_token=self.s3_security_token,
            s3_url_style=self.s3_url_style,
            s3_public_base_url=self.s3_public_base_url,
            s3_presign=self.s3_presign,
            s3_presign_expires=self.s3_presign_expires,
            s3_use_tls=self.s3_use_tls,
        )
