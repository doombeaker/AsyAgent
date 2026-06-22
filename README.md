# asyagent

An HTTP service that compiles [Asymptote](https://asymptote.sourceforge.io/) (`*.asy`) vector-graphics source code into rendered output (PDF, SVG, EPS, PNG, JPG) and returns it either inline (raw binary or base64 JSON) or as an object-storage URL.

AsyAgent is a proxy that wraps a local tool and exposes it as an API with optional object-storage upload for Asymptote: the `asy` compiler doesn't have a server mode, so `asyagent` wraps it in an HTTP API.

## Key characteristics

- **Zero third-party dependencies** — pure Python 3.10+ standard library. No `pip install`, no virtualenv required.
- **Header-driven control plane** — all request behaviour (output format, response mode, encoding, DPI, timeout, storage prefix) is controlled by `X-Asy-*` request headers.
- **Dual response modes** — return compiled output inline (binary or base64 JSON) or upload to storage and return a URL.
- **Multiple storage backends** — local filesystem (zero-config), S3-compatible object storage (hand-rolled AWS Signature V4), or disabled.
- **Multi-format** — native `pdf`/`svg`/`eps`, plus `png`/`jpg` via Ghostscript rasterization. Multi-output (multiple `shipout()` calls) is auto-bundled as a ZIP.

## Quick start

```bash
# Start the server (zero config — uses local storage)
python3 -m asyagent

# Compile an asy source, get PDF inline
curl -s http://127.0.0.1:8787/v1/render \
  --data-binary 'size(5cm); draw(unitcircle);' \
  -H 'Content-Type: text/plain' \
  -o circle.pdf

# Get a PNG instead
curl -s http://127.0.0.1:8787/v1/render \
  --data-binary 'size(5cm); draw(unitcircle);' \
  -H 'Content-Type: text/plain' \
  -H 'X-Asy-Format: png' \
  -o circle.png

# Return base64 JSON
curl -s http://127.0.0.1:8787/v1/render \
  -d '{"source": "size(5cm); draw(unitcircle);"}' \
  -H 'Content-Type: application/json' \
  -H 'X-Asy-Encoding: base64'

# Upload to storage, return URL
curl -s http://127.0.0.1:8787/v1/render \
  -d '{"source": "size(5cm); draw(unitcircle);"}' \
  -H 'Content-Type: application/json' \
  -H 'X-Asy-Mode: url'
```

## API

### `POST /v1/render`

Accepts an Asymptote source and returns the compiled output.

**Request body** (one of):

| Body type | Content-Type | Description |
|-----------|-------------|-------------|
| Raw source text | `text/plain` (or any non-JSON) | The `.asy` source code directly. Auto-detection: if the body is a single line starting with `http://` or `https://`, it's treated as a URL. |
| JSON object | `application/json` | `{"source": "..."}` or `{"url": "https://..."}` |

**Control headers:**

| Header | Values | Default | Description |
|--------|--------|---------|-------------|
| `X-Asy-Format` | `pdf` `svg` `eps` `png` `jpg` `jpeg` | `pdf` (or inferred from `Accept`) | Output format |
| `X-Asy-Mode` | `inline` `url` | `inline` | `inline` = return binary/base64; `url` = upload to storage, return URL |
| `X-Asy-Encoding` | `binary` `base64` | `binary` | Only for inline mode. `binary` returns raw bytes with proper Content-Type; `base64` returns JSON with base64-encoded data |
| `X-Asy-Input` | `auto` `source` `url` | `auto` | How to interpret a non-JSON body |
| `X-Asy-Dpi` | `1`–`4096` | `150` | DPI for raster formats (png/jpg) |
| `X-Asy-Timeout` | seconds | `60` | Compile timeout (capped by `ASYAGENT_MAX_TIMEOUT`) |
| `X-Asy-Filename` | string | — | Suggested filename for Content-Disposition / storage key |
| `X-Asy-Disposition` | `inline` `attachment` | `inline` | Content-Disposition value |
| `X-Asy-Storage-Prefix` | string | env `S3_PREFIX` | Override storage key prefix for this request |
| `X-Asy-Storage-Bucket` | string | env `S3_BUCKET` | Override S3 bucket for this request |
| `Accept` | MIME type | — | Alternative to `X-Asy-Format` (e.g. `Accept: image/png`) |

**Response (inline/binary):** Raw bytes with `Content-Type` matching the format (e.g. `application/pdf`, `image/png`).

**Response (inline/base64):**
```json
{
  "ok": true,
  "mode": "inline",
  "encoding": "base64",
  "format": "pdf",
  "mime": "application/pdf",
  "size": 5989,
  "data": "JVBERi0xLjU..."
}
```

**Response (url mode):**
```json
{
  "ok": true,
  "mode": "url",
  "format": "pdf",
  "mime": "application/pdf",
  "size": 5989,
  "url": "http://host/files/...",
  "key": "files/abc123.pdf",
  "urls": [{"url": "...", "key": "...", "mime": "...", "size": 5989}]
}
```

### `GET /`

Service info (version, formats, storage health, defaults).

### `GET /healthz`

Health check — returns 200 if storage is writable, 503 otherwise.

### `GET /files/{key}`

Serves files from local storage (only available when `ASYAGENT_STORAGE=local`).

## Configuration

All configuration via environment variables:

### Server

| Variable | Default | Description |
|----------|---------|-------------|
| `ASYAGENT_HOST` | `0.0.0.0` | Listen address |
| `ASYAGENT_PORT` | `8787` | Listen port |
| `ASYAGENT_MAX_WORKERS` | `16` | Max concurrent compiles (semaphore) |
| `ASYAGENT_COMPILE_TIMEOUT` | `60` | Default compile timeout (s) |
| `ASYAGENT_MAX_TIMEOUT` | `300` | Max allowed client-requested timeout |
| `ASYAGENT_FETCH_TIMEOUT` | `20` | URL fetch timeout (s) |
| `ASYAGENT_MAX_SOURCE_BYTES` | `1048576` | Max request body size |
| `ASYAGENT_MAX_FETCH_BYTES` | `5242880` | Max remote file size for URL input |
| `ASYAGENT_ASY_BIN` | `asy` | Path to asy binary |
| `ASYAGENT_GS_BIN` | `gs` | Path to ghostscript binary |
| `ASYAGENT_DEFAULT_FORMAT` | `pdf` | Default output format |
| `ASYAGENT_DEFAULT_MODE` | `inline` | Default response mode |
| `ASYAGENT_DEFAULT_ENCODING` | `binary` | Default inline encoding |
| `ASYAGENT_DEFAULT_DPI` | `150` | Default raster DPI |
| `ASYAGENT_TMP_DIR` | — | Override temp directory for compile working dirs |
| `ASYAGENT_INSTALL_SKILLUTILS` | `true` | Auto-install `skillutils.asy` to `~/.asy/` |

### Storage

| Variable | Default | Description |
|----------|---------|-------------|
| `ASYAGENT_STORAGE` | `local` | Backend: `local`, `s3`, or `none` |
| `ASYAGENT_LOCAL_DIR` | `./storage` | Local storage directory |
| `ASYAGENT_LOCAL_BASE_URL` | auto | Base URL for local file serving |

### S3 / Object Storage

| Variable | Default | Description |
|----------|---------|-------------|
| `S3_BUCKET` | — | Bucket name (required for S3) |
| `S3_PREFIX` | `asyagent/` | Key prefix |
| `S3_ENDPOINT` | auto | Custom endpoint (e.g. `http://minio:9000`) |
| `S3_URL_STYLE` | `path` | `path` or `virtual` (virtual-hosted) |
| `S3_PUBLIC_BASE_URL` | — | Override the public URL base (e.g. CDN domain) |
| `S3_PRESIGN` | `false` | Return presigned URLs instead of public URLs |
| `S3_PRESIGN_EXPIRES` | `3600` | Presigned URL expiry (s) |
| `S3_USE_TLS` | `true` | Use HTTPS for S3 API calls |
| `AWS_ACCESS_KEY_ID` | — | Access key |
| `AWS_SECRET_ACCESS_KEY` | — | Secret key |
| `AWS_SESSION_TOKEN` | — | STS session token (optional) |
| `AWS_REGION` | `us-east-1` | Region |

## Architecture

```
asyagent/
  __init__.py          # package metadata
  __main__.py          # python -m asyagent entry point
  config.py            # Settings dataclass, env-driven
  errors.py            # typed exception hierarchy
  sigv4.py             # AWS Signature V4 (sign + presign), zero-dep
  fetcher.py           # URL -> source text fetcher
  compiler.py          # asy invocation + gs rasterization + ZIP bundling
  storage.py           # Local / S3 / None storage backends
  server.py            # ThreadingHTTPServer, header-driven rendering
  assets/
    skillutils.asy     # bundled CJK/utility library, auto-installed to ~/.asy/
tests/
  test_sigv4.py        # KAT against AWS test vector (AKIDEXAMPLE)
  test_compiler.py     # all formats, multi-shipout, errors
  test_server.py       # end-to-end integration tests
examples/
  unit_circle.asy      # example source
  function_plot.asy    # example source
  multi_page.asy       # multi-shipout example
  client.py            # example client script
```

### Request flow

```
Client ──POST /v1/render──▶ server.py
  │                           │
  │  Headers: X-Asy-Format,   │  RenderContext (parses all X-Asy-* headers)
  │  X-Asy-Mode, etc.         │
  │                           ├── text/plain body ──▶ _resolve_source (auto-detect url/source)
  │                           ├── application/json ──▶ _resolve_source (json.source or json.url)
  │                           │                          └── fetcher.py (if url)
  │                           │
  │                           ├── compile_source (semaphore-gated)
  │                           │   ├── asy -f pdf -o out input.asy    (native: pdf/svg/eps)
  │                           │   ├── gs -sDEVICE=pngalpha ...        (raster: png/jpg)
  │                           │   └── select_or_bundle (ZIP if multiple outputs)
  │                           │
  │                           ├── mode=inline,encoding=binary ──▶ raw bytes + Content-Type
  │                           ├── mode=inline,encoding=base64 ──▶ JSON {data: base64...}
  │                           └── mode=url ──▶ storage.upload ──▶ JSON {url: ...}
  │
◀── response (binary / JSON) ─┘
```

### Response mode comparison

| Mode | Encoding | Response body | Content-Type | Use case |
|------|----------|---------------|-------------|----------|
| `inline` | `binary` | Raw compiled bytes | matches format | Direct download, browser display |
| `inline` | `base64` | JSON `{data: "..."}` | `application/json` | API compositing, embedding in JSON workflows |
| `url` | — | JSON `{url: "..."}` | `application/json` | Large files, CDN delivery, async workflows |

## Running tests

```bash
python3 -m unittest discover -s tests -v
```

## Docker

```bash
docker build -t asyagent .
docker run -p 8787:8787 asyagent
```

## License

MIT
