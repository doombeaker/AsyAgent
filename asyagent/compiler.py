from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import uuid
import zipfile
from dataclasses import dataclass

from .errors import CompileError, CompileTimeout, RasterError, UnsupportedFormat

NATIVE_FORMATS = ("pdf", "svg", "eps")
RASTER_FORMATS = ("png", "jpg", "jpeg")
SUPPORTED_FORMATS = NATIVE_FORMATS + RASTER_FORMATS

MIME_BY_EXT = {
    "pdf": "application/pdf",
    "svg": "image/svg+xml",
    "eps": "application/postscript",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "zip": "application/zip",
}

GS_DEVICE = {
    "png": "pngalpha",
    "jpg": "jpeg",
    "jpeg": "jpeg",
}

OUTPUT_EXTS = set(NATIVE_FORMATS)


@dataclass
class CompiledFile:
    name: str
    ext: str
    mime: str
    data: bytes

    @property
    def size(self) -> int:
        return len(self.data)


def validate_format(fmt: str) -> str:
    fmt = fmt.lower()
    if fmt not in SUPPORTED_FORMATS:
        raise UnsupportedFormat(
            f"unsupported format: {fmt!r}",
            detail=f"supported: {', '.join(SUPPORTED_FORMATS)}",
        )
    return fmt


def _snapshot(workdir: str) -> set[str]:
    names = set()
    for entry in os.listdir(workdir):
        if os.path.isfile(os.path.join(workdir, entry)):
            names.add(entry)
    return names


def _run(cmd, *, cwd, timeout, label) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.setdefault("HOME", os.path.expanduser("~"))
    try:
        return subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"") + b"\n" + (e.stderr or b"")
        raise CompileTimeout(
            f"{label} timed out after {timeout}s",
            detail=out.decode("utf-8", "replace")[-2000:],
        ) from e


def _rasterize(pdf_path, *, workdir, stem, ext, device, dpi, gs_bin, timeout) -> list[str]:
    pattern = os.path.join(workdir, f"{stem}_{ext}_%d.{ext}")
    cmd = [
        gs_bin,
        "-q",
        "-dNOPAUSE",
        "-dBATCH",
        "-dSAFER",
        f"-sDEVICE={device}",
        f"-r{dpi}",
        "-dTextAlphaBits=4",
        "-dGraphicsAlphaBits=4",
        f"-sOutputFile={pattern}",
        pdf_path,
    ]
    try:
        result = subprocess.run(
            cmd, cwd=workdir, capture_output=True, timeout=timeout
        )
    except subprocess.TimeoutExpired as e:
        raise RasterError(
            f"ghostscript timed out after {timeout}s",
            detail=(e.stderr or b"").decode("utf-8", "replace")[-2000:],
        ) from e
    if result.returncode != 0:
        raise RasterError(
            "ghostscript rasterization failed",
            detail=result.stderr.decode("utf-8", "replace")[-2000:],
        )

    produced = sorted(
        f for f in os.listdir(workdir) if f.startswith(f"{stem}_{ext}_") and f.endswith(f".{ext}")
    )
    if not produced:
        raise RasterError("ghostscript produced no output", detail=pdf_path)
    return produced


def compile_source(
    source: str,
    *,
    fmt: str,
    dpi: int,
    timeout: int,
    asy_bin: str,
    gs_bin: str,
    tmp_dir: str | None,
) -> list[CompiledFile]:
    fmt = validate_format(fmt)
    native = fmt if fmt in NATIVE_FORMATS else "pdf"

    workdir = tempfile.mkdtemp(prefix="asyagent_", dir=tmp_dir)
    try:
        input_path = os.path.join(workdir, "input.asy")
        with open(input_path, "w", encoding="utf-8") as f:
            f.write(source)
            if not source.endswith("\n"):
                f.write("\n")

        before = _snapshot(workdir)
        cmd = [asy_bin, "-f", native, "-o", "out", "input.asy"]
        result = _run(cmd, cwd=workdir, timeout=timeout, label="asy")

        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", "replace")
            stdout = result.stdout.decode("utf-8", "replace")
            detail = (stderr + "\n" + stdout).strip()[-4000:]
            raise CompileError("asymptote compilation failed", detail=detail)

        after = _snapshot(workdir)
        new_outputs = sorted(
            n for n in (after - before) if n.rsplit(".", 1)[-1].lower() in OUTPUT_EXTS
        )

        if not new_outputs:
            listing = sorted(after - before)
            raise CompileError(
                "compilation produced no output",
                detail=f"files produced: {listing}",
            )

        if fmt in NATIVE_FORMATS:
            chosen = new_outputs
        else:
            device = GS_DEVICE[fmt]
            chosen = []
            for pdf_name in new_outputs:
                stem = pdf_name.rsplit(".", 1)[0]
                raster_names = _rasterize(
                    os.path.join(workdir, pdf_name),
                    workdir=workdir,
                    stem=stem,
                    ext=fmt,
                    device=device,
                    dpi=dpi,
                    gs_bin=gs_bin,
                    timeout=timeout,
                )
                chosen.extend(raster_names)

        chosen = sorted(set(chosen))
        files: list[CompiledFile] = []
        for name in chosen:
            ext = name.rsplit(".", 1)[-1].lower()
            if ext == "jpeg":
                ext = "jpg"
            with open(os.path.join(workdir, name), "rb") as f:
                data = f.read()
            files.append(
                CompiledFile(name=name, ext=ext, mime=MIME_BY_EXT.get(ext, "application/octet-stream"), data=data)
            )
        return files
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def select_or_bundle(files: list[CompiledFile]) -> CompiledFile:
    if not files:
        raise CompileError("no output to return")
    if len(files) == 1:
        return files[0]

    import io

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.writestr(f.name, f.data)
    return CompiledFile(
        name="asyagent-output.zip",
        ext="zip",
        mime=MIME_BY_EXT["zip"],
        data=buf.getvalue(),
    )
