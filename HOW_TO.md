# 📖 SPECTRE — Technical Guide

This document provides detailed instructions for installing, configuring, and troubleshooting the SPECTRE MCP Server across different AI environments.

---

## 🛠️ Prerequisites
Before you begin, ensure you have the following installed:
*   **Docker Desktop:** [Download for Windows](https://docs.docker.com/desktop/install/windows-install/)
*   **A supported AI CLI:** (Claude Code, Gemini CLI, etc.)

---

## 📦 Step 1: Installation & Build

Open your terminal in the project root and run:
```bash
docker compose up -d --build
```
> **Note:** The initial build takes **10–20 minutes** as it pulls the Kali Linux base and installs all 139 security tools. Subsequent starts take only seconds.

---

## ⚙️ Step 2: Configure Your AI Editor

SPECTRE is a standard **MCP SSE (Server-Sent Events)** server. Use the instructions below for your specific tool.

### 🤖 Claude Code (Anthropic)
Run the following command to add SPECTRE to your Claude Code configuration:
```bash
# In your terminal
claude mcp add spectre http://localhost:8001/sse
```
*Alternatively, manually add to `~/.claude/config.json`.*

### ♊ Gemini CLI (Google)
Add the server with the following command:
```bash
gemini mcp add --transport sse --trust spectre http://localhost:8001/sse
```

### 🛠️ Cursor / Windsurf / Cline (IDE Extensions)
While these are often used in IDEs, they use the same MCP configuration. Add a new MCP server with:
- **Type:** `sse`
- **Name:** `spectre`
- **URL:** `http://localhost:8001/sse`

---

## 🧪 Step 3: Verify Tools

Once connected, you can verify the status of the 139 tools by asking your AI:
> "Run the `spectre_status` tool and show me which modules are active."

---

## 🔑 API Key Integration (Optional)
Enhance tool intelligence by adding keys to your `docker-compose.yml`:

```yaml
environment:
  SHODAN_API_KEY: "YOUR_KEY"
  VT_API_KEY: "YOUR_KEY"
  ABUSEIPDB_KEY: "YOUR_KEY"
  ETHERSCAN_KEY: "YOUR_KEY"
```
*Restart with `docker compose up -d` after editing.*

---

## 🔧 Common Management Commands
| Action | Command |
| :--- | :--- |
| **Stop Server** | `docker compose down` |
| **View Logs** | `docker compose logs -f spectre` |
| **Inside Shell** | `docker exec -it spectre-mcp bash` |
| **Force Rebuild** | `docker compose up -d --build` |

---

## ❓ Troubleshooting

*   **Connection Refused:** Ensure port `8001` isn't occupied. Run `docker compose logs spectre` to check for Python startup errors.
*   **Authorization Errors:** In some CLIs, you may need to explicitly "trust" the local SSE endpoint when prompted.
*   **Tool Failures:** Individual tool build failures are usually non-fatal. Use `spectre_status` to see which tools are available.
*   **Pathing:** On Windows, if using PowerShell, ensure you are in the correct directory where `docker-compose.yml` exists.
