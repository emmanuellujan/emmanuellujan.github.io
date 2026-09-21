#!/usr/bin/env bash
# Compare the MIT mirror against the live site, page by page.
#
# The mirror is a second copy, so it can silently fall behind. Run this after
# any site change (or whenever you wonder) to see whether MIT is stale.
#
# Usage:  tools/check_mit_sync.sh
set -uo pipefail

LIVE="https://www.emmanuellujan.com"
MIT="https://www.mit.edu/~eljn"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Compare rendered bytes, ignoring the canonical/og URLs which legitimately
# differ in neither copy (both point at the live domain) — so a plain hash works.
# Deliberately does NOT follow redirects. If MIT ever redirects again, -L
# would quietly fetch the live site and every page would look "in sync".
hash_of() {
  curl -s --max-time 25 -A "$UA" "$1" 2>/dev/null | sha256sum | cut -c1-16
}
status_of() {
  curl -sI --max-time 20 -A "$UA" "$1" 2>/dev/null | head -1 | grep -oE '[0-9]{3}'
}

paths=("/")
while IFS= read -r d; do
  paths+=("/papers/$(basename "$d")/")
done < <(find "$REPO/papers" -maxdepth 1 -mindepth 1 -type d | sort)

stale=0; missing=0; ok=0
printf '%-46s %-18s %-18s %s\n' PAGE LIVE MIT STATUS
for p in "${paths[@]}"; do
  a=$(hash_of "$LIVE$p")
  code=$(status_of "$MIT$p")
  b=$(hash_of "$MIT$p")
  if [ "$code" = "301" ] || [ "$code" = "302" ]; then
    status="REDIRECTING"; missing=$((missing+1))
  elif [ -z "$b" ] || [ "$b" = "$(printf '' | sha256sum | cut -c1-16)" ] || [ "$code" != "200" ]; then
    status="MISSING"; missing=$((missing+1))
  elif [ "$a" = "$b" ]; then
    status="ok"; ok=$((ok+1))
  else
    status="STALE"; stale=$((stale+1))
  fi
  [ "$status" = "ok" ] || printf '%-46s %-18s %-18s %s\n' "$p" "$a" "$b" "$status"
done

echo
echo "in sync: $ok   stale: $stale   missing: $missing"
if [ $((stale + missing)) -gt 0 ]; then
  echo "run:  tools/deploy_mit.sh --push"
  exit 1
fi
