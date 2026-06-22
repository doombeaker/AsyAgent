import base64
import json
import os
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request

from asyagent.config import Settings
from asyagent.server import build_server

SIMPLE_SRC = 'size(3cm); draw(unitcircle); label("$c$", (0,0), S);'
BAD_SRC = 'draw(foo bar baz'
PDF_MAGIC = b"%PDF"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

ASY_AVAILABLE = os.system("command -v asy >/dev/null 2>&1") == 0

_PROXY_LESS_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _urlopen(req, **kw):
    return _PROXY_LESS_OPENER.open(req, **kw)


def _free_port() -> int:
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class ServerFixture:
    def __init__(self):
        self.tmpdir = tempfile.mkdtemp(prefix="asyagent_test_")
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


class TestServerBasics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = ServerFixture()

    @classmethod
    def tearDownClass(cls):
        cls.fixture.stop()

    def test_root_info(self):
        r = _urlopen(f"{self.fixture.base_url}/")
        obj = json.loads(r.read())
        self.assertEqual(obj["service"], "asyagent")
        self.assertIn("formats", obj)
        self.assertIn("pdf", obj["formats"])
        self.assertEqual(obj["storage"]["backend"], "local")

    def test_healthz(self):
        r = _urlopen(f"{self.fixture.base_url}/healthz")
        obj = json.loads(r.read())
        self.assertEqual(obj["backend"], "local")
        self.assertTrue(obj["ok"])

    def test_404(self):
        with self.assertRaises(urllib.error.HTTPError) as cm:
            _urlopen(f"{self.fixture.base_url}/nonexistent")
        self.assertEqual(cm.exception.code, 400)


