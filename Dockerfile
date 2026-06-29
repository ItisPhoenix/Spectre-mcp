# ╔══════════════════════════════════════════════════════════════╗
# ║  SPECTRE MCP — Dockerfile                                    ║
# ║  Base: Kali Linux Rolling                                    ║
# ║  MCP endpoint → http://localhost:8001/sse                    ║
# ╚══════════════════════════════════════════════════════════════╝

FROM kalilinux/kali-rolling:latest

# ── Build args ────────────────────────────────────────────────────────────────
ARG DEBIAN_FRONTEND=noninteractive
ARG GO_VERSION=1.22.4

# ── Environment ───────────────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    GOPATH=/root/go \
    PATH="/root/go/bin:/opt/mcp-venv/bin:$PATH"

# ── System update + core tools ────────────────────────────────────────────────
RUN apt-get update -qq && apt-get install -y --no-install-recommends \
    # Core utilities
    python3 python3-pip python3-venv python3-dev \
    git curl wget unzip tar build-essential libssl-dev libffi-dev \
    # Network tools
    nmap masscan netcat-openbsd iputils-ping traceroute net-tools iproute2 \
    arp-scan tcpdump dnsutils whois \
    # Web tools
    nikto gobuster ffuf whatweb wafw00f sqlmap wpscan \
    # SSL/TLS
    sslscan testssl.sh \
    # Password tools
    hydra john hashcat crunch hash-identifier \
    # Enumeration
    enum4linux smbclient snmp snmpwalk ldap-utils ftp \
    # Metadata
    exiftool mat2 \
    # Wireless
    aircrack-ng \
    # Exploitation
    metasploit-framework \
    # Post-exploitation / AD
    responder crackmapexec arpspoof \
    # Recon frameworks
    recon-ng amass \
    # Wordlists
    wordlists \
    # Misc
    jq vim less file libpcap-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ── Install Go (for fast Go-based tools) ──────────────────────────────────────
RUN curl -sSL https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz \
    | tar -xzf - -C /usr/local && \
    ln -sf /usr/local/go/bin/go /usr/local/bin/go && \
    ln -sf /usr/local/go/bin/gofmt /usr/local/bin/gofmt
ENV PATH="/usr/local/go/bin:$PATH"

