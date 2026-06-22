#!/usr/bin/env python3
"""Example client demonstrating all asyagent request modes."""
import base64
import json
import sys
import urllib.request

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8787"

NO_PROXY_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def post(source, **headers):
    body = source.encode("utf-8") if isinstance(source, str) else source
    req = urllib.request.Request(f"{BASE_URL}/v1/render", data=body, method="POST")
    for k, v in headers.items():
        req.add_header(k, v)
    req.add_header("Content-Type", "text/plain")
    return NO_PROXY_OPENER.open(req)


def save(path, data):
    with open(path, "wb") as f:
        f.write(data)
    print(f"  saved -> {path} ({len(data)} bytes)")


def main():
    src = open("examples/unit_circle.asy").read()

    print("1. Inline binary PDF")
    r = post(src, **{"X-Asy-Format": "pdf"})
    save("output_circle.pdf", r.read())

    print("2. Inline binary PNG (150 dpi)")
    r = post(src, **{"X-Asy-Format": "png", "X-Asy-Dpi": "150"})
    save("output_circle.png", r.read())

    print("3. Inline binary SVG")
    r = post(src, **{"X-Asy-Format": "svg"})
    save("output_circle.svg", r.read())

    print("4. Base64 JSON")
    r = post(src, **{"X-Asy-Encoding": "base64"})
    obj = json.loads(r.read())
    save("output_circle_b64.pdf", base64.b64decode(obj["data"]))

    print("5. URL mode (uploaded to storage, returns URL)")
    r = post(src, **{"X-Asy-Mode": "url"})
    obj = json.loads(r.read())
    print(f"  url: {obj['url']}")
    r2 = urllib.request.Request(obj["url"])
    save("output_circle_url.pdf", NO_PROXY_OPENER.open(r2).read())

    print("\nAll done!")


if __name__ == "__main__":
    main()
