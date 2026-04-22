#!/usr/bin/env bash
# ============================================================
#  RAPP Hatchery — Install the hatchery agent into your brainstem
#  Usage: curl -fsSL https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/hatch.sh | bash
# ============================================================
set -e

AGENT_URL="https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/hatchery/rapp_hatchery_agent.py"
AGENT_FILE="rapp_hatchery_agent.py"

echo "=== RAPP Hatchery ==="
echo ""

# ── Detect brainstem agents/ directory ──────────────────────

AGENTS_DIR=""

# 1. Environment variable
if [ -n "$RAPP_BRAINSTEM_DIR" ] && [ -d "$RAPP_BRAINSTEM_DIR/agents" ]; then
    AGENTS_DIR="$RAPP_BRAINSTEM_DIR/agents"

# 2. Current directory has soul.md (we're inside the brainstem)
elif [ -f "soul.md" ] && [ -d "agents" ]; then
    AGENTS_DIR="$(pwd)/agents"

# 3. Parent rapp_brainstem directory (running from repo root)
elif [ -f "rapp_brainstem/soul.md" ] && [ -d "rapp_brainstem/agents" ]; then
    AGENTS_DIR="$(pwd)/rapp_brainstem/agents"

# 4. Default install location
elif [ -d "$HOME/rapp-installer/rapp_brainstem/agents" ]; then
    AGENTS_DIR="$HOME/rapp-installer/rapp_brainstem/agents"
fi

if [ -z "$AGENTS_DIR" ]; then
    echo "Could not find your brainstem's agents/ directory."
    echo ""
    echo "Try one of:"
    echo "  1. Run this from inside your brainstem directory"
    echo "  2. Set RAPP_BRAINSTEM_DIR=/path/to/rapp_brainstem"
    echo "  3. Install the brainstem first: https://github.com/kody-w/rapp-installer"
    exit 1
fi

echo "Brainstem agents directory: $AGENTS_DIR"

# ── Download the hatchery agent ────────────────────────────

echo "Downloading hatchery agent..."
curl -fsSL "$AGENT_URL" -o "$AGENTS_DIR/$AGENT_FILE"

echo ""
echo "Hatchery agent installed to $AGENTS_DIR/$AGENT_FILE"
echo ""
echo "Next steps:"
echo "  1. Restart your brainstem (or wait for the agent cache to refresh)"
echo "  2. Tell your brainstem: 'Hatch a project called my-project'"
echo ""
echo "=== Done ==="
