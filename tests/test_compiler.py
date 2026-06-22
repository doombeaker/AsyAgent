import os
import unittest
import zipfile

from asyagent.compiler import (
    MIME_BY_EXT,
    SUPPORTED_FORMATS,
    CompiledFile,
    compile_source,
    select_or_bundle,
)
from asyagent.errors import CompileError, UnsupportedFormat

SIMPLE_SRC = 'size(5cm); draw(unitcircle); label("$x^2+y^2=1$", (0,-1.2), S);'
MULTI_SRC = (
    'size(3cm); draw(unitcircle); shipout("a");\n'
    'draw(unitsquare); shipout("b");\n'
)
BAD_SRC = 'draw(foo bar baz'

ASY_BIN = os.environ.get("ASYAGENT_ASY_BIN", "asy")
GS_BIN = os.environ.get("ASYAGENT_GS_BIN", "gs")

PDF_MAGIC = b"%PDF"
SVG_MAGIC = b"<?xml"
EPS_MAGIC = b"%!PS"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPG_MAGIC = b"\xff\xd8\xff"


@unittest.skipUnless(os.system(f"command -v {ASY_BIN} >/dev/null 2>&1") == 0, "asy not available")
class TestCompileNative(unittest.TestCase):
    def test_pdf(self):
        files = compile_source(SIMPLE_SRC, fmt="pdf", dpi=150, timeout=60, asy_bin=ASY_BIN, gs_bin=GS_BIN, tmp_dir=None)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].ext, "pdf")
        self.assertEqual(files[0].mime, "application/pdf")
        self.assertTrue(files[0].data.startswith(PDF_MAGIC))
        self.assertGreater(files[0].size, 1000)

    def test_svg(self):
        files = compile_source(SIMPLE_SRC, fmt="svg", dpi=150, timeout=60, asy_bin=ASY_BIN, gs_bin=GS_BIN, tmp_dir=None)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].ext, "svg")
        self.assertTrue(files[0].data.startswith(SVG_MAGIC))

    def test_eps(self):
        files = compile_source(SIMPLE_SRC, fmt="eps", dpi=150, timeout=60, asy_bin=ASY_BIN, gs_bin=GS_BIN, tmp_dir=None)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].ext, "eps")
        self.assertTrue(files[0].data.startswith(EPS_MAGIC))


@unittest.skipUnless(
    os.system(f"command -v {ASY_BIN} >/dev/null 2>&1") == 0
    and os.system(f"command -v {GS_BIN} >/dev/null 2>&1") == 0,
    "asy and gs not available",
)
class TestCompileRaster(unittest.TestCase):
    def test_png(self):
        files = compile_source(SIMPLE_SRC, fmt="png", dpi=150, timeout=60, asy_bin=ASY_BIN, gs_bin=GS_BIN, tmp_dir=None)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].ext, "png")
        self.assertTrue(files[0].data.startswith(PNG_MAGIC))

    def test_jpg(self):
        files = compile_source(SIMPLE_SRC, fmt="jpg", dpi=150, timeout=60, asy_bin=ASY_BIN, gs_bin=GS_BIN, tmp_dir=None)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].ext, "jpg")
        self.assertTrue(files[0].data.startswith(JPG_MAGIC))

    def test_jpeg_alias(self):
        files = compile_source(SIMPLE_SRC, fmt="jpeg", dpi=150, timeout=60, asy_bin=ASY_BIN, gs_bin=GS_BIN, tmp_dir=None)
        self.assertEqual(files[0].ext, "jpg")


class TestCompileErrors(unittest.TestCase):
    def test_unsupported_format(self):
        with self.assertRaises(UnsupportedFormat):
            compile_source(SIMPLE_SRC, fmt="gif", dpi=150, timeout=60, asy_bin=ASY_BIN, gs_bin=GS_BIN, tmp_dir=None)

    @unittest.skipUnless(os.system(f"command -v {ASY_BIN} >/dev/null 2>&1") == 0, "asy not available")
    def test_compile_error(self):
        with self.assertRaises(CompileError) as cm:
            compile_source(BAD_SRC, fmt="pdf", dpi=150, timeout=60, asy_bin=ASY_BIN, gs_bin=GS_BIN, tmp_dir=None)
        self.assertIn("failed", cm.exception.message.lower())
        self.assertIsNotNone(cm.exception.detail)


class TestSelectOrBundle(unittest.TestCase):
    def test_single_file(self):
        f = CompiledFile(name="out.pdf", ext="pdf", mime="application/pdf", data=b"%PDF...")
        result = select_or_bundle([f])
        self.assertIs(result, f)

    def test_multi_files_bundled_as_zip(self):
        f1 = CompiledFile(name="a.pdf", ext="pdf", mime="application/pdf", data=b"%PDF-1")
        f2 = CompiledFile(name="b.pdf", ext="pdf", mime="application/pdf", data=b"%PDF-2")
        result = select_or_bundle([f1, f2])
        self.assertEqual(result.ext, "zip")
        self.assertEqual(result.mime, "application/zip")
        import io

        with zipfile.ZipFile(io.BytesIO(result.data)) as zf:
            names = sorted(zf.namelist())
            self.assertEqual(names, ["a.pdf", "b.pdf"])
            self.assertEqual(zf.read("a.pdf"), b"%PDF-1")

    def test_empty_raises(self):
        with self.assertRaises(CompileError):
            select_or_bundle([])


class TestMimeMapping(unittest.TestCase):
    def test_all_formats_have_mime(self):
        for fmt in SUPPORTED_FORMATS:
            self.assertIn(fmt, MIME_BY_EXT, f"missing MIME for {fmt}")


if __name__ == "__main__":
    unittest.main()
