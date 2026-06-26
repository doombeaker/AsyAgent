import io
import json
import os
import tarfile
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
import zipfile

from asyagent.config import Settings
from asyagent.server import build_server

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


class SkillFixture:
    """A live asyagent server using the packaged _skill/ bundle."""

    def __init__(self):
        self.tmpdir = tempfile.mkdtemp(prefix="asyagent_skill_test_")
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


class TestSkillEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = SkillFixture()

    @classmethod
    def tearDownClass(cls):
        cls.fixture.stop()

    def test_root_lists_skill_endpoints(self):
        r = _urlopen(f"{self.fixture.base_url}/")
        obj = json.loads(r.read())
        self.assertTrue(obj["skill_available"])
        endpoints = obj["endpoints"]
        self.assertEqual(endpoints["skill"], "GET /v1/skill")
        self.assertEqual(endpoints["skill_files"], "GET /v1/skill/files/{path}")
        self.assertEqual(endpoints["skill_archive"], "GET /v1/skill/archive[.tar.gz|.zip]")

    def test_manifest_shape(self):
        r = _urlopen(f"{self.fixture.base_url}/v1/skill")
        obj = json.loads(r.read())
        self.assertTrue(obj["ok"])
        self.assertTrue(obj["available"])
        self.assertEqual(obj["service"], "asyagent")
        self.assertEqual(obj["skill"]["name"], "asymptote")
        self.assertEqual(obj["skill"]["license"], "LGPL-3.0")
        self.assertEqual(obj["install"]["method"], "archive")
        self.assertTrue(obj["install"]["archive_url"].endswith("/v1/skill/archive.tar.gz"))
        self.assertIsInstance(obj["install"]["steps"], list)
        self.assertGreater(len(obj["install"]["steps"]), 0)
        self.assertIsInstance(obj["files"], list)
        self.assertGreater(len(obj["files"]), 5)
        for f in obj["files"]:
            self.assertIn("path", f)
            self.assertIn("url", f)
            self.assertIn("size", f)
            self.assertTrue(f["url"].startswith(self.fixture.base_url))
        self.assertEqual(obj["render_api"]["endpoint"], "POST /v1/render")
        self.assertEqual(obj["render_api"]["base_url"], self.fixture.base_url)
        self.assertIn("example", obj["render_api"])
        self.assertIn("asy_render.py", obj["render_api"]["official_client"])

    def test_manifest_includes_key_files(self):
        r = _urlopen(f"{self.fixture.base_url}/v1/skill")
        obj = json.loads(r.read())
        paths = {f["path"] for f in obj["files"]}
        for expected in ("SKILL.md", "README.md", "lib/skillutils.asy",
                         "scripts/asy_render.py", "docs/01-basics.md"):
            self.assertIn(expected, paths, f"missing {expected} in manifest files")

    def test_fetch_skill_file(self):
        r = _urlopen(f"{self.fixture.base_url}/v1/skill/files/SKILL.md")
        data = r.read()
        self.assertEqual(r.status, 200)
        self.assertEqual(r.headers["Content-Type"], "text/markdown")
        self.assertTrue(data.startswith(b"---"))
        self.assertIn(b"name: asymptote", data)
        self.assertIn("Cache-Control", r.headers)

    def test_fetch_nested_file(self):
        r = _urlopen(f"{self.fixture.base_url}/v1/skill/files/docs/01-basics.md")
        data = r.read()
        self.assertEqual(r.status, 200)
        self.assertGreater(len(data), 1000)

    def test_fetch_skillutils(self):
        r = _urlopen(f"{self.fixture.base_url}/v1/skill/files/lib/skillutils.asy")
        self.assertEqual(r.status, 200)
        self.assertEqual(r.headers["Content-Type"], "text/x-asymptote")
        self.assertIn(b"label_box_pic", r.read())

    def test_fetch_render_client(self):
        r = _urlopen(f"{self.fixture.base_url}/v1/skill/files/scripts/asy_render.py")
        self.assertEqual(r.status, 200)
        self.assertEqual(r.headers["Content-Type"], "text/x-python")
        body = r.read()
        self.assertIn(b"def render(", body)
        self.assertIn(b"/v1/render", body)

    def test_file_url_in_manifest_works(self):
        manifest = json.loads(_urlopen(f"{self.fixture.base_url}/v1/skill").read())
        url = manifest["files"][0]["url"]
        r = _urlopen(url)
        self.assertEqual(r.status, 200)

    def test_path_traversal_blocked(self):
        for evil in ("../etc/passwd", "../../asyagent/server.py", "/etc/passwd",
                     "..%2f..%2fetc%2fpasswd", "docs/../../etc/passwd",
                     "docs/../../../etc/passwd"):
            with self.assertRaises(urllib.error.HTTPError) as cm:
                _urlopen(f"{self.fixture.base_url}/v1/skill/files/{evil}")
            self.assertEqual(cm.exception.code, 404)

    def test_nonexistent_file_404(self):
        with self.assertRaises(urllib.error.HTTPError) as cm:
            _urlopen(f"{self.fixture.base_url}/v1/skill/files/does/not/exist.md")
        self.assertEqual(cm.exception.code, 404)

    def test_archive_tar_gz(self):
        r = _urlopen(f"{self.fixture.base_url}/v1/skill/archive.tar.gz")
        data = r.read()
        self.assertEqual(r.status, 200)
        self.assertEqual(r.headers["Content-Type"], "application/gzip")
        self.assertIn("attachment", r.headers["Content-Disposition"])
        self.assertIn("asymptote-skill.tar.gz", r.headers["Content-Disposition"])
        self.assertTrue(data[:4] == b"\x1f\x8b\x08\x00")
        names = tarfile.open(fileobj=io.BytesIO(data), mode="r:gz").getnames()
        self.assertIn("SKILL.md", names)
        self.assertIn("lib/skillutils.asy", names)
        self.assertIn("scripts/asy_render.py", names)
        self.assertNotIn(".git", names)

    def test_archive_zip(self):
        r = _urlopen(f"{self.fixture.base_url}/v1/skill/archive.zip")
        data = r.read()
        self.assertEqual(r.status, 200)
        self.assertEqual(r.headers["Content-Type"], "application/zip")
        zf = zipfile.ZipFile(io.BytesIO(data))
        names = zf.namelist()
        self.assertIn("SKILL.md", names)
        self.assertIn("lib/skillutils.asy", names)
        self.assertIn("scripts/asy_render.py", names)
        self.assertNotIn(".git", names)

    def test_archive_default_format(self):
        r = _urlopen(f"{self.fixture.base_url}/v1/skill/archive")
        data = r.read()
        self.assertEqual(r.status, 200)
        self.assertTrue(data[:4] == b"\x1f\x8b\x08\x00")

    def test_skill_trailing_slash(self):
        r = _urlopen(f"{self.fixture.base_url}/v1/skill/")
        self.assertEqual(r.status, 200)
        obj = json.loads(r.read())
        self.assertTrue(obj["ok"])


class TestEmptySkillBundle(unittest.TestCase):
    """A bundle pointing at a nonexistent directory is inert, not fatal."""

    def test_empty_bundle(self):
        from asyagent.skill import SkillBundle

        b = SkillBundle("/nonexistent/path/that/does/not/exist")
        self.assertFalse(b.available)
        manifest = b.manifest("http://x")
        self.assertFalse(manifest["ok"])
        self.assertFalse(manifest["available"])
        self.assertIsNone(b.read_file("anything"))
        self.assertIsNone(b.archive())


if __name__ == "__main__":
    unittest.main()
