#!/usr/bin/env bash
# daily_report.sh — Fetch dashboard data and print a summary
set -euo pipefail

BASE_URL="${DASHBOARD_URL:-http://localhost:5000}"
echo "====================================="
echo " DevOps Dashboard — Daily Report"
echo " $(date)"
echo "====================================="

# Health check
HEALTH=$(curl -sf "${BASE_URL}/health" || echo '{"status":"unreachable"}')
echo "\n[Health] ${HEALTH}"

# Pull JSON data
DATA=$(curl -sf "${BASE_URL}/api/data" || echo '{}')

LOGIN=$(echo "$DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('profile',{}).get('login','N/A'))")
REPOS=$(echo "$DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('profile',{}).get('public_repos','N/A'))")
FOLLOWERS=$(echo "$DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('profile',{}).get('followers','N/A'))")

echo "\n[GitHub Profile]"
echo "  Username  : $LOGIN"
echo "  Repos     : $REPOS"
echo "  Followers : $FOLLOWERS"

echo "\n[Recent Repos]"
echo "$DATA" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for r in data.get('repos', [])[:5]:
    if 'name' in r:
        print(f\"  - {r['name']} [{r.get('language','?')}] ⭐{r.get('stars',0)}\")
"

echo "\n====================================="
echo " Report complete — $(date)"
echo "====================================="
