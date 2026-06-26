"""Bundled Asymptote skill distribution.

The asyagent server vendors the ``asymptote-skill`` under ``asyagent/_skill/``
and exposes it through three HTTP endpoints so any LLM agent can discover the
skill, fetch individual files, download the whole bundle as an archive, and
learn how to call the render API — all from a single running server.

This module is pure standard library (``os``, ``mimetypes``, ``tarfile``,
``zipfile``, ``io``): no third-party dependencies, matching the rest of
asyagent.

The :class:`SkillBundle` is constructed once at server startup. If the skill
directory is missing or unreadable the bundle reports ``available=False`` and
the skill endpoints return a clear 404-style error, but the rest of the server
(render, health) keeps working.
"""

from __future__ import annotations

import io
import logging
import mimetypes
import os
import tarfile
import zipfile
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("asyagent.skill")

# Directory names never exposed through the skill endpoints — these are either
# build artifacts (``__pycache__``) or VCS cruft (``.git``) that may linger if
# the bundle was vendored from a working checkout. The vendored ``_skill/``
# copy is already clean, but this is a defensive second filter so a mis-staged
# ``ASYAGENT_SKILL_DIR`` override cannot leak secrets or binaries.
_EXCLUDE_DIRS = {".git", "__pycache__", ".pytest_cache", "vendor", "build", "dist"}
_EXCLUDE_FILENAMES = {".gitignore", ".gitattributes", ".DS_Store", "Thumbs.db"}

# MIME types for the file extensions the skill actually uses. ``mimetypes``
# guesses ``.asy`` as ``application/atom+xml`` etc., so we pin the correct ones
# explicitly and fall back to the system table + ``application/octet-stream``.
_MIME_OVERRIDES = {
    ".md": "text/markdown",
    ".asy": "text/x-asymptote",
    ".py": "text/x-python",
    ".svg": "image/svg+xml",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".texi": "application/x-texinfo",
}


