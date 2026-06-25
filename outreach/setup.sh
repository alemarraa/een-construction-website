#!/usr/bin/env bash
# EEN Construction outreach system setup script
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC}  $*"; }
die()  { echo -e "${RED}✗${NC} $*" >&2; exit 1; }

echo "═══════════════════════════════════════"
echo "  EEN Construction — Outreach Setup"
echo "═══════════════════════════════════════"
echo

# Python version check
PY_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
if [[ "$PY_MAJOR" -lt 3 || ("$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 12) ]]; then
  die "Python 3.12+ required (found $PY_VERSION)"
fi
ok "Python $PY_VERSION"

# Virtual environment
if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
  ok "Created virtual environment"
fi
# shellcheck source=/dev/null
source .venv/bin/activate
ok "Activated virtual environment"

# Install dependencies
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet -e .
ok "Dependencies installed"

# .env file
if [[ ! -f ".env" ]]; then
  cp .env.example .env
  warn ".env created from .env.example — fill in your credentials before running"
else
  ok ".env already exists"
fi

# Database directory
mkdir -p data
ok "data/ directory ready"

# Run initial migration
python -m alembic upgrade head
ok "Database migrations applied"

# Run tests
echo
echo "Running tests…"
python -m pytest tests/ -q --tb=short
ok "Tests passed"

echo
echo "═══════════════════════════════════════"
ok "Setup complete!"
echo
echo "Next steps:"
echo "  1. Edit .env and fill in your credentials (SENDER_NAME, BUSINESS_EMAIL, etc.)"
echo "  2. Activate venv: source .venv/bin/activate"
echo "  3. Run discovery: een-outreach ingest --county montgomery"
echo "  4. Qualify:       een-outreach qualify"
echo "  5. Score:         een-outreach score"
echo "  6. Compose:       een-outreach compose"
echo "  7. Preview:       een-outreach report"
echo "  8. When ready:    set DRY_RUN=false SEND_ENABLED=true in .env"
echo "  9. Send:          een-outreach send --limit 5"
echo
echo "Keep DRY_RUN=true and SEND_ENABLED=false until you have verified"
echo "sender identity and reviewed all compliance checklist items:"
echo "  een-outreach compliance"
