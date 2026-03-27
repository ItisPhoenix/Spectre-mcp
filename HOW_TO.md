# 📖 SPECTRE — Technical Guide

This document provides detailed instructions for installing, configuring, and troubleshooting the SPECTRE MCP Server.

---

## 🛠️ Prerequisites
Before you begin, ensure you have the following installed:
*   **Docker Desktop:** [Download for Windows](https://docs.docker.com/desktop/install/windows-install/)
*   **Gemini CLI:** `npm install -g @google/gemini-cli`

---

## 📦 Step 1: Installation & Build

Open your terminal in the project root and run:
```bash
docker compose up -d --build
```
> **Note:** The initial build takes **10–20 minutes** as it pulls the Kali Linux base and installs all 139 security tools. Subsequent starts take only seconds.

### Verify the Server is Running
1.  **Check Docker Status:**
    ```bash
    docker ps
    # Should show spectre-mcp running on port 8001
    ```
2.  **Test SSE Endpoint:**
    ```bash
    curl http://localhost:8001/sse
    # Should return a stream of events
    ```

---

## ⚙️ Step 2: Gemini CLI Configuration

### Option A: Automatic (Recommended)
Run the following command to add SPECTRE to your Gemini CLI automatically:
```bash
gemini mcp add --transport sse --trust spectre http://localhost:8001/sse
```

### Option B: Manual Setup
Manually edit your `settings.json` file:
*   **Windows:** `%USERPROFILE%\.gemini\settings.json`
*   **Mac/Linux:** `~/.gemini/settings.json`

Add the following block to the `mcpServers` object:
```json
{
  "mcpServers": {
    "spectre": {
      "url": "http://localhost:8001/sse",
      "timeout": 60000,
      "trust": true
    }
  }
}
```

---

## 🧪 Step 3: Tool Verification

Launch Gemini CLI:
```bash
gemini
```
Inside the CLI, use `/mcp` to list active servers. You should see **SPECTRE** listed as **Connected**.

**Try running:** `spectre_status` to see the status of all internal tool sub-modules.

---

## 🔑 API Key Integration
Some tools (like Shodan or VirusTotal) perform better with API keys. Edit the `docker-compose.yml` file to include your keys:

```yaml
environment:
  SHODAN_API_KEY: "YOUR_KEY"
  VT_API_KEY: "YOUR_KEY"
  ABUSEIPDB_KEY: "YOUR_KEY"
  ETHERSCAN_KEY: "YOUR_KEY"
```
*Restart with `docker compose up -d` after editing.*

---

## 🔧 Common Commands
| Action | Command |
| :--- | :--- |
| **Stop Server** | `docker compose down` |
| **View Logs** | `docker compose logs -f spectre` |
| **Inside Shell** | `docker exec -it spectre-mcp bash` |
| **Check Health** | `docker inspect --format='{{.State.Health.Status}}' spectre-mcp` |

---

## ❓ Troubleshooting

*   **Connection Refused:** Ensure port `8001` isn't occupied. Run `docker compose logs spectre` to check for Python startup errors.
*   **Gemini CLI Disconnected:** Restart the Gemini CLI after adding the server. Verify your internet connection can reach `localhost:8001`.
*   **Nmap Permission Denied:** While the container is configured for raw sockets, if issues persist, run:
    `docker exec -it spectre-mcp bash` -> `setcap cap_net_raw+eip $(which nmap)`
*   **Build Failures:** Individual tool build failures (Go/Python) are often non-fatal. Check logs to see if the main server still initialized.

---

## 🛠️ Tool Categories Detail

### OSINT
*   **Identity:** `sherlock`, `maigret`, `holehe`, `h8mail`, `socialscan`
*   **Email:** `email_harvest`, `email_verify`, `ghunt`, `hibp_check`
*   **Domains:** `whois`, `dns`, `subfinder`, `amass`, `cert_transparency`
*   **Threat Intel:** `shodan`, `censys`, `virustotal`, `abuseipdb`
*   **Scraping:** `scrapling` full suite (fetch, crawl, patterns, screenshot)

### Pentest
*   **Exploitation:** `msfconsole`, `msfvenom`
*   **Passwords:** `hydra`, `john`, `hashcat`, `crunch`
*   **Network:** `arpspoof`, `tcpdump`, `responder`, `netcat`
*   **Post-Exploit:** `linpeas`, `linux_enum`
*   **Windows/AD:** `crackmapexec`, `enum4linux`, `impacket`, `mimikatz`