# ── Go-based security tools (pinned to latest stable) ─────────────────────────
RUN go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest && \
    go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest && \
    go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest && \
    go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest && \
    go install -v github.com/projectdiscovery/katana/cmd/katana@latest && \
    go install -v github.com/projectdiscovery/tlsx/cmd/tlsx@latest && \
    go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest && \
    go install -v github.com/tomnomnom/waybackurls@latest && \
    go install -v github.com/lc/gau/v2/cmd/gau@latest && \
    go install -v github.com/tomnomnom/assetfinder@latest && \
    go install -v github.com/hakluke/hakrawler@latest && \
    go install -v github.com/jaeles-project/gospider@latest && \
    cp -r /root/go/bin/* /usr/local/bin/ 2>/dev/null || true

# ── Impacket (network protocol exploitation suite) ───────────────────────────
RUN pip3 install --break-system-packages impacket 2>/dev/null || true

# ── NetExec (CrackMapExec successor) ─────────────────────────────────────────
RUN pip3 install --break-system-packages netexec 2>/dev/null || \
    echo "[WARN] netexec pip install failed — crackmapexec apt fallback available"

# ── theHarvester (latest from GitHub for freshest sources) ───────────────────
RUN git clone --depth=1 https://github.com/laramies/theHarvester.git /opt/theHarvester && \
    pip3 install --break-system-packages -r /opt/theHarvester/requirements/base.txt 2>/dev/null || true && \
    ln -sf /usr/bin/python3 /opt/theHarvester/venv 2>/dev/null || true && \
    ln -sf /opt/theHarvester/theHarvester.py /usr/local/bin/theHarvester 2>/dev/null || true

# ── Metagoofil ────────────────────────────────────────────────────────────────
RUN git clone --depth=1 https://github.com/opsdisk/metagoofil.git /opt/metagoofil && \
    pip3 install --break-system-packages -r /opt/metagoofil/requirements.txt 2>/dev/null || true

# ── SpiderFoot ────────────────────────────────────────────────────────────────
RUN git clone --depth=1 https://github.com/smicallef/spiderfoot.git /opt/spiderfoot && \
    pip3 install --break-system-packages -r /opt/spiderfoot/requirements.txt 2>/dev/null && \
    echo "[INFO] SpiderFoot installed" || \
    echo "[WARN] SpiderFoot requirements partially failed — non-fatal"

# ── Python virtual environment for MCP server ─────────────────────────────────
RUN python3 -m venv /opt/mcp-venv && \
    /opt/mcp-venv/bin/pip install --upgrade pip setuptools wheel

# ── MCP core (pinned stable pair — compatible with Gemini CLI SSE) ────────────
RUN /opt/mcp-venv/bin/pip install \
    "mcp[cli]==1.9.4" \
    "fastmcp==2.3.3" \
    "uvicorn[standard]" \
    "starlette"

# ── OSINT Python packages — CRITICAL (build fails if these fail) ───────────────
RUN /opt/mcp-venv/bin/pip install \
    dnspython \
    shodan \
    requests \
    beautifulsoup4 \
    lxml \
    "scrapling[all]"

# ── OSINT Python packages — OPTIONAL (failures are non-fatal) ─────────────────
RUN /opt/mcp-venv/bin/pip install sherlock-project 2>/dev/null && \
    echo "[OK] sherlock" || echo "[WARN] sherlock failed"

RUN /opt/mcp-venv/bin/pip install holehe 2>/dev/null && \
    echo "[OK] holehe" || echo "[WARN] holehe failed"

RUN /opt/mcp-venv/bin/pip install h8mail 2>/dev/null && \
    echo "[OK] h8mail" || echo "[WARN] h8mail failed"

RUN /opt/mcp-venv/bin/pip install maigret 2>/dev/null && \
    echo "[OK] maigret" || echo "[WARN] maigret failed"

RUN /opt/mcp-venv/bin/pip install socialscan 2>/dev/null && \
    echo "[OK] socialscan" || echo "[WARN] socialscan failed"

RUN /opt/mcp-venv/bin/pip install ghunt 2>/dev/null && \
    echo "[OK] ghunt" || echo "[WARN] ghunt failed"

RUN /opt/mcp-venv/bin/pip install onionsearch 2>/dev/null && \
    echo "[OK] onionsearch" || echo "[WARN] onionsearch failed"

RUN /opt/mcp-venv/bin/pip install instaloader 2>/dev/null && \
    echo "[OK] instaloader" || echo "[WARN] instaloader failed"

# NOTE: twint-fork removed — project abandoned since 2022, breaks consistently.
# Use reddit_user / twitter search via google_dork instead.

# XSStrike — install gracefully; create symlink only if binary exists
RUN /opt/mcp-venv/bin/pip install xsstrike 2>/dev/null && \
    ( ln -sf /opt/mcp-venv/bin/xsstrike /usr/local/bin/xssstrike 2>/dev/null || true ) && \
    echo "[OK] xsstrike" || echo "[WARN] xsstrike failed — tool will report error when called"

# OSRFramework — optional, tools fall back to sherlock/holehe if absent
RUN /opt/mcp-venv/bin/pip install osrframework 2>/dev/null && \
    echo "[OK] osrframework" || echo "[WARN] osrframework failed — sherlock/holehe fallbacks active"

RUN /opt/mcp-venv/bin/pip install phoneinfoga 2>/dev/null && \
    echo "[OK] phoneinfoga" || echo "[WARN] phoneinfoga failed"

# ── Playwright browsers for Scrapling dynamic/stealth modes ──────────────────
RUN /opt/mcp-venv/bin/python3 -m playwright install --with-deps chromium 2>/dev/null && \
    echo "[OK] playwright chromium" || echo "[WARN] playwright install failed"

# ── commix (command injection exploiter) ─────────────────────────────────────
RUN git clone --depth=1 https://github.com/commixproject/commix.git /opt/commix && \
    ln -sf /opt/commix/commix.py /usr/local/bin/commix

# ── PhoneInfoga binary (faster than pip version) ─────────────────────────────
RUN ARCH=amd64 && \
    LATEST=$(curl -sSL https://api.github.com/repos/sundowndev/phoneinfoga/releases/latest \
        | grep tag_name | cut -d'"' -f4) && \
    curl -sSL "https://github.com/sundowndev/phoneinfoga/releases/download/${LATEST}/phoneinfoga_Linux_${ARCH}.tar.gz" \
        | tar -xzf - -C /usr/local/bin/ phoneinfoga 2>/dev/null && \
    chmod +x /usr/local/bin/phoneinfoga && echo "[OK] phoneinfoga binary" || \
    echo "[WARN] phoneinfoga binary download failed — pip version used as fallback"

# ── Copy server file ──────────────────────────────────────────────────────────
RUN mkdir -p /opt/spectre /tmp/spectre
COPY spectre.py /opt/spectre/spectre.py

# ── Copy & register entrypoint ────────────────────────────────────────────────
COPY entrypoint.sh /opt/spectre/entrypoint.sh
RUN chmod +x /opt/spectre/entrypoint.sh

# ── Expose MCP SSE port ───────────────────────────────────────────────────────
EXPOSE 8001

# ── Working directory ─────────────────────────────────────────────────────────
WORKDIR /opt/spectre

ENTRYPOINT ["/opt/spectre/entrypoint.sh"]