def _guess_mime(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in _MIME_OVERRIDES:
        return _MIME_OVERRIDES[ext]
    mt, _ = mimetypes.guess_type(path)
    return mt or "application/octet-stream"


@dataclass
class SkillFile:
    """One file in the skill bundle."""

    path: str          # POSIX-style relative path, e.g. "docs/01-basics.md"
    size: int
    mime: str


@dataclass
class SkillBundle:
    """A vendored skill directory served over HTTP.

    Construct with a filesystem path (the ``_skill/`` package directory by
    default, overridable via ``ASYAGENT_SKILL_DIR``). If the path is missing
    the bundle is inert: ``available`` is ``False`` and all methods return a
    not-available sentinel so callers can surface a clean error.
    """

    root: Optional[str] = None
    available: bool = False
    skill_meta: dict = field(default_factory=dict)
    _files: list[SkillFile] = field(default_factory=list)

    def __init__(self, root: Optional[str]) -> None:
        self.root = root
        self.available = False
        self.skill_meta = {}
        self._files = []
        if not root or not os.path.isdir(root):
            logger.warning("skill bundle not available: %r is not a directory", root)
            return
        self._scan()
        self._parse_frontmatter()
        self.available = bool(self._files)
        if self.available:
            logger.info("skill bundle ready: %d files from %s", len(self._files), root)
        else:
            logger.warning("skill bundle empty after scan: %s", root)

    # ------------------------------------------------------------------ scan

    def _scan(self) -> None:
        assert self.root is not None
        files: list[SkillFile] = []
        for dirpath, dirnames, filenames in os.walk(self.root):
            # Prune excluded dirs in-place so os.walk doesn't descend into them.
            dirnames[:] = [d for d in dirnames if d not in _EXCLUDE_DIRS]
            for name in sorted(filenames):
                if name in _EXCLUDE_FILENAMES:
                    continue
                full = os.path.join(dirpath, name)
                if not os.path.isfile(full):
                    continue
                rel = os.path.relpath(full, self.root).replace(os.sep, "/")
                try:
                    size = os.path.getsize(full)
                except OSError:
                    continue
                files.append(SkillFile(path=rel, size=size, mime=_guess_mime(rel)))
        files.sort(key=lambda f: f.path)
        self._files = files

    def _parse_frontmatter(self) -> None:
        """Extract skill metadata from the YAML frontmatter in SKILL.md.

        The frontmatter is a simple ``key: value`` block between ``---``
        fences; we parse the flat scalar fields we care about without pulling
        in a YAML dependency. Nested mappings (``metadata:``) are skipped.
        """
        assert self.root is not None
        skill_md = os.path.join(self.root, "SKILL.md")
        meta: dict = {}
        if not os.path.isfile(skill_md):
            self.skill_meta = meta
            return
        try:
            with open(skill_md, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
        except OSError:
            self.skill_meta = meta
            return
        # A frontmatter block starts at the first line if it is "---".
        if not lines or lines[0].strip() != "---":
            self.skill_meta = meta
            return
        for line in lines[1:]:
            if line.strip() == "---":
                break
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            # Skip nested mapping keys (e.g. "metadata:") — value would be empty.
            if value:
                meta[key] = value
        self.skill_meta = meta

    # ----------------------------------------------------------------- public

    @property
    def files(self) -> list[SkillFile]:
        return self._files

    def read_file(self, rel_path: str) -> Optional[tuple[bytes, str]]:
        """Return ``(data, mime)`` for a relative path, or ``None`` if it
        is outside the bundle root or missing.

        Path-traversal is blocked by normalising under the root and checking
        the result stays inside it — same technique ``_serve_file`` uses for
        local storage.
        """
        if not self.available or not self.root:
            return None
        # Normalise the requested path against the root and reject escapes.
        full = os.path.normpath(os.path.join(self.root, rel_path))
        if not (full == self.root or full.startswith(self.root + os.sep)):
            return None
        if not os.path.isfile(full):
            return None
        try:
            with open(full, "rb") as f:
                data = f.read()
        except OSError:
            return None
        return data, _guess_mime(rel_path)

    def archive(self, fmt: str = "tar.gz") -> Optional[bytes]:
        """Stream the whole bundle into a single archive.

        ``fmt`` is ``"tar.gz"`` (default) or ``"zip"``. Returns ``None`` if
        the bundle is not available. The archive is built in memory with
        ``io.BytesIO``; the skill is small (~280 KB) so this is fine.
        """
        if not self.available or not self.root:
            return None
        buf = io.BytesIO()
        if fmt == "zip":
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for sf in self._files:
                    assert self.root is not None
                    full = os.path.join(self.root, sf.path.replace("/", os.sep))
                    zf.write(full, sf.path)
        else:
            with tarfile.open(fileobj=buf, mode="w:gz") as tf:
                for sf in self._files:
                    assert self.root is not None
                    full = os.path.join(self.root, sf.path.replace("/", os.sep))
                    tf.add(full, sf.path, recursive=False)
        return buf.getvalue()

    def manifest(self, base_url: str) -> dict:
        """Build the self-describing install manifest.

        ``base_url`` is the server's external base (no trailing slash), used to
        construct per-file and archive download URLs. The manifest has four
        sections an agent needs: ``skill`` (what it is), ``install`` (how to
        get it), ``files`` (lazy per-file fetch URLs), and ``render_api`` (how
        to turn ``.asy`` source into an image via this same server).
        """
        if not self.available:
            return {"ok": False, "available": False}

        files_payload = [
            {
                "path": sf.path,
                "url": f"{base_url}/v1/skill/files/{sf.path}",
                "size": sf.size,
                "mime": sf.mime,
            }
            for sf in self._files
        ]

        archive_url = f"{base_url}/v1/skill/archive.tar.gz"
        install_steps = [
            f"curl -sL {archive_url} | tar xz -C ~/.config/opencode/skills",
            "skillutils.asy is bundled with the skill and placed on the "
            "asyagent server's Asymptote module path automatically — no "
            "client-side setup is needed; `import skillutils;` works out "
            "of the box.",
        ]

        port_hint = ""
        if ":" in base_url.split("//", 1)[-1]:
            port_hint = f" (port {base_url.rsplit(':', 1)[-1]})"

        return {
            "ok": True,
            "available": True,
            "service": "asyagent",
            "skill": {
                "name": self.skill_meta.get("name", "asymptote"),
                "version": self.skill_meta.get("version"),
                "description": self.skill_meta.get("description"),
                "license": self.skill_meta.get("license"),
                "compatibility": self.skill_meta.get("compatibility"),
            },
            "install": {
                "method": "archive",
                "archive_url": archive_url,
                "archive_formats": ["tar.gz", "zip"],
                "steps": install_steps,
                "notes": (
                    f"The skill is distributed by this asyagent server at "
                    f"{base_url}{port_hint}. There is no separate GitHub "
                    f"clone — fetch the archive or individual files via the "
                    f"URLs below."
                ),
            },
            "files": files_payload,
            "render_api": {
                "endpoint": "POST /v1/render",
                "base_url": base_url,
                "auth": (
                    "optional — the server accepts an Authorization: Bearer "
                    "header but does not currently enforce it"
                ),
                "body": {
                    "text/plain": "raw .asy source (simplest form)",
                    "application/json": '{"source": "..."} or {"url": "https://..."}',
                },
                "headers": {
                    "X-Asy-Format": "pdf | svg | eps | png | jpg | jpeg",
                    "X-Asy-Encoding": "binary | base64 (inline mode only)",
                    "X-Asy-Mode": "inline | url",
                    "X-Asy-Dpi": "1-4096 (raster formats: png/jpg)",
                    "X-Asy-Timeout": "seconds (capped by server)",
                    "X-Asy-Filename": "suggested filename",
                },
                "response_modes": {
                    "inline/binary": "raw bytes with format-appropriate Content-Type",
                    "inline/base64": 'JSON {"ok":true,"data":"<base64>","format":"..."}',
                    "url": 'JSON {"ok":true,"url":"...","key":"..."}',
                },
                "example": (
                    f"curl -s {base_url}/v1/render "
                    f"--data-binary 'size(5cm); draw(unitcircle);' "
                    f"-H 'Content-Type: text/plain' "
                    f"-H 'X-Asy-Format: png' -o circle.png"
                ),
                "official_client": (
                    "scripts/asy_render.py — the skill's render client. "
                    "Fetch it from the files list above. It reads source "
                    "from -f <file>, -s <string>, or stdin, and writes the "
                    "rendered image to -o <path>. Needs ASY_API_KEY env var."
                ),
            },
        }
