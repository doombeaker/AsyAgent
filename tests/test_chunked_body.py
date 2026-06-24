import json
import os
import socket
import tempfile
import threading
import time
import unittest
import urllib.request

from asyagent.config import Settings
from asyagent.server import build_server


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class ChunkedFixture:
    def __init__(self):
        self.tmpdir = tempfile.mkdtemp(prefix="asyagent_chunked_")
        self.port = _free_port()
        env_overrides = {
            "ASYAGENT_HOST": "127.0.0.1",
            "ASYAGENT_PORT": str(self.port),
            "ASYAGENT_LOCAL_DIR": os.path.join(self.tmpdir, "storage"),
            "ASYAGENT_LOCAL_BASE_URL": f"http://127.0.0.1:{self.port}",
            "ASYAGENT_STORAGE": "local",
            "ASYAGENT_DEFAULT_FORMAT": "pdf",
            "ASYAGENT_DEFAULT_MODE": "inline",
            "ASYAGENT_DEFAULT_ENCODING": "binary",
            "ASYAGENT_COMPILE_TIMEOUT": "60",
        }
        old_env = dict(os.environ)
        os.environ.update(env_overrides)
        try:
            self.settings = Settings.from_env()
        finally:
            os.environ.clear()
            os.environ.update(old_env)
        self.server = build_server(self.settings)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        time.sleep(0.4)

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"


def _send_chunked(host: str, port: int, path: str, headers: dict, body: bytes) -> tuple[int, bytes, dict]:
    """Send a request with Transfer-Encoding: chunked over a raw socket.
    Reuses the connection so we can verify keep-alive safety too."""
    sock = socket.create_connection((host, port))
    try:
        # Build chunked body: <hex-size>\r\n<data>\r\n0\r\n\r\n
        chunked = f"{len(body):x}\r\n".encode() + body + b"\r\n0\r\n\r\n"
        req_lines = [f"POST {path} HTTP/1.1", f"Host: {host}:{port}"]
        for k, v in headers.items():
            req_lines.append(f"{k}: {v}")
        req_lines.append("Transfer-Encoding: chunked")
        req_lines.append("Connection: keep-alive")
        raw = "\r\n".join(req_lines).encode() + b"\r\n\r\n" + chunked
        sock.sendall(raw)

        # Read the full response (headers + body), using Content-Length.
        resp = b""
        sock.settimeout(5)
        while True:
            try:
                buf = sock.recv(8192)
            except socket.timeout:
                break
            if not buf:
                break
            resp += buf
            if b"\r\n\r\n" in resp:
                head, _, rest = resp.partition(b"\r\n\r\n")
                cl = 0
                for line in head.split(b"\r\n"):
                    if line.lower().startswith(b"content-length:"):
                        cl = int(line.split(b":", 1)[1].strip())
                        break
                if len(rest) >= cl:
                    break
        head, _, rest = resp.partition(b"\r\n\r\n")
        status = int(head.split(b"\r\n", 1)[0].split(b" ")[1])
        hdrs = {}
        for line in head.split(b"\r\n")[1:]:
            if b":" in line:
                k, v = line.split(b":", 1)
                hdrs[k.strip().lower().decode()] = v.strip().decode()
        return status, rest, hdrs
    finally:
        sock.close()


class TestChunkedBody(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = ChunkedFixture()

    @classmethod
    def tearDownClass(cls):
        cls.fixture.stop()

    def test_chunked_json_body_is_read(self):
        """The core regression: chunked body must be received, not empty."""
        payload = json.dumps({"source": "size(3cm); draw(unitcircle);"}).encode()
        status, body, _ = _send_chunked(
            "127.0.0.1", self.fixture.port, "/v1/render",
            {"Content-Type": "application/json", "X-Asy-Format": "png"},
            payload,
        )
        # We expect 200 (if asy works) or a compile error (422). The one
        # thing we must NOT get is 400 invalid_input "JSON body must contain
        # source or url" — that would mean the body was empty.
        self.assertNotEqual(status, 400, "chunked body was not read (got 400)")
        obj = json.loads(body) if status != 200 else None
        if status == 200:
            self.assertEqual(obj["error"]["code"] if "error" in obj else obj.get("format"), "png")

    def test_chunked_preserves_keep_alive(self):
        """After a chunked request, the format header must be honored —
        proving the connection wasn't poisoned by leftover bytes."""
        payload = json.dumps({"source": "size(3cm); draw(unitcircle);"}).encode()
        status, body, hdrs = _send_chunked(
            "127.0.0.1", self.fixture.port, "/v1/render",
            {"Content-Type": "application/json", "X-Asy-Format": "svg"},
            payload,
        )
        self.assertNotEqual(status, 400, "chunked body was not read (got 400)")
        # If compile succeeded, the response must be SVG (proving X-Asy-Format
        # was read, not the default pdf).
        if status == 200:
            self.assertIn("svg", hdrs.get("content-type", ""))
            self.assertTrue(body.startswith(b"<?xml"))


if __name__ == "__main__":
    unittest.main()
