#!/usr/bin/env bash
# ============================================================
#  RAPP Hatch Project — Create a CommunityRAPP instance for a customer
#
#  Usage:
#    curl -fsSL https://raw.githubusercontent.com/kody-w/m365-agents-for-python/main/CommunityRAPP/hatch-project.sh | bash -s -- my-project
#
#  Or with a custom directory:
#    RAPP_PROJECTS_DIR=~/clients ./hatch-project.sh my-project
# ============================================================
set -e

PROJECT_NAME="${1:-}"
PROJECTS_DIR="${RAPP_PROJECTS_DIR:-$HOME/rapp-projects}"
REPO_URL="https://github.com/kody-w/m365-agents-for-python.git"
BASE_PORT=7072

# ── Helpers ─────────────────────────────────────────────────

die()  { echo "ERROR: $1" >&2; exit 1; }
info() { echo "==> $1"; }

find_python() {
    for cmd in python3.11 python3.12 python3; do
        if command -v "$cmd" &>/dev/null; then
            local ver
            ver=$("$cmd" --version 2>&1 | awk '{print $2}')
            local major minor
            major=$(echo "$ver" | cut -d. -f1)
            minor=$(echo "$ver" | cut -d. -f2)
            if [ "$major" = "3" ] && [ "$minor" -ge 11 ]; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    return 1
}

next_port() {
    local port=$BASE_PORT
    if [ -f "$PROJECTS_DIR/.hatchery.json" ]; then
        # Find highest port in use
        local max
        max=$(grep -o '"port": [0-9]*' "$PROJECTS_DIR/.hatchery.json" 2>/dev/null | awk '{print $2}' | sort -n | tail -1)
        if [ -n "$max" ] && [ "$max" -ge "$port" ]; then
            port=$((max + 1))
        fi
    fi
    echo "$port"
}

# ── Prompt for name if not provided ─────────────────────────

if [ -z "$PROJECT_NAME" ]; then
    echo ""
    echo "=== RAPP Hatch Project ==="
    echo ""
    echo "Create a CommunityRAPP instance for a customer."
    echo ""
    printf "Project name (e.g. contoso-bot): "
    read -r PROJECT_NAME
    [ -z "$PROJECT_NAME" ] && die "Project name is required."
fi

# ── Validate ────────────────────────────────────────────────

if ! echo "$PROJECT_NAME" | grep -qE '^[a-z0-9][a-z0-9-]*$'; then
    die "Invalid name '$PROJECT_NAME'. Use lowercase letters, numbers, and hyphens."
fi

PROJECT_DIR="$PROJECTS_DIR/$PROJECT_NAME"
[ -d "$PROJECT_DIR" ] && die "Project '$PROJECT_NAME' already exists at $PROJECT_DIR"

# ── Prerequisites ───────────────────────────────────────────

command -v git &>/dev/null || die "Git is required. Install from https://git-scm.com"

PYTHON_CMD=$(find_python) || die "Python 3.11+ required (3.13+ not recommended). Install from https://python.org"
info "Using $PYTHON_CMD ($($PYTHON_CMD --version 2>&1))"

# ── Clone ───────────────────────────────────────────────────

echo ""
echo "=== Hatching '$PROJECT_NAME' ==="
echo ""

mkdir -p "$PROJECTS_DIR"
TMP_DIR="$PROJECTS_DIR/.tmp-$PROJECT_NAME-$$"

info "Cloning CommunityRAPP..."
git clone --depth 1 --quiet "$REPO_URL" "$TMP_DIR"
mv "$TMP_DIR/CommunityRAPP" "$PROJECT_DIR"
rm -rf "$TMP_DIR"

# ── Venv + deps ─────────────────────────────────────────────

info "Creating virtual environment..."
"$PYTHON_CMD" -m venv "$PROJECT_DIR/.venv"

info "Installing dependencies..."
"$PROJECT_DIR/.venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt" --quiet 2>/dev/null

# ── Settings ────────────────────────────────────────────────

if [ -f "$PROJECT_DIR/local.settings.template.json" ]; then
    cp "$PROJECT_DIR/local.settings.template.json" "$PROJECT_DIR/local.settings.json"
    info "Copied settings template → local.settings.json"
fi

# ── Port + start scripts ───────────────────────────────────

PORT=$(next_port)

cat > "$PROJECT_DIR/start.sh" << EOF
#!/usr/bin/env bash
# Start CommunityRAPP on port $PORT
cd "\$(dirname "\$0")"
source .venv/bin/activate
func start --port $PORT
EOF
chmod +x "$PROJECT_DIR/start.sh"

cat > "$PROJECT_DIR/start.ps1" << EOF
# Start CommunityRAPP on port $PORT
\$ErrorActionPreference = 'Stop'
Set-Location \$PSScriptRoot
.venv\\Scripts\\Activate.ps1
func start --port $PORT
EOF

# ── Business Mode UI (first hatch deploys it) ────────────────

BIZ_HTML="$PROJECTS_DIR/business.html"
if [ ! -f "$BIZ_HTML" ]; then
    info "Deploying Business Mode UI..."
    BIZ_URL="https://raw.githubusercontent.com/kody-w/m365-agents-for-python/main/CommunityRAPP/business.html"
    curl -fsSL "$BIZ_URL" -o "$BIZ_HTML" 2>/dev/null || true
fi

# ── Update manifest ─────────────────────────────────────────

MANIFEST="$PROJECTS_DIR/.hatchery.json"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

if [ -f "$MANIFEST" ]; then
    # Append to existing manifest using python (available since we just used it)
    "$PYTHON_CMD" -c "
import json, sys
with open('$MANIFEST', 'r') as f:
    data = json.load(f)
data.setdefault('projects', {})['$PROJECT_NAME'] = {
    'path': '$PROJECT_DIR',
    'port': $PORT,
    'created_at': '$TIMESTAMP',
    'python': '$PYTHON_CMD'
}
with open('$MANIFEST', 'w') as f:
    json.dump(data, f, indent=2)
"
else
    cat > "$MANIFEST" << EOF
{
  "projects": {
    "$PROJECT_NAME": {
      "path": "$PROJECT_DIR",
      "port": $PORT,
      "created_at": "$TIMESTAMP",
      "python": "$PYTHON_CMD"
    }
  }
}
EOF
fi

# ── Done ────────────────────────────────────────────────────

echo ""
echo "=== Project '$PROJECT_NAME' hatched ==="
echo ""
echo "  Location:  $PROJECT_DIR"
echo "  Port:      $PORT"
echo "  Python:    $PYTHON_CMD"
echo ""
echo "Next steps:"
echo ""
echo "  1. Start locally:"
echo "     cd $PROJECT_DIR && ./start.sh"
echo ""
echo "  2. Verify:"
echo "     curl http://localhost:$PORT/api/health"
echo ""
echo "  Everything runs on your machine with local file storage."
echo "  No Azure account or API keys needed to get started."
echo ""
if [ -f "$BIZ_HTML" ]; then
echo "  3. Business Mode (chat with brainstem + projects side by side):"
echo "     open $BIZ_HTML"
echo ""
fi
echo "  When you're ready to add AI responses:"
echo "     Edit $PROJECT_DIR/local.settings.json"
echo "     Add your Azure OpenAI endpoint, deployment name, and API key"
echo ""
echo "  When you're ready to deploy to the cloud:"
echo "     See the deployment guide in $PROJECT_DIR/docs/"
echo ""
