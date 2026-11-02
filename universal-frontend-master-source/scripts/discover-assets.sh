#!/usr/bin/env bash
# discover-assets.sh
# Priority 3 — Asset Intelligence: discover and manage project assets.
# Scans for images, fonts, icons, videos, illustrations, backgrounds.
# Records metadata to .ufme/ASSET_MANIFEST.md with:
#   - Hash-based duplicate detection
#   - File-size reporting
#   - Image dimension extraction (where tools available)
#   - Aspect-ratio information
#   - Broken asset detection
#   - Asset attribution records
#   - Status distinction (locally discovered / candidate / downloaded / verified / approved)
#
# Safety: read-only scan of project files; writes .ufme/ASSET_MANIFEST.md only.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UFME_DIR="$ROOT_DIR/.ufme"
MANIFEST="$UFME_DIR/ASSET_MANIFEST.md"

mkdir -p "$UFME_DIR"

log() { echo "[discover-assets] $*"; }

hash_file() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}';
  elif command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{print $1}';
  else echo "unknown"; fi
}

get_image_dimensions() {
  # Try identify (ImageMagick) first, then file output parsing.
  if command -v identify >/dev/null 2>&1; then
    identify -format "%wx%h" "$1" 2>/dev/null || echo "unknown"
  elif command -v file >/dev/null 2>&1; then
    file "$1" 2>/dev/null | grep -oE '[0-9]+ x [0-9]+' | head -1 | tr -d ' ' | tr 'x' 'x' || echo "unknown"
  else
    echo "unknown"
  fi
}

aspect_ratio() {
  local dims="$1"
  [ "$dims" = "unknown" ] && { echo "unknown"; return; }
  local w h
  w="${dims%x*}"
  h="${dims#*x}"
  [ "$h" = "0" ] && { echo "unknown"; return; }
  echo "scale=2; $w / $h" | bc 2>/dev/null || echo "unknown"
}

license_hint() {
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

# Detect if an image file is broken/corrupt.
is_broken_image() {
  local f="$1"
  case "$f" in
    *.svg)
      # Basic SVG well-formedness check
      grep -q '<svg' "$f" 2>/dev/null && grep -q '</svg>' "$f" 2>/dev/null || return 0
      return 1
      ;;
    *)
      if command -v identify >/dev/null 2>&1; then
        identify -ping "$f" >/dev/null 2>&1 || return 0
        return 1
      else
        return 1
      fi
      ;;
  esac
}

main() {
  local tmp_dupes
  tmp_dupes="$(mktemp "$UFME_DIR/.asset-dupes.XXXXXX")"

  # First pass: collect all files and hashes for duplicate detection.
  declare -A hash_seen
  declare -A hash_files

  {
    echo "# Asset Manifest"
    echo "Generated: $(date -Iseconds)"
    echo ""
    echo "| Asset | Type | Path | Size (bytes) | SHA-256 | Dimensions | Aspect Ratio | License hint | Status |"
    echo "|-------|------|------|-------------|---------|------------|--------------|--------------|--------|"
  } > "$MANIFEST"

  local count=0
  local dupe_count=0
  local broken_count=0

  # Collect all asset files first
  local all_assets=()
  for ext in jpg jpeg png gif webp svg ico woff woff2 ttf otf mp4 webm ogv; do
    while IFS= read -r f; do
      [ -f "$f" ] || continue
      all_assets+=("$f")
    done < <(find "$ROOT_DIR" -type f -iname "*.$ext" -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.ufme/evidence/*' 2>/dev/null)
  done

  # Compute hashes and detect duplicates
  for f in "${all_assets[@]}"; do
    local h
    h=$(hash_file "$f")
    if [ -n "${hash_seen[$h]:-}" ]; then
      hash_files["$h"]="${hash_files[$h]} $f"
    else
      hash_seen["$h"]=1
      hash_files["$h"]="$f"
    fi
  done

  # Identify duplicate hashes
  for h in "${!hash_seen[@]}"; do
    local file_list
    file_list="${hash_files[$h]}"
    local file_count
    file_count=$(echo "$file_list" | wc -w)
    if [ "$file_count" -gt 1 ]; then
      echo "$h" >> "$tmp_dupes"
      dupe_count=$((dupe_count + 1))
    fi
  done

  # Build duplicate lookup
  declare -A is_duplicate
  if [ -f "$tmp_dupes" ]; then
    while IFS= read -r dh; do
      is_duplicate["$dh"]=1
    done < "$tmp_dupes"
  fi

  # Second pass: write manifest entries
  for f in "${all_assets[@]}"; do
    local size h dims ar lic status broken
    size=$(wc -c < "$f" 2>/dev/null || echo 0)
    h=$(hash_file "$f")
    dims="unknown"
    ar="unknown"

    # Determine type
    local ext="${f##*.}"
    ext=$(echo "$ext" | tr '[:upper:]' '[:lower:]')
    local ftype
    case "$ext" in
      jpg|jpeg|png|gif|webp|svg|ico) ftype="image";;
      woff|woff2|ttf|otf) ftype="font";;
      mp4|webm|ogv) ftype="video";;
      *) ftype="other";;
    esac

    # Image dimensions and aspect ratio
    if [ "$ftype" = "image" ]; then
      dims=$(get_image_dimensions "$f")
      ar=$(aspect_ratio "$dims")
    fi

    # License hint
    lic=$(license_hint "$f")

    # Broken asset detection
    broken=0
    if [ "$ftype" = "image" ]; then
      if is_broken_image "$f"; then
        broken=1
        broken_count=$((broken_count + 1))
      fi
    fi

    # Duplicate detection
    if [ "${is_duplicate[$h]:-}" = "1" ]; then
      status="duplicate"
    elif [ "$broken" -eq 1 ]; then
      status="broken"
    else
      status="locally discovered"
    fi

    echo "| $f | $ftype | $f | $size | $h | $dims | $ar | $lic | $status |" >> "$MANIFEST"
    count=$((count+1))
  done

  echo ""
  echo "Total assets discovered: $count" >> "$MANIFEST"
  echo "Duplicate groups detected: $dupe_count" >> "$MANIFEST"
  echo "Broken assets detected: $broken_count" >> "$MANIFEST"
  echo "" >> "$MANIFEST"
  echo "## Status definitions" >> "$MANIFEST"
  echo "| Status | Meaning |" >> "$MANIFEST"
  echo "|--------|---------|" >> "$MANIFEST"
  echo "| locally discovered | Asset found in project; license not yet verified |" >> "$MANIFEST"
  echo "| duplicate | Same hash as another asset; consider removing |" >> "$MANIFEST"
  echo "| broken | Image file appears corrupt or malformed |" >> "$MANIFEST"
  echo "| remotely discovered candidate | Found via external provider; not downloaded |" >> "$MANIFEST"
  echo "| downloaded | Asset downloaded to project; license not verified |" >> "$MANIFEST"
  echo "| license verified | License confirmed for intended use |" >> "$MANIFEST"
  echo "| approved for production use | Approved by orchestrator for production |" >> "$MANIFEST"
  echo "" >> "$MANIFEST"
  echo "## Optimization notes" >> "$MANIFEST"
  echo "- Convert PNG to WebP where supported." >> "$MANIFEST"
  echo "- Subset fonts to used glyphs." >> "$MANIFEST"
  echo "- Verify license for every asset before production use." >> "$MANIFEST"
  echo "- Remove duplicate assets to reduce bundle size." >> "$MANIFEST"

  rm -f "$tmp_dupes"

  log "Asset manifest written to $MANIFEST ($count assets, $dupe_count duplicate groups, $broken_count broken)"
}

main "$@"