@unittest.skipUnless(ASY_AVAILABLE, "asy binary not available")
class TestRenderInlineBinary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = ServerFixture()

    @classmethod
    def tearDownClass(cls):
        cls.fixture.stop()

    def test_raw_source_pdf(self):
        req = urllib.request.Request(
            f"{self.fixture.base_url}/v1/render",
            data=SIMPLE_SRC.encode(),
            method="POST",
        )
        req.add_header("Content-Type", "text/plain")
        r = _urlopen(req)
        data = r.read()
        self.assertEqual(r.status, 200)
        self.assertEqual(r.headers["Content-Type"], "application/pdf")
        self.assertTrue(data.startswith(PDF_MAGIC))

    def test_json_source_pdf(self):
        body = json.dumps({"source": SIMPLE_SRC}).encode()
        req = urllib.request.Request(
            f"{self.fixture.base_url}/v1/render",
            data=body,
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        r = _urlopen(req)
        self.assertTrue(r.read().startswith(PDF_MAGIC))

    def test_svg_via_accept_header(self):
        req = urllib.request.Request(
            f"{self.fixture.base_url}/v1/render",
            data=SIMPLE_SRC.encode(),
            method="POST",
        )
        req.add_header("Content-Type", "text/plain")
        req.add_header("Accept", "image/svg+xml")
        r = _urlopen(req)
        self.assertEqual(r.headers["Content-Type"], "image/svg+xml")
        self.assertTrue(r.read().startswith(b"<?xml"))

    def test_png_via_header(self):
        req = urllib.request.Request(
            f"{self.fixture.base_url}/v1/render",
            data=SIMPLE_SRC.encode(),
            method="POST",
        )
        req.add_header("Content-Type", "text/plain")
        req.add_header("X-Asy-Format", "png")
        req.add_header("X-Asy-Dpi", "100")
        r = _urlopen(req)
        data = r.read()
        self.assertEqual(r.headers["Content-Type"], "image/png")
        self.assertTrue(data.startswith(PNG_MAGIC))

    def test_filename_header(self):
        req = urllib.request.Request(
            f"{self.fixture.base_url}/v1/render",
            data=SIMPLE_SRC.encode(),
            method="POST",
        )
        req.add_header("Content-Type", "text/plain")
        req.add_header("X-Asy-Filename", "circle.pdf")
        r = _urlopen(req)
        self.assertIn("circle.pdf", r.headers.get("Content-Disposition", ""))


@unittest.skipUnless(ASY_AVAILABLE, "asy binary not available")
class TestRenderBase64(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = ServerFixture()

    @classmethod
    def tearDownClass(cls):
        cls.fixture.stop()

    def test_base64_json_response(self):
        body = json.dumps({"source": SIMPLE_SRC}).encode()
        req = urllib.request.Request(
            f"{self.fixture.base_url}/v1/render",
            data=body,
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        req.add_header("X-Asy-Encoding", "base64")
        r = _urlopen(req)
        obj = json.loads(r.read())
        self.assertTrue(obj["ok"])
        self.assertEqual(obj["mode"], "inline")
        self.assertEqual(obj["encoding"], "base64")
        self.assertEqual(obj["format"], "pdf")
        decoded = base64.b64decode(obj["data"])
        self.assertTrue(decoded.startswith(PDF_MAGIC))


@unittest.skipUnless(ASY_AVAILABLE, "asy binary not available")
class TestRenderUrlMode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = ServerFixture()

    @classmethod
    def tearDownClass(cls):
        cls.fixture.stop()

    def test_url_mode_returns_url(self):
        body = json.dumps({"source": SIMPLE_SRC}).encode()
        req = urllib.request.Request(
            f"{self.fixture.base_url}/v1/render",
            data=body,
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        req.add_header("X-Asy-Mode", "url")
        r = _urlopen(req)
        obj = json.loads(r.read())
        self.assertTrue(obj["ok"])
        self.assertEqual(obj["mode"], "url")
        self.assertTrue(obj["url"].startswith("http"))
        self.assertIn("/files/", obj["url"])

        r2 = _urlopen(obj["url"])
        fetched = r2.read()
        self.assertTrue(fetched.startswith(PDF_MAGIC))

    def test_url_mode_with_storage_prefix(self):
        body = json.dumps({"source": SIMPLE_SRC}).encode()
        req = urllib.request.Request(
            f"{self.fixture.base_url}/v1/render",
            data=body,
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        req.add_header("X-Asy-Mode", "url")
        req.add_header("X-Asy-Storage-Prefix", "custom/prefix/")
        r = _urlopen(req)
        obj = json.loads(r.read())
        self.assertIn("custom/prefix/", obj["key"])


@unittest.skipUnless(ASY_AVAILABLE, "asy binary not available")
class TestRenderErrors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = ServerFixture()

    @classmethod
    def tearDownClass(cls):
        cls.fixture.stop()

    def test_compile_error(self):
        req = urllib.request.Request(
            f"{self.fixture.base_url}/v1/render",
            data=BAD_SRC.encode(),
            method="POST",
        )
        req.add_header("Content-Type", "text/plain")
        with self.assertRaises(urllib.error.HTTPError) as cm:
            _urlopen(req)
        self.assertEqual(cm.exception.code, 422)
        obj = json.loads(cm.exception.read())
        self.assertEqual(obj["error"]["code"], "compile_failed")

    def test_empty_source(self):
        req = urllib.request.Request(
            f"{self.fixture.base_url}/v1/render",
            data=b"",
            method="POST",
        )
        req.add_header("Content-Type", "text/plain")
        with self.assertRaises(urllib.error.HTTPError) as cm:
            _urlopen(req)
        self.assertEqual(cm.exception.code, 400)

    def test_json_missing_fields(self):
        body = json.dumps({"foo": "bar"}).encode()
        req = urllib.request.Request(
            f"{self.fixture.base_url}/v1/render",
            data=body,
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        with self.assertRaises(urllib.error.HTTPError) as cm:
            _urlopen(req)
        self.assertEqual(cm.exception.code, 400)

    def test_unsupported_format(self):
        req = urllib.request.Request(
            f"{self.fixture.base_url}/v1/render",
            data=SIMPLE_SRC.encode(),
            method="POST",
        )
        req.add_header("Content-Type", "text/plain")
        req.add_header("X-Asy-Format", "gif")
        with self.assertRaises(urllib.error.HTTPError) as cm:
            _urlopen(req)
        self.assertEqual(cm.exception.code, 400)
        obj = json.loads(cm.exception.read())
        self.assertEqual(obj["error"]["code"], "unsupported_format")


if __name__ == "__main__":
    unittest.main()
