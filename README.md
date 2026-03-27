███████╗██████╗ ███████╗ ██████╗████████╗██████╗ ███████╗
██╔════╝██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔════╝
███████╗██████╔╝█████╗  ██║        ██║   ██████╔╝█████╗
╚════██║██╔═══╝ ██╔══╝  ██║        ██║   ██╔══██╗██╔══╝
███████║██║     ███████╗╚██████╗   ██║   ██║  ██║███████╗
╚══════╝╚═╝     ╚══════╝ ╚═════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝

SPECTRE — Surveillance, Penetration, Exploitation & Cyber Threat Reconnaissance Engine
139 tools · OSINT + Pentest · MCP SSE · Gemini CLI ready

═══════════════════════════════════════════════════════════════
  PREREQUISITES
═══════════════════════════════════════════════════════════════

  ✔ Docker Desktop for Windows  (https://docs.docker.com/desktop/install/windows-install/)
  ✔ Gemini CLI                  (npm install -g @google/gemini-cli)

═══════════════════════════════════════════════════════════════
  FOLDER STRUCTURE
═══════════════════════════════════════════════════════════════

  spectre/
  ├── spectre.py              ← the MCP server (139 tools)
  ├── Dockerfile              ← Kali-based image
  ├── docker-compose.yml      ← one-command launcher
  └── README.md               ← this file

═══════════════════════════════════════════════════════════════
  STEP 1 — BUILD & START THE CONTAINER
═══════════════════════════════════════════════════════════════

  Open a terminal in the spectre/ folder, then run:

    docker compose up -d --build

  First build takes ~10–20 minutes (downloads Kali + all tools).
  Subsequent starts take a few seconds.

  Verify it's running:

    docker ps
    # → spectre-mcp   Up X seconds   0.0.0.0:8001->8001/tcp

  Check the SSE endpoint manually:

    curl http://localhost:8001/sse
    # → should stream an SSE connection (ctrl+c to stop)

═══════════════════════════════════════════════════════════════
  STEP 2 — CONFIGURE GEMINI CLI
═══════════════════════════════════════════════════════════════

  Option A — One-liner (recommended):

    gemini mcp add --transport sse --trust spectre http://localhost:8001/sse

  Option B — Manually edit settings.json:

    File location:
      Windows:   %USERPROFILE%\.gemini\settings.json
      Mac/Linux: ~/.gemini/settings.json

    Add or merge the following block:

    {
      "mcpServers": {
        "spectre": {
          "url": "http://localhost:8001/sse",
          "timeout": 60000,
          "trust": true
        }
      }
    }

    ⚠  If settings.json already has other servers, merge the
       "spectre" block inside the existing "mcpServers" object.
       Do NOT create a second "mcpServers" key.

═══════════════════════════════════════════════════════════════
  STEP 3 — VERIFY IN GEMINI CLI
═══════════════════════════════════════════════════════════════

  Start Gemini CLI:

    gemini

  Inside the CLI session:

    /mcp
    # → SPECTRE should appear with status: Connected
    # → 139 tools listed

  Test a tool:

    Run spectre_status to show all installed tools

═══════════════════════════════════════════════════════════════
  OPTIONAL API KEYS
═══════════════════════════════════════════════════════════════

  Some tools work better (or at all) with API keys.
  Edit docker-compose.yml and uncomment the relevant lines:

    environment:
      SHODAN_API_KEY: "your_key"     # shodan.io
      VT_API_KEY: "your_key"         # virustotal.com
      ABUSEIPDB_KEY: "your_key"      # abuseipdb.com
      ETHERSCAN_KEY: "your_key"      # etherscan.io

  Then restart:

    docker compose up -d

  Without keys, SPECTRE gracefully falls back to free endpoints
  (e.g. Shodan InternetDB).

═══════════════════════════════════════════════════════════════
  COMMON COMMANDS
═══════════════════════════════════════════════════════════════

  Start server:           docker compose up -d
  Stop server:            docker compose down
  View logs:              docker compose logs -f spectre
  Rebuild after changes:  docker compose up -d --build
  Open shell inside:      docker exec -it spectre-mcp bash
  Check health:           docker inspect --format='{{.State.Health.Status}}' spectre-mcp

═══════════════════════════════════════════════════════════════
  TROUBLESHOOTING
═══════════════════════════════════════════════════════════════

  Problem: curl http://localhost:8001/sse returns connection refused
  Fix:     docker compose logs spectre — check for Python import errors
           Make sure port 8001 is not used by another process

  Problem: Gemini CLI shows SPECTRE as "Disconnected"
  Fix:     Confirm the SSE endpoint works: curl http://localhost:8001/sse
           Restart CLI after editing settings.json
           Use /mcp to refresh the connection status

  Problem: nmap scans return permission errors
  Fix:     The container already has NET_RAW capability.
           If still failing: docker exec -it spectre-mcp bash
           then: setcap cap_net_raw+eip $(which nmap)

  Problem: Build fails on Go tools
  Fix:     Individual Go tools failing is non-fatal — the server
           still starts. Check docker compose logs for details.

  Problem: settings.json location on Windows
  Fix:     Run: echo %USERPROFILE%\.gemini\settings.json
           in PowerShell to confirm the path.

═══════════════════════════════════════════════════════════════
  TOOL CATEGORIES (139 total)
═══════════════════════════════════════════════════════════════

  OSINT:
    Identity & People      → sherlock, maigret, holehe, h8mail, socialscan
    Email Intelligence     → email_harvest, email_verify, ghunt, hibp_check
    Social Media           → reddit, github, telegram, linkedin
    Domain & IP            → whois, dns, subfinder, amass, cert_transparency
    Threat Intel           → shodan, censys, virustotal, abuseipdb, threatfox
    Network Ports          → nmap, masscan, naabu, httpx, tlsx
    Web App                → whatweb, wafw00f, nikto, nuclei, gobuster, ffuf, katana
    Web Scraping           → scrapling_fetch, scrapling_extract, scrapling_extract_patterns, scrapling_crawl, scrapling_smart_content, scrapling_session_fetch, scrapling_screenshot, scrapling_bypass_check, scrapling_cli
    Dark Web & Leaks       → onionsearch, paste_search, breach_search, dehashed
    Geo & Physical         → exif_extract, exif_url, gps_to_address, metagoofil
    Dorking                → google_dork, dork_exposed_files, github_dork
    Crypto / Blockchain    → btc_address, eth_address, crypto_tx
    Business Intel         → company_search, sec_filing, linkedin_company
    Exploit Intel          → searchsploit, cve_lookup, exploit_suggest, nuclei_cve_scan
    Frameworks             → spiderfoot, recon_ng_query

  PENTEST:
    Exploitation           → msfconsole, msfvenom
    Password Attacks       → hydra, john, hashcat, crunch, hash_identify
    Network Attacks        → arpspoof, tcpdump, responder, netcat, smbclient
    AD / Windows           → crackmapexec, enum4linux, impacket, mimikatz, smb_enum
    Post Exploitation      → linpeas, linux_enum
    Wireless               → aircrack, airodump

  GOD MODE:
    full_domain_profile    → 10-tool domain sweep
    full_person_profile    → username + email + phone + name OSINT
    full_pentest_recon     → 7-tool pentest recon chain

═══════════════════════════════════════════════════════════════
  LICENSE / USAGE
═══════════════════════════════════════════════════════════════

  For authorised penetration testing and OSINT research only.
  Never run against systems you do not own or have explicit
  written permission to test.
