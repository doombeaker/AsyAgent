from __future__ import annotations

import hashlib
import hmac
import urllib.parse
from datetime import datetime, timezone
from typing import Mapping

ALGORITHM = "AWS4-HMAC-SHA256"
EMPTY_PAYLOAD_HASH = hashlib.sha256(b"").hexdigest()
UNSIGNED_PAYLOAD = "UNSIGNED-PAYLOAD"


def uri_encode(value: str, keep_slash: bool = False) -> str:
    safe = "/" if keep_slash else ""
    return urllib.parse.quote(value, safe=safe, encoding="utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hmac_sha256(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def derive_signing_key(secret_key: str, date_stamp: str, region: str, service: str) -> bytes:
    k_date = hmac_sha256(("AWS4" + secret_key).encode("utf-8"), date_stamp)
    k_region = hmac_sha256(k_date, region)
    k_service = hmac_sha256(k_region, service)
    return hmac_sha256(k_service, "aws4_request")


def _normalize_host_header(host: str, port: int | None, use_tls: bool) -> str:
    if port is None:
        return host
    default_port = 443 if use_tls else 80
    if port == default_port:
        return host
    return f"{host}:{port}"


def canonical_query_string(params: Mapping[str, str]) -> str:
    items = []
    for k, v in params.items():
        items.append((uri_encode(k), uri_encode(v)))
    items.sort()
    return "&".join(f"{k}={v}" for k, v in items)


def _canonical_request(
    method: str,
    canonical_uri: str,
    canonical_query: str,
    canonical_headers: str,
    signed_headers: str,
    payload_hash: str,
) -> str:
    return (
        method
        + "\n"
        + canonical_uri
        + "\n"
        + canonical_query
        + "\n"
        + canonical_headers
        + "\n"
        + signed_headers
        + "\n"
        + payload_hash
    )


def _string_to_sign(
    amz_date: str, scope: str, canonical_request: str
) -> str:
    return (
        ALGORITHM
        + "\n"
        + amz_date
        + "\n"
        + scope
        + "\n"
        + sha256_hex(canonical_request.encode("utf-8"))
    )


def sign_request(
    *,
    method: str,
    host: str,
    port: int | None,
    path: str,
    query: Mapping[str, str] | None,
    extra_headers: Mapping[str, str] | None,
    body: bytes,
    access_key: str,
    secret_key: str,
    security_token: str | None,
    region: str,
    service: str,
    use_tls: bool = True,
    date: datetime | None = None,
) -> tuple[dict, str, str, str]:
    """Sign an HTTP request with AWS Signature V4.

    Returns (final_headers, signature, string_to_sign, canonical_request).
    The final_headers include Authorization, x-amz-date and x-amz-content-sha256
    plus host and any provided extra headers.
    """
    date = date or datetime.now(timezone.utc)
    amz_date = date.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = date.strftime("%Y%m%d")
    scope = f"{date_stamp}/{region}/{service}/aws4_request"

    host_value = _normalize_host_header(host, port, use_tls)
    payload_hash = sha256_hex(body)

    headers: dict[str, str] = {
        "host": host_value,
        "x-amz-content-sha256": payload_hash,
        "x-amz-date": amz_date,
    }
    if security_token:
        headers["x-amz-security-token"] = security_token

    for k, v in (extra_headers or {}).items():
        lk = k.lower()
        if lk in ("host", "x-amz-date", "x-amz-content-sha256"):
            continue
        if lk.startswith("x-amz-"):
            headers[lk] = " ".join(v.split())
        elif lk == "content-type":
            headers[lk] = " ".join(v.split())

    items = sorted(headers.items())
    canonical_headers = "".join(f"{k}:{v}\n" for k, v in items)
    signed_headers = ";".join(k for k, _ in items)

    canonical_uri = uri_encode(path, keep_slash=True) or "/"
    canonical_query = canonical_query_string(query or {})

    canonical_req = _canonical_request(
        method,
        canonical_uri,
        canonical_query,
        canonical_headers,
        signed_headers,
        payload_hash,
    )
    sts = _string_to_sign(amz_date, scope, canonical_req)

    signing_key = derive_signing_key(secret_key, date_stamp, region, service)
    signature = hmac.new(signing_key, sts.encode("utf-8"), hashlib.sha256).hexdigest()

    authorization = (
        f"{ALGORITHM} Credential={access_key}/{scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    final_headers = dict(headers)
    final_headers["authorization"] = authorization
    return final_headers, signature, sts, canonical_req


def presign_url(
    *,
    method: str,
    host: str,
    port: int | None,
    path: str,
    query: Mapping[str, str] | None,
    headers_to_sign: Mapping[str, str] | None,
    access_key: str,
    secret_key: str,
    security_token: str | None,
    region: str,
    service: str,
    expires: int,
    use_tls: bool = True,
    date: datetime | None = None,
) -> str:
    """Produce a presigned URL (method GET/HEAD) with UNSIGNED-PAYLOAD."""
    date = date or datetime.now(timezone.utc)
    amz_date = date.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = date.strftime("%Y%m%d")
    scope = f"{date_stamp}/{region}/{service}/aws4_request"
    host_value = _normalize_host_header(host, port, use_tls)

    signed: dict[str, str] = {"host": host_value}
    if security_token:
        signed["x-amz-security-token"] = security_token
    for k, v in (headers_to_sign or {}).items():
        lk = k.lower()
        if lk in ("host", "x-amz-date", "x-amz-content-sha256"):
            continue
        if lk.startswith("x-amz-"):
            signed[lk] = " ".join(v.split())
    signed_headers = ";".join(k for k, _ in sorted(signed.items()))
    canonical_headers = "".join(f"{k}:{v}\n" for k, v in sorted(signed.items()))

    params: dict[str, str] = dict(query or {})
    params["X-Amz-Algorithm"] = ALGORITHM
    params["X-Amz-Credential"] = f"{access_key}/{scope}"
    params["X-Amz-Date"] = amz_date
    params["X-Amz-Expires"] = str(expires)
    params["X-Amz-SignedHeaders"] = signed_headers
    if security_token:
        params["X-Amz-Security-Token"] = security_token

    canonical_uri = uri_encode(path, keep_slash=True) or "/"
    canonical_query = canonical_query_string(params)

    canonical_req = _canonical_request(
        method,
        canonical_uri,
        canonical_query,
        canonical_headers,
        signed_headers,
        UNSIGNED_PAYLOAD,
    )
    sts = _string_to_sign(amz_date, scope, canonical_req)
    signing_key = derive_signing_key(secret_key, date_stamp, region, service)
    signature = hmac.new(signing_key, sts.encode("utf-8"), hashlib.sha256).hexdigest()

    params["X-Amz-Signature"] = signature
    scheme = "https" if use_tls else "http"
    netloc = host_value
    return f"{scheme}://{netloc}{canonical_uri}?{canonical_query_string(params)}"
