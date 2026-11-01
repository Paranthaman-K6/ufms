#!/usr/bin/env bash
# research-libraries.sh
# Design Intelligence: researches candidate frontend libraries from the npm registry
# (name, license, version, homepage, repository) and appends findings to
# .ufme/LIBRARY_REGISTRY.md for the researcher agent to evaluate.
#
# Safety: project-local only; reads public npm registry; never sudo/pacman/systemctl.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REGISTRY="$ROOT_DIR/universal-frontend-master-source/templates/LIBRARY_REGISTRY.md"
OUT_DIR="$ROOT_DIR/.ufme"
REGISTRY_OUT="$OUT_DIR/LIBRARY_REGISTRY.md"

mkdir -p "$OUT_DIR"

log() { echo "[research-libraries] $*"; }

# Default candidate libraries (Priority 2 design intelligence).
LIBS="${*:-tailwindcss @mantine/core motion gsap lucide-react @phosphor-icons/react recharts @radix-ui/react-dialog}"

# Initialize output registry with header only if it doesn't exist.
# The template remains the format reference; examples are not copied to avoid duplicates.
if [ ! -f "$REGISTRY_OUT" ]; then
  {
    echo "# Library Research Registry"
    echo "Records every web library, UI component set, icon set, font, image source, animation"
    echo "library, or template considered for use. Populated by the researcher agent via"
    echo "scripts/research-libraries.sh; approved items are recorded in .ufme/DECISIONS.md."
    echo ""
    echo "| Name | Category | Official repo / site | License | Commercial use | Install method | Reason for selection | Status |"
    echo "|------|----------|---------------------|---------|----------------|----------------|----------------------|--------|"
  } > "$REGISTRY_OUT"
  log "Initialized .ufme/LIBRARY_REGISTRY.md with header"
fi

fetch_lib() { # fetch_lib <npm_package>
  local pkg="$1"
  local url="https://registry.npmjs.org/${pkg}"
  local tmp
  tmp="$(mktemp "$ROOT_DIR/.ufme-lib.XXXXXX.json")"
  curl -sS --max-time 15 "$url" -o "$tmp" 2>/dev/null || {
    log "WARN: could not fetch $pkg from npm registry"
    rm -f "$tmp"
    return 1
  }
  # Parse with node via stdin (registry JSON can be too large for an argument).
  local info
  info="$(node -e "
    let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{
      try{
        const j=JSON.parse(d);
        const name=j.name||'$pkg';
        const lic=(j.license&&typeof j.license==='object')?j.license.type:(j.license||'UNKNOWN');
        const latest=(j['dist-tags']&&j['dist-tags'].latest)||'UNKNOWN';
        const homepage=j.homepage||'';
        const repo=(j.repository&&typeof j.repository==='object')?j.repository.url:'';
        const commercial=(lic==='MIT'||lic==='ISC'||lic==='Apache-2.0'||lic==='BSD-2-Clause'||lic==='BSD-3-Clause'||lic==='0BSD')?'Yes':'Verify';
        console.log(name+'\t'+lic+'\t'+latest+'\t'+homepage+'\t'+repo+'\t'+commercial+'\tnpm install -D $pkg\tOpen-source component/design library candidate');
      }catch(e){process.exit(1);}
    });
  " < "$tmp" 2>/dev/null)" || {
    log "WARN: could not parse registry response for $pkg"
    rm -f "$tmp"
    return 1
  }
  rm -f "$tmp"
  echo "$info"
}

# shadcn/ui is CLI-based, not an npm package; record manually.
if echo "$LIBS" | grep -qw 'shadcn/ui'; then
  echo "| shadcn/ui | UI components | github.com/shadcn/ui | MIT | Yes | npx shadcn-ui add | Accessible, copy-paste, Tailwind + Radix | candidate |" >> "$REGISTRY_OUT"
fi

for pkg in $LIBS; do
  # Skip shadcn/ui (handled above) and non-npm entries.
  [ "$pkg" = "shadcn/ui" ] && continue
  info="$(fetch_lib "$pkg")" || continue
  IFS=$'\t' read -r name license version homepage repo commercial install reason <<< "$info"
  echo "| $name | UI components | $homepage | $license | $commercial | $install | $reason | candidate |" >> "$REGISTRY_OUT"
  log "Researched: $name ($license, $commercial commercial-use)"
done

log "Library research appended to $REGISTRY_OUT"
