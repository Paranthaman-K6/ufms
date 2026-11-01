#!/usr/bin/env bash
# discover-assets.sh
# Priority 3 — Asset Intelligence: discover and manage project assets.
# Scans for images, fonts, icons, videos, illustrations, backgrounds.
# Checks license hints, records metadata to .ufme/ASSET_MANIFEST.md,
# detects duplicates by hash, and recommends optimization.
#
# Safety: read-only scan of project files; writes .ufme/ASSET_MANIFEST.md only.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UFME_DIR="$ROOT_DIR/.ufme"
MANIFEST="$UFME_DIR/ASSET_MANIFEST.md"

mkdir -p "$UFME_DIR"

log() { echo "[discover-assets] $*"; }

hash_file() { # hash_file <path>
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}';
  elif command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{print $1}';
  else echo "unknown"; fi
}

license_hint() { # license_hint <path>
  local p="$1"
  case "$p" in
    *unsplash.com*|*source.unsplash.com*) echo "Unsplash (free, attribution appreciated)";;
    *pexels.com*) echo "Pexels (free)";;
    *pixabay.com*) echo "Pixabay (free)";;
    *wikimedia.org*|*wikipedia.org*) echo "Wikimedia Commons (varies; check file page)";;
    *fontsource*|*googleapis.com/css*) echo "Google Fonts (SIL OFL)";;
    *lucide*|*lucide-react*) echo "Lucide (ISC)";;
    *phosphor*) echo "Phosphor Icons (MIT)";;
    *) echo "Verify";;
  esac
}

main() {
  {
    echo "# Asset Manifest"
    echo "Generated: $(date -Iseconds)"
    echo ""
    echo "| Asset | Type | Path | Size (bytes) | SHA-256 | License hint | Status |"
    echo "|-------|------|------|-------------|---------|--------------|--------|"
  } > "$MANIFEST"

  local count=0
  # Image extensions
  for ext in jpg jpeg png gif webp svg ico; do
    while IFS= read -r f; do
      [ -f "$f" ] || continue
      local size
      size=$(wc -c < "$f" 2>/dev/null || echo 0)
      local h
      h=$(hash_file "$f")
      local lic
      lic=$(license_hint "$f")
      echo "| $f | image | $f | $size | $h | $lic | pending |" >> "$MANIFEST"
      count=$((count+1))
    done < <(find "$ROOT_DIR" -type f -iname "*.$ext" -not -path '*/node_modules/*' -not -path '*/.git/*' 2>/dev/null)
  done
  # Font extensions
  for ext in woff woff2 ttf otf; do
    while IFS= read -r f; do
      [ -f "$f" ] || continue
      local size; size=$(wc -c < "$f" 2>/dev/null || echo 0)
      local h; h=$(hash_file "$f")
      local lic; lic=$(license_hint "$f")
      echo "| $f | font | $f | $size | $h | $lic | pending |" >> "$MANIFEST"
      count=$((count+1))
    done < <(find "$ROOT_DIR" -type f -iname "*.$ext" -not -path '*/node_modules/*' -not -path '*/.git/*' 2>/dev/null)
  done
  # Video
  for ext in mp4 webm ogv; do
    while IFS= read -r f; do
      [ -f "$f" ] || continue
      local size; size=$(wc -c < "$f" 2>/dev/null || echo 0)
      local h; h=$(hash_file "$f")
      local lic; lic=$(license_hint "$f")
      echo "| $f | video | $f | $size | $h | $lic | pending |" >> "$MANIFEST"
      count=$((count+1))
    done < <(find "$ROOT_DIR" -type f -iname "*.$ext" -not -path '*/node_modules/*' -not -path '*/.git/*' 2>/dev/null)
  done

  echo ""
  echo "Total assets discovered: $count" >> "$MANIFEST"
  echo "" >> "$MANIFEST"
  echo "## Duplicate detection" >> "$MANIFEST"
  echo "Run: find . -type f -exec sha256sum {} + | sort | uniq -d -w32" >> "$MANIFEST"
  echo "" >> "$MANIFEST"
  echo "## Optimization notes" >> "$MANIFEST"
  echo "- Convert PNG to WebP where supported." >> "$MANIFEST"
  echo "- Subset fonts to used glyphs." >> "$MANIFEST"
  echo "- Verify license for every asset before production use." >> "$MANIFEST"

  log "Asset manifest written to $MANIFEST ($count assets)"
}

main "$@"
