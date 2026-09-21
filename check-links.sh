#!/usr/bin/env bash
# Check every external link in index.html and report non-OK responses.
# Usage: ./check-links.sh [file]   (default: index.html)
set -uo pipefail

FILE="${1:-index.html}"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
fail=0

urls=$(grep -o 'href="https\?://[^"]*"' "$FILE" \
  | sed 's/^href="//; s/"$//' \
  | sed 's/&amp;/\&/g' \
  | grep -v '^https://fonts\.\(googleapis\|gstatic\)\.com' \
  | sort -u)

while IFS= read -r url; do
  code=$(curl -sSL --max-time 25 -A "$UA" -o /dev/null -w '%{http_code}' "$url" 2>/dev/null || echo 000)
  case "$code" in
    2*|3*) status="ok  " ;;
    403|405|429|999) status="warn" ;; # bot-blocked (LinkedIn, Elsevier, RG), not necessarily broken
    *)     status="FAIL"; fail=$((fail + 1)) ;;
  esac
  [ "$status" = "ok  " ] || printf '%s %s  %s\n' "$status" "$code" "$url"
done <<< "$urls"

total=$(wc -l <<< "$urls")
echo "---"
echo "checked $total links, $fail failing"
exit $(( fail > 0 ))
