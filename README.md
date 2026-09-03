<div align="center">

```
███████╗██████╗ ███████╗ ██████╗████████╗██████╗ ███████╗
██╔════╝██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔════╝
███████╗██████╔╝█████╗  ██║        ██║   ██████╔╝█████╗
╚════██║██╔═══╝ ██╔══╝  ██║        ██║   ██╔══██╗██╔══╝
███████║██║     ███████╗╚██████╗   ██║   ██║  ██║███████╗
╚══════╝╚═╝     ╚══════╝ ╚═════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝
```

**Surveillance · Penetration · Exploitation · Cyber Threat Reconnaissance Engine**

*The ultimate OSINT + Pentest MCP Server for AI Agents.*

[![Stars](https://img.shields.io/github/stars/ItisPhoenix/Spectre-mcp?style=for-the-badge&color=blue)](https://github.com/ItisPhoenix/Spectre-mcp/stargazers)
[![Forks](https://img.shields.io/github/forks/ItisPhoenix/Spectre-mcp?style=for-the-badge&color=green)](https://github.com/ItisPhoenix/Spectre-mcp/network/members)
[![Issues](https://img.shields.io/github/issues/ItisPhoenix/Spectre-mcp?style=for-the-badge&color=red)](https://github.com/ItisPhoenix/Spectre-mcp/issues)
[![Tools](https://img.shields.io/badge/Tools-140-purple?style=for-the-badge)](https://github.com/ItisPhoenix/Spectre-mcp)
[![Platform](https://img.shields.io/badge/Base-Kali%20Linux-blue?style=for-the-badge&logo=kalilinux)](https://www.kali.org/)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-blue?style=for-the-badge)](https://modelcontextprotocol.io/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://hub.docker.com/)

</div>

---

## What is SPECTRE?

**SPECTRE** transforms your AI agent into a full-spectrum security researcher. It runs a containerised **Kali Linux** environment and exposes every tool inside it to any MCP-compatible AI via **MCP Streamable HTTP**. One command spins it up. One URL connects your agent.


The server exposes **140 industrial-grade security tools** — from passive OSINT through to active exploitation — all wrapped as clean, typed MCP tools that any capable AI can call natively, including Claude Code, Gemini CLI, Cursor, and Windsurf.

> ⚠️ **For authorised penetration testing and research only.** By using this software, you agree to comply with all applicable local and international laws.

---

## Key Capabilities

| Module | What your AI can do |
| :--- | :--- |
| 🔍 **OSINT** | Hunt usernames across 3000+ sites, investigate emails, phone numbers, social profiles |
| 🌐 **Domain & IP Intel** | WHOIS, DNS, subdomain enumeration, cert transparency, Shodan, threat intel |
| 🕸️ **Web Intelligence** | Crawl, fingerprint, scan for CVEs, fuzz directories, bypass WAFs, inspect TLS |
| 🧠 **Web Scraping** | Stealth-fetch JS-heavy pages, extract with CSS/XPath, crawl entire domains |
| 💥 **Exploitation** | Metasploit, searchsploit, CVE lookup, exploit suggestions, reverse shell generation |
| 🔑 **Password Attacks** | Hydra, John, Hashcat, custom wordlist generation, hash identification |
| 🔗 **Network Attacks** | ARP poisoning, NTLM hash capture, packet capture, SMB enumeration |
| 🏴‍☠️ **Post-Exploitation** | LinPEAS, full Linux enumeration, Mimikatz integration |
| 🪙 **Blockchain** | BTC/ETH address intelligence, transaction lookup |
| 👤 **God Mode** | Single-call full domain profile, full person dossier, full pentest recon chain |

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/ItisPhoenix/Spectre-mcp.git
cd Spectre-mcp

# 2. Spin up the engine (initial builds may take 40–60 minutes depending on network, host performance, and package mirrors)
docker compose up -d --build

# 3. Connect your AI
# Claude Code
claude mcp add spectre http://localhost:8001/mcp

# Gemini CLI
gemini mcp add --transport http --trust spectre http://localhost:8001/mcp

# Cursor / Windsurf / Cline → add a Streamable HTTP server at http://localhost:8001/mcp
```

Verify everything is running by asking your AI:
> *"Run `spectre_status` and show me the installed tools."*

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                   AI Agent / CLI                     │
│        (Claude Code, Gemini CLI, Cursor ...)         │
└───────────────────────┬──────────────────────────────┘
                        │  MCP / Streamable HTTP  (port 8001)
┌───────────────────────▼──────────────────────────────┐
│              spectre.py  (FastMCP server)             │
│         mcp==1.24.0  ·  fastmcp==2.3.3               │
└──────┬──────────┬──────────┬──────────────┬──────────┘
       │          │          │              │
  OSINT       Network     Web App      Pentest
  Module      Module      Module       Module
(sherlock,  (nmap,mass- (nuclei,    (msf,hydra,
 maigret,    scan,httpx)  nikto,      john,CME,
 holehe ...)             gobuster)   responder)
       │
  Kali Linux Container  ─  apt pkgs + Go tools + Python venv
```

The server runs entirely inside a Docker container built on `kalilinux/kali-rolling`. The MCP layer is a single Python file (`spectre.py`) using **FastMCP** over Streamable HTTP — meaning any MCP-capable AI can connect to it over HTTP with zero custom integration.

---

## Tool Ecosystem

### 👤 Identity & People OSINT

| Tool | MCP Function | What it does |
| :--- | :--- | :--- |
| Sherlock | `sherlock_username` | Hunt a username across 400+ social networks |
| Maigret | `maigret_username` | Deep username recon across 3000+ sites |
| Holehe | `holehe_email` | Check if an email is registered on 120+ sites |
| H8mail | `h8mail_breach` | Search email/username against breach databases |
| SocialScan | `socialscan_check` | Check username/email availability |
| PhoneInfoga | `phoneinfoga_scan` | Phone number intelligence (carrier, country, type) |
| OSRFramework | `osrf_usufy` `osrf_mailfy` `osrf_searchfy` | Multi-platform username, email, and entity search |

### 📧 Email Intelligence

| Tool | MCP Function | What it does |
| :--- | :--- | :--- |
| theHarvester | `email_harvest` | Harvest all emails for a domain from search engines |
| SMTP Probe | `email_verify` | Verify if an email address is reachable via SMTP |
| GHunt | `ghunt_google` | Deep Google account investigation (maps, photos, calendar) |
| HIBP | `hibp_check` | Check HaveIBeenPwned for breach appearances |

### 📱 Social Media Intelligence (SOCMINT)

| Tool | MCP Function | What it does |
| :--- | :--- | :--- |
| Google Dork | `linkedin_search` `linkedin_company` | Find LinkedIn profiles and companies |
| Reddit API | `reddit_user` `reddit_search` | Investigate users and search communities |
| GitHub API | `github_user` `github_email_leak` `github_dork` `github_secrets` | Full GitHub recon and secret extraction |
| Telegram | `telegram_search` | Search public Telegram channels and groups |

### 🌐 Domain & IP Intelligence

| Tool | MCP Function | What it does |
| :--- | :--- | :--- |
| whois | `whois_lookup` | Domain/IP registration and owner info |
| dig | `dns_lookup` `reverse_dns` | DNS records (A, MX, TXT, ANY …) |
| ipinfo / ip-api | `ip_info` `ip_geolocate` | ASN, org, country, city, ISP |
| ipinfo | `asn_lookup` | All IP ranges owned by an organisation |
| crt.sh | `cert_transparency` | All SSL certs ever issued for a domain |
| Subfinder | `subfinder_enum` | Passive subdomain enumeration via 50+ sources |
| Amass | `amass_enum` | Comprehensive OWASP subdomain enumeration |
| dnsx | `dnsx_resolve` | Fast DNS resolution and subdomain brute force |
| Shodan | `shodan_host` `shodan_search` | Open ports, services, CVEs (falls back to InternetDB) |
| Censys | `censys_query` | Exposed services and certificate search |
| Wayback Machine | `wayback_urls` | All archived URLs for a domain |
| GAU | `gau_urls` | All URLs from Wayback, OTX, Common Crawl, URLScan |
| URLScan.io | `urlscan_lookup` | Past scans, screenshots, and tech stack |
| VirusTotal | `virustotal_domain` `virustotal_ip` | Malware detections and reputation |
| ThreatFox | `threatfox_lookup` | Check IPs/domains/hashes against malware IOCs |
| AbuseIPDB | `abuseipdb_check` | IP abuse reports and reputation score |
| HackerTarget | `reverse_ip` `dns_history` | Reverse IP lookup and past DNS records |

### 🔌 Network & Port Intelligence

| Tool | MCP Function | What it does |
| :--- | :--- | :--- |
| Nmap | `nmap_scan` `nmap_vuln` `nmap_full` `nmap_udp_scan` | Port scan, vuln scripts, full 65535-port scan, UDP |
| Masscan | `masscan_scan` | World's fastest port scanner |
| Naabu | `naabu_scan` | Fast port scan with service discovery |
| Httpx | `httpx_probe` | HTTP/S probing — status, titles, tech stack |
| TLSx | `tlsx_scan` | TLS fingerprinting, cipher suites, JA3 |
| Traceroute | `traceroute_host` | Network path tracing |
| Nmap | `ping_sweep` `arp_scan` | Host discovery on CIDR ranges and local network |

### 🕸️ Web Application Intelligence

| Tool | MCP Function | What it does |
| :--- | :--- | :--- |
| WhatWeb | `whatweb_scan` | CMS, frameworks, server, and analytics fingerprinting |
| WafW00f | `wafw00f_scan` | WAF detection and identification |
| Nikto | `nikto_scan` | Web server vulnerability and misconfiguration scanning |
| Nuclei | `nuclei_scan` `nuclei_cve_scan` | 6000+ templates; CVE-specific scanning |
| Gobuster | `gobuster_dir` | Directory and file brute force |
| FFUF | `ffuf_fuzz` | Web fuzzer for directories, params, and virtual hosts |
| Katana | `katana_crawl` | Next-gen web crawler with JavaScript parsing |
| SSLScan | `sslscan_check` | SSL/TLS ciphers, protocols, certificates |
| testssl.sh | `testssl_run` | Checks BEAST, POODLE, Heartbleed, and more |
| curl | `headers_security` | HTTP security header analysis (CSP, HSTS, X-Frame …) |
| curl | `js_secrets` | Extract hardcoded API keys from JavaScript files |

### 🧠 Web Scraping (Scrapling)

| MCP Function | What it does |
| :--- | :--- |
| `scrapling_fetch` | Fetch a page; modes: `fetcher` (fast), `dynamic` (JS), `stealth` (anti-bot bypass) |
| `scrapling_extract` | Extract elements by CSS or XPath selector |
| `scrapling_extract_patterns` | Extract data matching regex patterns |
| `scrapling_crawl` | Follow links on the same domain up to a specified depth |
| `scrapling_smart_content` | Auto-extract main article/text content without selectors |
| `scrapling_session_fetch` | Fetch with persistent session and custom cookies |
| `scrapling_screenshot` | Screenshot a webpage using StealthyFetcher |
| `scrapling_bypass_check` | Test whether Scrapling can bypass a site's anti-bot measures |

### 🔎 Dorking & Search

| MCP Function | What it does |
| :--- | :--- |
| `google_dork` | Custom Google dork against any target |
| `shodan_dork` | Advanced Shodan search with dork syntax |
| `github_dork` | Search GitHub for exposed credentials and API keys |
| `dork_exposed_files` | Find exposed sensitive files (SQL, env, backups, admin panels) |

### 🪙 Cryptocurrency & Blockchain

| MCP Function | What it does |
| :--- | :--- |
| `btc_address` | Bitcoin balance, transactions, total received/sent |
| `eth_address` | Ethereum balance, token holdings, recent transactions |
| `crypto_tx` | Look up a BTC or ETH transaction by hash |

### 🏢 Company & Business Intelligence

| MCP Function | What it does |
| :--- | :--- |
| `company_search` | OpenCorporates — registration, executives, jurisdiction |
| `linkedin_company` | LinkedIn company page and employee discovery |
| `sec_filing` | SEC EDGAR — 10-K, 10-Q, 8-K filings |
| `mx_finder` | Mail servers and email format for a domain |

### 💥 Exploit & Vulnerability Intelligence

| MCP Function | What it does |
| :--- | :--- |
| `searchsploit_search` | Search Exploit-DB by software name or version |
| `searchsploit_get` | View exploit source by numeric ID |
| `cve_lookup` | CVSS score, description, affected software, PoC links |
| `exploit_suggest` | Exploit suggestions from Exploit-DB and NVD combined |

### 🕵️ OSINT Frameworks

| MCP Function | What it does |
| :--- | :--- |
| `spiderfoot_scan` | SpiderFoot automated OSINT across 200+ data sources |
| `recon_ng_query` | Recon-ng framework with any module |

### 🖥️ Network Service Enumeration

| MCP Function | What it does |
| :--- | :--- |
| `enum4linux_scan` | Windows/Samba — users, shares, groups, password policy |
| `smb_enum` | SMB shares, users, OS version |
| `snmp_enum` | SNMP device info, interfaces, running processes |
| `ldap_enum` | LDAP users, groups, domain info |
| `ftp_enum` | FTP anonymous access, banner, version |
| `ssh_enum` | SSH algorithms, host keys, auth methods |

### 🔑 Password Attacks

| MCP Function | What it does |
| :--- | :--- |
| `hydra_attack` | Brute-force login attack (SSH, HTTP, FTP, SMB …) |
| `john_crack` | Crack password hashes with John the Ripper |
| `hashcat_crack` | GPU-accelerated hash cracking (MD5, NTLM, sha512crypt …) |
| `hash_identify` | Identify the type of an unknown hash |
| `crunch_wordlist` | Generate custom wordlists with any charset and length |

### 💣 Exploitation

| MCP Function | What it does |
| :--- | :--- |
| `msfconsole_run` | Run Metasploit commands non-interactively |
| `msfvenom_generate` | Generate shellcode and payloads |

### 🔗 Network Attacks

| MCP Function | What it does |
| :--- | :--- |
| `arpspoof_run` | ARP poisoning MITM between a target and gateway |
| `responder_run` | Capture NTLM hashes via LLMNR/NBT-NS poisoning |
| `crackmapexec_run` | SMB/WinRM/SSH/LDAP enumeration and credential testing |
| `impacket_run` | Any Impacket script (secretsdump, psexec, GetUserSPNs …) |
| `tcpdump_capture` | Packet capture on any interface |
| `netcat_run` | Port scan, banner grabbing, reverse shells |
| `smbclient_run` | List or access SMB shares |

### 🏴‍☠️ Post-Exploitation

| MCP Function | What it does |
| :--- | :--- |
| `linpeas_run` | Run LinPEAS Linux privilege escalation checker |
| `linux_enum` | Full Linux enum — id, users, SUID, cron, env, history |
| `mimikatz_run` | Mimikatz credential dump (or Metasploit kiwi fallback) |

### 📡 Wireless

| MCP Function | What it does |
| :--- | :--- |
| `aircrack_run` | Crack WEP/WPA from a packet capture file |
| `airodump_run` | Capture wireless packets and list nearby APs |

### 🛠️ Utilities

| MCP Function | What it does |
| :--- | :--- |
| `download_file` | Download any URL into the container filesystem |
| `generate_reverse_shell` | Generate one-liners for bash, python, php, perl, nc, powershell |
| `encode_payload` | Encode a payload as base64, URL, or hex |
| `run_command` | Execute any arbitrary shell command in the container |
| `spectre_status` | Show server config, API key status, and all installed binaries |

---

## ⚡ God Mode — Full Target Profiles

Three high-level tools that chain multiple tools automatically for a single command.

### `full_domain_profile(domain)`
Runs **10 tools in sequence** — WHOIS → DNS → Subdomain Enumeration → Certificate Transparency → IP Geolocation → Open Ports → Web Technology → Email Harvest → Archived URLs → Threat Intelligence.

### `full_person_profile(name, email, username, phone)`
Supply any combination of identifiers. Runs Sherlock, Holehe, H8mail, PhoneInfoga, and social media search as appropriate.

### `full_pentest_recon(target)`
Full pentest recon chain — **Nmap → Httpx → WhatWeb → Nikto → Nuclei → Gobuster → SSLScan** — in one call.

---

## Configuration

All settings are tunable via environment variables in `docker-compose.yml`.

| Variable | Default | Description |
| :--- | :--- | :--- |
| `MCP_HOST` | `127.0.0.1` | Default bind address (Compose overrides this inside the container) |
| `MCP_PORT` | `8001` | Listening port |
| `MCP_TRANSPORT` | `streamable-http` | Default MCP transport; set to `sse` for compatibility |
| `TOOL_TIMEOUT` | `600` | Default timeout (seconds) per tool call |
| `SPECTRE_PYTHON` | `/opt/mcp-venv/bin/python3` | Python interpreter inside the venv |
| `SPECTRE_WORDLIST` | `/usr/share/wordlists/dirb/common.txt` | Default wordlist for fuzzing tools |
| `SHODAN_API_KEY` | *(unset)* | Falls back to InternetDB (free) if unset |
| `VT_API_KEY` | *(unset)* | VirusTotal API key |
| `ABUSEIPDB_KEY` | *(unset)* | AbuseIPDB API key |
| `ETHERSCAN_KEY` | *(unset)* | Etherscan API key for ETH tools |

To set API keys, edit the `environment` section of `docker-compose.yml` and restart:
```bash
docker compose up -d
```

---

## Connecting Your AI

SPECTRE is a standard MCP Streamable HTTP server. The default connection URL is `http://localhost:8001/mcp`.

**Claude Code**
```bash
claude mcp add spectre http://localhost:8001/mcp
```

**Gemini CLI**
```bash
gemini mcp add --transport http --trust spectre http://localhost:8001/mcp
```

**Cursor / Windsurf / Cline**
Configure an HTTP / Streamable HTTP MCP server at `http://localhost:8001/mcp`.

**Manual JSON config** (`~/.claude/config.json` or equivalent)
```json
{
  "mcpServers": {
    "spectre": {
      "type": "http",
      "url": "http://localhost:8001/mcp"
    }
  }
}
```

The bundled example uses `type: "http"`; exact JSON fields vary by client.

---

## Management Commands

| Action | Command |
| :--- | :--- |
| Start (first build) | `docker compose up -d --build` |
| Start (subsequent) | `docker compose up -d` |
| Stop | `docker compose down` |
| View live logs | `docker compose logs -f spectre` |
| Shell into container | `docker exec -it spectre-mcp bash` |
| Force rebuild | `docker compose up -d --build --force-recreate` |

---

## Stack

| Layer | Technology |
| :--- | :--- |
| **Base Image** | `kalilinux/kali-rolling` |
| **MCP Server** | FastMCP 2.3.3 + mcp[cli] 1.24.0 |
| **Transport** | Streamable HTTP on port 8001 |
| **Python Tools** | sherlock, maigret, holehe, h8mail, ghunt, socialscan, scrapling, phoneinfoga, osrframework, shodan, dnspython |
| **Go Tools** | subfinder, httpx, nuclei, naabu, katana, tlsx, dnsx, waybackurls, gau, assetfinder, hakrawler, gospider |
| **Kali Packages** | nmap, masscan, nikto, sqlmap, wpscan, gobuster, ffuf, hydra, john, hashcat, metasploit-framework, aircrack-ng, responder, netexec, impacket, enum4linux, and 100+ more |
| **Storage** | Docker volume `spectre-output` mounted at `/tmp/spectre` |
| **Resources** | 512 MB reserved · 4 GB limit |

---

## Troubleshooting

**Connection refused on port 8001**
Check that the container is running: `docker compose ps`. View startup errors: `docker compose logs spectre`.

**Authorization errors in your AI CLI**
Some CLIs prompt you to explicitly trust local Streamable HTTP endpoints. Accept the prompt or use the `--trust` flag (Gemini CLI).

**A specific tool returns an error or no output**
Some tools may fail to install on certain systems. Run `spectre_status` to see which binaries are available. Tool build failures are non-fatal; everything else keeps working.

**API key errors (VirusTotal, AbuseIPDB, Etherscan)**
These tools require API keys. Set them in `docker-compose.yml` under `environment` and restart the container. Shodan falls back to the free InternetDB endpoint automatically.

**DNS resolution fails during `docker compose build`**
This is a Docker daemon DNS issue, not a runtime issue. Configure DNS in your Docker Desktop settings → Resources → Network → DNS. See the [Docker docs](https://docs.docker.com/desktop/settings/windows/#network).

---

## Disclaimer

SPECTRE is intended for **authorised security research, penetration testing, and educational use only**. The author assumes no liability for misuse. You are solely responsible for ensuring you have written permission before testing any system.

---

<div align="center">

*Built by* **ItisPhoenix** · *Powered by Kali Linux + open-source tools*

</div>
