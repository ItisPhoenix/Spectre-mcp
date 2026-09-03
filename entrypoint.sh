#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  SPECTRE MCP — Container Entrypoint                          ║
# ╚══════════════════════════════════════════════════════════════╝
set -euo pipefail

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   SPECTRE — starting up                                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# ── Ensure output volume directory exists ────────────────────────
mkdir -p /tmp/spectre

# ── Update Nuclei templates in the background ────────────────────
# Do NOT do this at build time — templates change daily.
echo "[*] Updating Nuclei templates (background)..."
nuclei -update-templates -silent &>/dev/null &

# ── Update Nuclei binary itself if a newer version is available ──
nuclei -update -silent &>/dev/null &

# ── Update subfinder sources ─────────────────────────────────────
subfinder -update -silent &>/dev/null &

# ── Initialise Shodan CLI if key is set ──────────────────────────
if [ -n "${SHODAN_API_KEY:-}" ]; then
    echo "[*] Configuring Shodan CLI..."
    shodan init "${SHODAN_API_KEY}" &>/dev/null || true
fi

echo "[*] Starting SPECTRE MCP server..."
echo "    Transport : ${MCP_TRANSPORT:-sse}"
echo "    Address   : ${MCP_HOST:-127.0.0.1}:${MCP_PORT:-8001}"
if [ -n "${SPECTRE_API_KEY:-}" ]; then
    echo "    Auth      : ENABLED"
else
    echo "    Auth      : DISABLED (open)"
fi
echo ""

exec /opt/mcp-venv/bin/python3 /opt/spectre/spectre.py
