#!/usr/bin/env bash
# Verify stage (replaces the GitHub Actions "verify" job from Lesson 6.5):
# wait until the live /health reports the commit that was just merged, and print the merge-to-live time.
#
# Usage: APP_URL=https://loan-api-xxx.onrender.com scripts/verify.sh [expected-sha]
#        (default expected SHA: the latest commit on origin/main)
set -euo pipefail
: "${APP_URL:?set APP_URL to your Render address, with no slash at the end}"
git fetch -q origin main
EXPECTED="${1:-$(git rev-parse origin/main)}"
MERGED_AT=$(git log -1 --format=%ct "$EXPECTED")   # commit time of the merge on main
echo "Waiting for $APP_URL to report $EXPECTED (merged $(date -d @"$MERGED_AT" '+%F %T'))"
for attempt in $(seq 1 45); do
  live_sha=$(curl -fsS --max-time 90 "$APP_URL/health" \
    | python3 -c "import sys, json; print(json.load(sys.stdin).get('git_sha', ''))" || true)
  if [ "$live_sha" = "$EXPECTED" ]; then
    now=$(date +%s); secs=$((now - MERGED_AT))
    echo "Deployed and healthy: $live_sha"
    echo "Merge to live: $((secs / 60)) min $((secs % 60)) s"
    exit 0
  fi
  echo "Live version is '${live_sha}', waiting ($attempt/45)"
  sleep 20
done
echo "The new version did not go live in time"
exit 1
