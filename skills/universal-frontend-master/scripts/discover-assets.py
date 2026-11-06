#!/usr/bin/env python3
"""
discover-assets.py — inventory project images, fonts, icons, and video.

Writes .ufme/ASSET_MANIFEST.md with SHA-256 duplicate detection, size,
image dimensions/aspect ratio, license hints, and broken-asset status.
Read-only scan; the manifest is the only write.

Safety: project-local only.
"""

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
UFME = ROOT / ".ufme"
MANIFEST = UFME / "ASSET_MANIFEST.md"

EXTENSIONS = {
    "jpg", "jpeg", "png", "gif", "webp", "svg", "ico",
    "woff", "woff2", "ttf", "otf", "mp4", "webm", "ogv",
}
SKIP_PARTS = {"node_modules", ".git"}
IMAGE_EXT = {"jpg", "jpeg", "png", "gif", "webp", "svg", "ico"}
FONT_EXT = {"woff", "woff2", "ttf", "otf"}
VIDEO_EXT = {"mp4", "webm", "ogv"}


def log(msg):
    print(f"[discover-assets] {msg}")


def pool(patterns):
    return re.compile("|".join(patterns), re.I)


UNSPLASH = pool([r"unsplash\.com", r"source\.unsplash\.com"])
PEXELS = pool([r"pexels\.com"])
PIXABAY = pool([r"pixabay\.com"])
WIKI = pool([r"wikimedia\.org", r"wikipedia\.org"])
FONTS = pool([r"fontsource", r"googleapis\.com/css"])
LUCIDE = pool([r"lucide", r"lucide-react"])
PHOSPHOR = pool([r"phosphor"])


def hash_file(path):
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return "unknown"


def image_dimensions(path):
    if shutil.which("identify"):
        try:
            out = subprocess.run(
                ["identify", "-format", "%wx%h", str(path)],
                capture_output=True, text=True, timeout=30,
            ).stdout.strip()
            if out:
                return out
        except (OSError, subprocess.SubprocessError):
            pass
    if shutil.which("file"):
        try:
            out = subprocess.run(
                ["file", str(path)], capture_output=True, text=True, timeout=30
            ).stdout
            m = re.search(r"(\d+) x (\d+)", out)
            if m:
                return f"{m.group(1)}x{m.group(2)}"
        except (OSError, subprocess.SubprocessError):
            pass
    return "unknown"


def aspect_ratio(dims):
    if dims == "unknown" or "x" not in dims:
        return "unknown"
    w, h = dims.split("x", 1)
    try:
        return f"{int(w) / int(h):.2f}" if int(h) else "unknown"
    except ValueError:
        return "unknown"


def license_hint(path):
    s = str(path)
    for test, label in ((UNSPLASH, "Unsplash (free, attribution appreciated)"),
                        (PEXELS, "Pexels (free)"),
                        (PIXABAY, "Pixabay (free)"),
                        (WIKI, "Wikimedia Commons (varies; check file page)"),
                        (FONTS, "Google Fonts (SIL OFL)"),
                        (LUCIDE, "Lucide (ISC)"),
                        (PHOSPHOR, "Phosphor Icons (MIT)")):
        if test.search(s):
            return label
    return "Verify"


def is_broken_image(path, ext):
    if ext == "svg":
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return True
        return "<svg" not in text or "</svg>" not in text
    if shutil.which("identify"):
        try:
            return subprocess.run(
                ["identify", "-ping", str(path)],
                capture_output=True, timeout=30,
            ).returncode != 0
        except (OSError, subprocess.SubprocessError):
            return False
    return False


def collect():
    found = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_PARTS]
        if Path(dirpath) == UFME / "evidence":
            dirnames[:] = []
            continue
        for name in filenames:
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            if ext in EXTENSIONS:
                found.append(Path(dirpath) / name)
    return found


def main():
    UFME.mkdir(parents=True, exist_ok=True)
    assets = collect()

    hashes = {}
    order = []
    for path in assets:
        h = hash_file(path)
        hashes.setdefault(h, []).append(str(path))
        order.append((path, h))

    dupe_groups = {h: files for h, files in hashes.items() if len(files) > 1}

    lines = [
        "# Asset Manifest",
        f"Generated: {__import__('datetime').datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
        "| Asset | Type | Path | Size (bytes) | SHA-256 | Dimensions | Aspect Ratio | License hint | Status |",
        "|-------|------|------|-------------|---------|------------|--------------|--------------|--------|",
    ]

    counts = {"assets": 0, "dup": len(dupe_groups), "broken": 0}
    for path, h in order:
        ext = path.suffix.lower().lstrip(".")
        if ext in IMAGE_EXT:
            ftype = "image"
        elif ext in FONT_EXT:
            ftype = "font"
        elif ext in VIDEO_EXT:
            ftype = "video"
        else:
            ftype = "other"
        try:
            size = path.stat().st_size
        except OSError:
            size = 0

        dims = image_dimensions(path) if ftype == "image" else "unknown"
        ar = aspect_ratio(dims) if ftype == "image" else "unknown"
        broken = ftype == "image" and is_broken_image(path, ext)
        if broken:
            counts["broken"] += 1
        if h in dupe_groups:
            status_ = "duplicate"
        elif broken:
            status_ = "broken"
        else:
            status_ = "locally discovered"
        lines.append(
            f"| {path} | {ftype} | {path} | {size} | {h} | {dims} | {ar} | "
            f"{license_hint(path)} | {status_} |"
        )
        counts["assets"] += 1

    lines += [
        "",
        f"Total assets discovered: {counts['assets']}",
        f"Duplicate groups detected: {counts['dup']}",
        f"Broken assets detected: {counts['broken']}",
        "",
        "## Status definitions",
        "| Status | Meaning |",
        "|--------|---------|",
        "| locally discovered | Asset found in project; license not yet verified |",
        "| duplicate | Same hash as another asset; consider removing |",
        "| broken | Image file appears corrupt or malformed |",
        "| remotely discovered candidate | Found via external provider; not downloaded |",
        "| downloaded | Asset downloaded to project; license not verified |",
        "| license verified | License confirmed for intended use |",
        "| approved for production use | Approved by orchestrator for production |",
        "",
        "## Optimization notes",
        "- Convert PNG to WebP where supported.",
        "- Subset fonts to used glyphs.",
        "- Verify license for every asset before production use.",
        "- Remove duplicate assets to reduce bundle size.",
    ]

    fd, tmp = tempfile.mkstemp(dir=str(UFME), prefix=".asset-manifest.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        os.replace(tmp, MANIFEST)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

    log(
        f"Asset manifest written to {MANIFEST} ({counts['assets']} assets, "
        f"{counts['dup']} duplicate groups, {counts['broken']} broken)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
