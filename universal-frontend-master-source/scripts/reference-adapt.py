#!/usr/bin/env python3
"""
reference-adapt.py — Adapt reference elements to target project's design system.

Reads .ufme/evidence/reference-match.json and generates:
  .ufme/evidence/reference-adapt.json  — adaptation plan with CSS variables
  .ufme/REFERENCE_IMPLEMENTATION.md    — implementation code for each element

Usage:
  python3 universal-frontend-master-source/scripts/reference-adapt.py [evidenceDir]
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UFME = ROOT / ".ufme"
EVIDENCE = Path(os.environ.get("UFME_EVIDENCE_DIR") or (UFME / "evidence"))


def load_match(evidence_dir):
    match_file = evidence_dir / "reference-match.json"
    if not match_file.exists():
        return None
    return json.loads(match_file.read_text(encoding="utf-8"))


def generate_css_variables(match_plan):
    """Generate CSS variable definitions from adapted elements."""
    vars_css = []
    vars_css.append("/* Reference-adapted CSS variables */")
    vars_css.append(":root {")
    for el in match_plan["elements"]:
        if el.get("status") != "matched":
            continue
        for var in el.get("cssVariables", []):
            # Default fallback values
            fallbacks = {
                "--ufmw-ref-bg-color": "#ffffff",
                "--ufmw-ref-text-color": "#333333",
                "--ufmw-ref-font-family": "system-ui, -apple-system, sans-serif",
                "--ufmw-ref-font-size": "1rem",
            }
            val = fallbacks.get(var, "#000000")
            vars_css.append(f"  {var}: {val};")
    vars_css.append("}")
    vars_css.append("")
    return "\n".join(vars_css)


def generate_component_code(match_plan):
    """Generate HTML/CSS component code for each adapted element."""
    components = []
    for el in match_plan["elements"]:
        if el.get("status") != "matched":
            continue
        etype = el.get("elementType", "component")
        dest = el.get("destination", "unknown")
        aspects = el.get("aspects", "combination")

        component = f"""
## Component: {etype.title()} ({el['elementId']})

**Destination**: {dest}
**Aspects**: {aspects}

### HTML
```html
<!-- Adapted from reference: {match_plan['url']} -->
<section class="ufmw-ref-{etype}" data-ref-id="{el['elementId']}">
  <div class="ufmw-ref-container">
    <!-- Content adapted from reference element -->
    <div class="ufmw-ref-content" style="color: var(--ufmw-ref-text-color);">
      {el.get('text', 'Content from reference')[:100]}
    </div>
  </div>
</section>
```

### CSS
```css
.ufmw-ref-{etype} {{
  background-color: var(--ufmw-ref-bg-color);
  color: var(--ufmw-ref-text-color);
  font-family: var(--ufmw-ref-font-family);
  font-size: var(--ufmw-ref-font-size);
  /* Aspects: {aspects} */
  /* Destination: {dest} */
}}
```

"""
        components.append(component)
    return "\n".join(components)


def adapt(evidence_dir=EVIDENCE, ufme_dir=UFME):
    match_plan = load_match(evidence_dir)
    if not match_plan:
        print(f"[reference-adapt] No reference-match.json found in {evidence_dir}")
        print("[reference-adapt] Run: python3 universal-frontend-master-source/scripts/reference-match.py")
        return 1

    matched = [e for e in match_plan["elements"] if e.get("status") == "matched"]
    if not matched:
        print("[reference-adapt] No matched elements. Run reference-analyze.py and specify destinations/aspects first.")
        return 1

    # Generate CSS variables
    css_vars = generate_css_variables(match_plan)

    # Generate component code
    components = generate_component_code(match_plan)

    # Write machine-readable adaptation
    adapt_data = {
        "url": match_plan.get("url", ""),
        "adaptedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "totalElements": len(match_plan["elements"]),
        "adaptedElements": len(matched),
        "cssVariables": css_vars,
        "components": match_plan["elements"],
    }

    adapt_file = evidence_dir / "reference-adapt.json"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    adapt_file.write_text(json.dumps(adapt_data, indent=2), encoding="utf-8")

    # Write implementation markdown
    impl_file = ufme_dir / "REFERENCE_IMPLEMENTATION.md"
    if impl_file.exists():
        impl_content = impl_file.read_text(encoding="utf-8")
    else:
        impl_content = "# Reference Implementation\n\n"

    impl_content += f"\n## Reference: {match_plan.get('url', '')}\n"
    impl_content += f"- **Adapted**: {adapt_data['adaptedAt']}\n"
    impl_content += f"- **Elements adapted**: {adapt_data['adaptedElements']}/{adapt_data['totalElements']}\n\n"

    impl_content += "### CSS Variables\n\n"
    impl_content += "```css\n"
    impl_content += css_vars
    impl_content += "```\n\n"

    impl_content += "### Components\n"
    impl_content += components

    impl_file.write_text(impl_content, encoding="utf-8")

    print(f"[reference-adapt] Adapted {adapt_data['adaptedElements']} elements")
    print(f"[reference-adapt] Adaptation data: {adapt_file}")
    print(f"[reference-adapt] Implementation: {impl_file}")
    print()
    print("[reference-adapt] NEXT STEPS:")
    print("  1. Review .ufme/REFERENCE_IMPLEMENTATION.md")
    print("  2. Apply component code to your target project")
    print("  3. Run: python3 universal-frontend-master-source/scripts/reference-verify.py <url>")
    return 0


def main():
    evidence_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else EVIDENCE
    sys.exit(adapt(evidence_dir))


if __name__ == "__main__":
    main()
