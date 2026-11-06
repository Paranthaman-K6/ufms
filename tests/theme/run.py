#!/usr/bin/env python3
"""tests/theme/run.py — theme showcase PDF contract tests.

Covers the palette catalog schema, the generated PDF (page count, theme names,
project marker), `--only`, registry merging with a silent local fallback, and
the automatic generation hooked into `init-project.py`.

Usage: python3 tests/theme/run.py
Exit: 0 all pass, 1 failure.
"""

import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills/universal-frontend-master/scripts/theme-showcase.py"
PALETTES = ROOT / "skills/universal-frontend-master/data/palettes.csv"
INIT = ROOT / "skills/universal-frontend-master/scripts/init-project.py"
THEME_KEYS = ["bg", "surface", "text", "muted", "accent", "accent_alt"]

results = []


def test(name):
    def wrapper(fn):
        try:
            fn()
            results.append({"name": name, "status": "PASS"})
            print(f"PASS: {name}")
        except Exception as exc:  # noqa: BLE001 - test harness
            results.append({"name": name, "status": "FAIL", "detail": str(exc)})
            print(f"FAIL: {name} — {exc}")
            traceback.print_exc()
        return fn
    return wrapper


def load_module():
    spec = importlib.util.spec_from_file_location("theme_showcase", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, cwd=cwd, timeout=120,
    )


def page_count(pdf_bytes):
    marker = b"/Count "
    index = pdf_bytes.index(marker) + len(marker)
    return int(pdf_bytes[index:index + 4].split()[0])


def palette_rows():
    with PALETTES.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@test("every palette row is a complete theme")
def _():
    rows = palette_rows()
    assert len(rows) >= 10, len(rows)
    for row in rows:
        for key in THEME_KEYS:
            value = row.get(key, "")
            assert value.startswith("#") and len(value) in (4, 7), f"{row['name']}: {key}={value!r}"
        assert row.get("font_pairing", "").strip(), f"{row['name']}: no font pairing"


@test("a palette row missing theme columns is rejected")
def _():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        broken = Path(tmp) / "palettes.csv"
        broken.write_text("name,description\nOnly Name,no colours\n", encoding="utf-8")
        try:
            module.load_local_themes(broken)
        except SystemExit as exc:
            assert "missing columns" in str(exc), str(exc)
            return
        raise AssertionError("incomplete palette catalog was accepted")


@test("the showcase renders one page per theme")
def _():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "showcase.pdf"
        proc = run("--target", tmp, "--out", str(out))
        assert proc.returncode == 0, proc.stderr
        data = out.read_bytes()
        assert data.startswith(b"%PDF-1.4"), data[:8]
        assert data.rstrip().endswith(b"%%EOF"), data[-16:]
        assert page_count(data) == len(palette_rows()), page_count(data)
        for row in palette_rows():
            assert row["name"].encode() in data, f"{row['name']} missing from PDF"


@test("the project's own theme is marked and shown first")
def _():
    with tempfile.TemporaryDirectory() as tmp:
        ufme = Path(tmp) / ".ufme"
        ufme.mkdir()
        (ufme / "design-choices.json").write_text(
            json.dumps({"palette": "Midnight Ocean", "font": "Fraunces + Karla"}),
            encoding="utf-8",
        )
        out = ufme / "showcase.pdf"
        proc = run("--target", tmp, "--out", str(out))
        assert proc.returncode == 0, proc.stderr
        data = out.read_bytes()
        first_page = data.split(b"stream\n")[1]
        assert b"YOUR PROJECT" in first_page
        assert b"Midnight Ocean" in first_page


@test("--only renders a single page and an unknown name exits 3")
def _():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "one.pdf"
        proc = run("--target", tmp, "--out", str(out), "--only", "midnight")
        assert proc.returncode == 0, proc.stderr
        assert page_count(out.read_bytes()) == 1
        missing = run("--target", tmp, "--out", str(out), "--only", "not-a-theme")
        assert missing.returncode == 3, (missing.returncode, missing.stderr)
        assert "no theme matches" in missing.stderr


@test("registry themes are appended and deduped; a failing client is ignored")
def _():
    module = load_module()
    registry_theme = {
        "name": "Registry Only",
        "description": "from the MCP registry",
        "best_for": "shared team themes",
        "bg": "#101010", "surface": "#1a1a1a", "text": "#f0f0f0",
        "muted": "#8a8a8a", "accent": "#ff6600", "accent_alt": "#00aaff",
        "display": "Helvetica", "body": "Helvetica", "mono": "",
    }
    duplicate = dict(registry_theme, name=palette_rows()[0]["name"])
    with tempfile.TemporaryDirectory() as tmp:
        stub = Path(tmp) / "stub.py"
        entries = [
            {"name": t["name"], "category": "theme", "theme": t}
            for t in (registry_theme, duplicate)
        ]
        stub.write_text(
            "import json\nprint(json.dumps(" + repr(entries) + "))\n",
            encoding="utf-8",
        )
        themes = module.collect_themes(tmp, use_registry=True, client=str(stub))
        names = [t["name"] for t in themes]
        assert "Registry Only" in names, names
        assert names.count(palette_rows()[0]["name"]) == 1, names

        failing = Path(tmp) / "failing.py"
        failing.write_text("raise SystemExit(1)\n", encoding="utf-8")
        local = module.collect_themes(tmp, use_registry=True, client=str(failing))
        assert [t["name"] for t in local] == [row["name"] for row in palette_rows()]


@test("init-project.py generates the showcase automatically")
def _():
    with tempfile.TemporaryDirectory() as tmp:
        proc = subprocess.run(
            [sys.executable, str(INIT), tmp, "--palette", "Forest Sustainability",
             "--font", "Fraunces + Karla", "--style", "Warm Editorial",
             "--profile", "basic", "--project-name", "Theme Test"],
            capture_output=True, text=True, timeout=180,
        )
        assert proc.returncode == 0, proc.stderr
        showcase = Path(tmp) / ".ufme" / "theme-showcase.pdf"
        assert showcase.is_file(), proc.stdout
        assert page_count(showcase.read_bytes()) == len(palette_rows())
        choices = json.loads((Path(tmp) / ".ufme" / "design-choices.json").read_text())
        assert choices["palette"] == "Forest Sustainability"


def main():
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    print(f"\n{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
