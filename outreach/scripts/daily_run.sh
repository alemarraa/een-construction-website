#!/usr/bin/env bash
# Daily outreach pipeline — intended to run via cron at 09:30 ET Mon-Fri
# Crontab example: 30 14 * * 1-5 /path/to/outreach/scripts/daily_run.sh >> /var/log/een_outreach.log 2>&1
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTREACH_DIR="$(dirname "$SCRIPT_DIR")"
cd "$OUTREACH_DIR"

source .venv/bin/activate

echo "=== $(date -u +"%Y-%m-%d %H:%M UTC") === Daily outreach pipeline starting ==="

een-outreach ingest --county all
een-outreach qualify
een-outreach score
een-outreach enrich --limit 20
een-outreach verify --limit 50
een-outreach compose
een-outreach send --limit 20
een-outreach report --format daily

echo "=== Pipeline complete ==="
