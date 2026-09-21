#!/usr/bin/env bash
# Mirror the site into the MIT Athena locker, so www.mit.edu/~eljn keeps its
# own URL and serves the pages directly instead of redirecting away.
#
# Safe to re-run. Every page carries <link rel="canonical"> pointing at
# www.emmanuellujan.com, so search engines consolidate there and the mirror
# is not treated as duplicate content.
#
# Usage:  tools/deploy_mit.sh            # stage and show what would be sent
#         tools/deploy_mit.sh --push     # stage, then scp to Athena
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAGE="${TMPDIR:-/tmp}/eljn-mit-site.$$"
# Set MIT_REMOTE to your own Athena target, e.g.
#   export MIT_REMOTE=username@athena.dialup.mit.edu:~/www/
# With an ssh ControlMaster entry (see README) an alias works too:
#   export MIT_REMOTE=athena:~/www/
REMOTE="${MIT_REMOTE:-USER@athena.dialup.mit.edu:~/www/}"

cleanup() { rm -rf "$STAGE"; }
trap cleanup EXIT

mkdir -p "$STAGE"
cp "$REPO/index.html" "$REPO/eljn.png" "$STAGE/"
cp -r "$REPO/papers" "$STAGE/"
find "$STAGE" -name '.*' -delete 2>/dev/null || true

echo "staged $(du -sh "$STAGE" | cut -f1) — $(find "$STAGE/papers" -name index.html | wc -l) paper pages"

# sitemap.xml and robots.txt are intentionally excluded: the sitemap lists
# emmanuellujan.com URLs, and robots.txt is only honoured at a domain root.

if [ "${1:-}" = "--push" ]; then
  case "$REMOTE" in
    USER@*) echo "error: set MIT_REMOTE first, e.g."; \
            echo "  export MIT_REMOTE=username@athena.dialup.mit.edu:~/www/"; exit 1 ;;
  esac
  host="${REMOTE%%:*}"
  if ssh -O check "$host" 2>/dev/null; then
    echo "reusing the open ssh session — no Duo prompt"
  else
    echo "no open session; Duo will prompt once, then stay open for 8h"
  fi
  scp -r "$STAGE"/. "$REMOTE"
  echo "done — check https://www.mit.edu/~eljn/"
else
  echo
  echo "dry run. to upload:  tools/deploy_mit.sh --push"
fi
