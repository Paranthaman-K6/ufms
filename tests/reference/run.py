#!/usr/bin/env python3
"""End-to-end regression tests for the reference discovery and adaptation pipeline."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "universal-frontend-master" / "scripts"
INSPECT = SCRIPTS / "reference-inspect.js"
ANALYZE = SCRIPTS / "reference-analyze.py"
MATCH = SCRIPTS / "reference-match.py"
ADAPT = SCRIPTS / "reference-adapt.py"
VERIFY = SCRIPTS / "reference-verify.js"


def run(command, env, expected=0):
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
    if result.returncode != expected:
        raise AssertionError(
            "command returned " + str(result.returncode) + ", expected " + str(expected)
            + "\nCOMMAND: " + " ".join(map(str, command))
            + "\nSTDOUT:\n" + result.stdout + "\nSTDERR:\n" + result.stderr
        )
    return result


def seed_inspection(evidence):
    data = {
        "referenceId": "ref-test-01",
        "url": "https://reference.example.test/",
        "inspectedAt": "2026-11-07T00:00:00Z",
        "pageTitle": "Reference fixture",
        "status": "PASS",
        "elements": [{
            "elementType": "card",
            "index": 0,
            "selector": ".source-card",
            "tagName": "DIV",
            "className": "source-card",
            "textContent": "Example card",
            "styles": {
                "backgroundColor": "rgb(20, 30, 40)",
                "color": "rgb(250, 250, 250)",
                "fontFamily": "Georgia, serif",
                "fontSize": "18px",
                "fontWeight": "600",
                "lineHeight": "24px",
                "padding": "20px",
                "margin": "10px",
                "borderRadius": "12px",
                "boxShadow": "none",
                "display": "block",
                "gap": "0px",
                "width": "320px",
                "height": "180px"
            },
            "screenshotFile": "reference-screenshots/ref-test-01/card-0.png"
        }]
    }
    (evidence / "reference-inspect.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main():
    checks = 0
    for script in (INSPECT, VERIFY):
        run(["node", "--check", str(script)], os.environ.copy())
        checks += 1

    with tempfile.TemporaryDirectory(prefix="ufmw-reference-") as temp:
        base = Path(temp)
        project = base / "project"
        evidence = project / ".ufme" / "evidence"
        memory = project / ".ufme"
        evidence.mkdir(parents=True)
        env = os.environ.copy()
        env["UFME_PROJECT_ROOT"] = str(project)
        env["UFME_DIR"] = str(memory)
        env["UFME_EVIDENCE_DIR"] = str(evidence)
        seed_inspection(evidence)

        run([sys.executable, str(ANALYZE), str(evidence)], env)
        map_file = memory / "ELEMENT_MAP.md"
        map_text = map_file.read_text(encoding="utf-8")
        assert "ref-test-01:card:0" in map_text
        assert map_text.count("#### Element ID:") == 1
        checks += 1

        # Save user mapping, then re-run analysis. The mapping must survive and
        # the reference section must be updated in place rather than duplicated.
        map_text = map_text.replace(
            "- **Target selector**: _[user to specify]_",
            "- **Target selector**: .target-card"
        )
        map_text = map_text.replace(
            "- **Destination**: _[user to specify]_",
            "- **Destination**: homepage"
        )
        map_text = map_text.replace(
            "- **Aspects**: _[user to specify]_",
            "- **Aspects**: visual appearance, layout"
        )
        map_file.write_text(map_text, encoding="utf-8")
        run([sys.executable, str(ANALYZE), str(evidence)], env)
        map_text = map_file.read_text(encoding="utf-8")
        assert "- **Target selector**: .target-card" in map_text
        assert "- **Destination**: homepage" in map_text
        assert "- **Aspects**: visual appearance, layout" in map_text
        assert map_text.count("#### Element ID:") == 1
        refs_text = (memory / "REFERENCES.md").read_text(encoding="utf-8")
        assert refs_text.count("ufmw-reference:ref-test-01") == 2
        checks += 1

        run([sys.executable, str(MATCH), str(evidence)], env)
        plan = json.loads((evidence / "reference-match.json").read_text(encoding="utf-8"))
        assert plan["status"] == "MATCHED"
        assert plan["matchedElements"] == 1
        assert plan["verificationReady"] is True
        assert plan["elements"][0]["sourceStyles"]["backgroundColor"] == "rgb(20, 30, 40)"
        checks += 1

        run([sys.executable, str(ADAPT), str(evidence)], env)
        adaptation = json.loads((evidence / "reference-adapt.json").read_text(encoding="utf-8"))
        assert adaptation["totalElements"] == 1
        brief = (memory / "REFERENCE_IMPLEMENTATION.md").read_text(encoding="utf-8")
        assert "background-color: rgb(20, 30, 40)" in brief
        assert ".target-card" in brief
        assert "This is an implementation brief" in brief
        assert "<section class=" not in brief
        checks += 1

    # Multiple references remain distinct and keep their own source URLs.
    with tempfile.TemporaryDirectory(prefix="ufmw-multi-") as temp:
        project = Path(temp)
        memory = project / ".ufme"
        evidence = memory / "evidence"
        evidence.mkdir(parents=True)
        env = os.environ.copy()
        env["UFME_PROJECT_ROOT"] = str(project)
        env["UFME_DIR"] = str(memory)
        env["UFME_EVIDENCE_DIR"] = str(evidence)

        for ref_id, url, element_type, selector, text_value in (
            ("ref-alpha", "https://alpha.example.test/", "card", ".alpha-card", "Alpha card"),
            ("ref-beta", "https://beta.example.test/", "button", ".beta-button", "Beta button"),
        ):
            data = {
                "referenceId": ref_id,
                "url": url,
                "inspectedAt": "2026-11-07T00:00:00Z",
                "pageTitle": ref_id,
                "status": "PASS",
                "elements": [{
                    "elementType": element_type,
                    "index": 0,
                    "selector": selector,
                    "tagName": "DIV",
                    "className": selector.lstrip("."),
                    "textContent": text_value,
                    "styles": {"backgroundColor": "rgb(20, 30, 40)", "color": "rgb(250, 250, 250)"},
                    "screenshotFile": ref_id + "/element.png"
                }]
            }
            filename = "reference-inspect-" + ref_id + ".json"
            (evidence / filename).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            run([sys.executable, str(ANALYZE), str(evidence), filename], env)

        map_file = memory / "ELEMENT_MAP.md"
        map_text = map_file.read_text(encoding="utf-8")
        map_text = map_text.replace(
            "- **Reference selector**: .alpha-card\n- **Target selector**: _[user to specify]_\n- **Destination**: _[user to specify]_\n- **Aspects**: _[user to specify]_",
            "- **Reference selector**: .alpha-card\n- **Target selector**: .target-alpha\n- **Destination**: homepage\n- **Aspects**: visual appearance"
        )
        map_text = map_text.replace(
            "- **Reference selector**: .beta-button\n- **Target selector**: _[user to specify]_\n- **Destination**: _[user to specify]_\n- **Aspects**: _[user to specify]_",
            "- **Reference selector**: .beta-button\n- **Target selector**: .target-beta\n- **Destination**: product page\n- **Aspects**: visual appearance"
        )
        map_file.write_text(map_text, encoding="utf-8")
        run([sys.executable, str(MATCH), str(evidence)], env)
        plan = json.loads((evidence / "reference-match.json").read_text(encoding="utf-8"))
        assert plan["status"] == "MATCHED"
        assert plan["matchedElements"] == 2
        assert set(plan["referenceIds"]) == {"ref-alpha", "ref-beta"}
        urls_by_id = {item["referenceId"]: item["referenceUrl"] for item in plan["elements"]}
        assert urls_by_id == {
            "ref-alpha": "https://alpha.example.test/",
            "ref-beta": "https://beta.example.test/"
        }
        run([sys.executable, str(ADAPT), str(evidence)], env)
        adaptation = json.loads((evidence / "reference-adapt.json").read_text(encoding="utf-8"))
        assert adaptation["totalElements"] == 2
        assert set(adaptation["urls"]) == {
            "https://alpha.example.test/", "https://beta.example.test/"
        }
        assert {item["referenceUrl"] for item in adaptation["elements"]} == set(adaptation["urls"])
        checks += 1

    # Empty/unselected candidates must never become matches.
    with tempfile.TemporaryDirectory(prefix="ufmw-pending-") as temp:
        project = Path(temp)
        memory = project / ".ufme"
        evidence = memory / "evidence"
        evidence.mkdir(parents=True)
        env = os.environ.copy()
        env["UFME_PROJECT_ROOT"] = str(project)
        env["UFME_DIR"] = str(memory)
        env["UFME_EVIDENCE_DIR"] = str(evidence)
        seed_inspection(evidence)
        run([sys.executable, str(ANALYZE), str(evidence)], env)
        result = run([sys.executable, str(MATCH), str(evidence)], env, expected=1)
        plan = json.loads((evidence / "reference-match.json").read_text(encoding="utf-8"))
        assert plan["status"] == "PENDING"
        assert plan["matchedElements"] == 0
        assert plan["elements"] == []
        assert "No elements selected" in result.stderr
        checks += 1

    print(str(checks) + " reference pipeline checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
