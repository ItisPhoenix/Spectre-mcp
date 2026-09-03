# ╔══════════════════════════════════════════════════════════════╗
# ║  SPECTRE MCP — Dockerfile                                    ║
# ║  Base: Kali Linux Rolling                                    ║
# ║  MCP endpoint → http://localhost:8001/mcp                    ║
# ╚══════════════════════════════════════════════════════════════╝

FROM kalilinux/kali-rolling:latest

# ── Build args ────────────────────────────────────────────────────────────────
ARG DEBIAN_FRONTEND=noninteractive
ARG GO_VERSION=1.24.3

# ── Environment ───────────────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    GOPATH=/root/go \
    PATH="/root/go/bin:/opt/mcp-venv/bin:$PATH"

# ── System update + core tools (strict — build fails if anything missing) ──
RUN set -eux; \
    sed -i 's|http://mirrors.esto.network|http://http.kali.org|g' /etc/apt/sources.list /etc/apt/sources.list.d/* 2>/dev/null || true; \
    echo 'Acquire::Retries "5"; Acquire::http::Timeout "30"; Acquire::https::Timeout "30";' \
      > /etc/apt/apt.conf.d/99-retries; \
    for i in 1 2 3 4 5; do apt-get update -qq && break || sleep 10; done; \
    apt-get install -y --no-install-recommends \
      python3 python3-pip python3-venv python3-dev \
      git curl wget unzip tar build-essential libssl-dev libffi-dev \
      nmap netcat-openbsd iputils-ping traceroute net-tools iproute2 \
      arp-scan tcpdump dnsutils whois \
      sslscan \
      hydra john \
      jq vim less file libpcap-dev libxml2-dev libxslt1-dev python3-lxml; \
    apt-get install -y --no-install-recommends \
      nikto gobuster ffuf whatweb wafw00f sqlmap wpscan \
      hashcat crunch hash-identifier \
      enum4linux snmp ldap-utils \
      exiftool mat2 \
      aircrack-ng masscan testssl.sh exploitdb onesixtyone \
      mimikatz metasploit-framework \
      responder netexec dsniff \
      recon-ng amass wordlists dirb; \
    if [ -f /usr/share/wordlists/rockyou.txt.gz ]; then gunzip -k /usr/share/wordlists/rockyou.txt.gz; fi; \
    apt-get clean && rm -rf /var/lib/apt/lists/*

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
    go install -v github.com/ffuf/ffuf/v2@latest && \
    go install -v github.com/OJ/gobuster/v3@latest && \
    go install -v github.com/owasp-amass/amass/v4/...@master && \
    cp -r /root/go/bin/* /usr/local/bin/

# ── Impacket (network protocol exploitation suite) ───────────────────────────
RUN pip3 install --break-system-packages impacket


# ── theHarvester (latest from GitHub for freshest sources) ───────────────────
# Install theHarvester (delete destination first to avoid rebuild conflicts)
# NOTE: upstream entrypoint filename/path can differ by version, so we detect it.
RUN rm -rf /opt/theHarvester && \
    git clone --depth=1 https://github.com/laramies/theHarvester.git /opt/theHarvester && \
    REQ=$(find /opt/theHarvester -maxdepth 3 -name 'requirements*.txt' 2>/dev/null | head -n 1); \
    if [ -n "$REQ" ]; then pip3 install --break-system-packages -r "$REQ" || echo "[WARN] theHarvester requirements had errors"; fi; \
    ENTRYPOINT=; \
    if [ -f /opt/theHarvester/theHarvester.py ]; then \
      ENTRYPOINT=/opt/theHarvester/theHarvester.py; \
    else \
      # Try common nested layouts; pick the first match.
      ENTRYPOINT=$(find /opt/theHarvester -maxdepth 3 -type f -name 'theHarvester.py' 2>/dev/null | head -n 1); \
    fi; \
    if [ -n "$ENTRYPOINT" ] && [ -f "$ENTRYPOINT" ]; then \
      chmod +x "$ENTRYPOINT"; \
      # Create wrapper script (symlink to .py fails — can't exec Python as shell)
      printf '#!/bin/bash\nexec python3 %s "$@"\n' "$ENTRYPOINT" > /usr/local/bin/theHarvester && \
      chmod +x /usr/local/bin/theHarvester && \
      echo "[OK] theHarvester wrapper: $ENTRYPOINT"; \
    else \
      echo "[ERROR] theHarvester entrypoint not found; wrapper not created" && exit 1; \
    fi


# ── Metagoofil ────────────────────────────────────────────────────────────────
RUN git clone --depth=1 https://github.com/opsdisk/metagoofil.git /opt/metagoofil && \
    pip3 install --break-system-packages -r /opt/metagoofil/requirements.txt

# ── SpiderFoot ────────────────────────────────────────────────────────────────
RUN git clone --depth=1 https://github.com/smicallef/spiderfoot.git /opt/spiderfoot && \
    pip3 install --break-system-packages -r /opt/spiderfoot/requirements.txt 2>&1 || \
    echo "[INFO] SpiderFoot installed (lxml from apt, pip deps partial)"

# ── Python virtual environment for MCP server ─────────────────────────────────
RUN python3 -m venv /opt/mcp-venv && \
    /opt/mcp-venv/bin/pip install --upgrade pip setuptools wheel

RUN /opt/mcp-venv/bin/pip install \
    "mcp[cli]>=1.27,<2" \
    "uvicorn[standard]" \
    "starlette" \
    "httpx>=0.27.2" \
    "fastmcp>=3.4.2" && \
    echo "[OK] MCP SDK 1.28+ + fastmcp 3.4+ installed"

# ── OSINT Python packages — CRITICAL (build fails if these fail) ───────────────
RUN /opt/mcp-venv/bin/pip install \
    dnspython \
    shodan \
    requests \
    beautifulsoup4 \
    lxml \
    "scrapling[all]"

# ── OSINT Python packages — OPTIONAL (failures are non-fatal) ─────────────────
RUN /opt/mcp-venv/bin/pip install sherlock-project && \
    echo "[OK] sherlock"

RUN /opt/mcp-venv/bin/pip install holehe && \
    echo "[OK] holehe"

RUN /opt/mcp-venv/bin/pip install h8mail && \
    echo "[OK] h8mail"

RUN /opt/mcp-venv/bin/pip install maigret && \
    echo "[OK] maigret"

RUN /opt/mcp-venv/bin/pip install socialscan && \
    echo "[OK] socialscan"

RUN /opt/mcp-venv/bin/pip install ghunt && \
    echo "[OK] ghunt"

RUN /opt/mcp-venv/bin/pip install onionsearch && \
    echo "[OK] onionsearch"

RUN /opt/mcp-venv/bin/pip install instaloader && \
    echo "[OK] instaloader"

# NOTE: twint-fork removed — project abandoned since 2022, breaks consistently.
# Use reddit_user / twitter search via google_dork instead.

# XSStrike — install gracefully; create symlink only if binary exists
RUN /opt/mcp-venv/bin/pip install xsstrike && \
    ln -sf /opt/mcp-venv/bin/xsstrike /usr/local/bin/xssstrike && \
    echo "[OK] xsstrike"

# OSRFramework — optional, tools fall back to sherlock/holehe if absent
RUN /opt/mcp-venv/bin/pip install osrframework && \
    echo "[OK] osrframework"

RUN /opt/mcp-venv/bin/pip install phoneinfoga && \
    echo "[OK] phoneinfoga"

RUN ln -sf /opt/mcp-venv/bin/shodan /usr/local/bin/shodan

# ── Playwright browsers for Scrapling dynamic/stealth modes ──────────────────
RUN /opt/mcp-venv/bin/python3 -m playwright install --with-deps chromium && \
    echo "[OK] playwright chromium"

# ── commix (command injection exploiter) ─────────────────────────────────────
RUN git clone --depth=1 https://github.com/commixproject/commix.git /opt/commix && \
    ln -sf /opt/commix/commix.py /usr/local/bin/commix && \
    chmod +x /opt/commix/commix.py

# ── PhoneInfoga binary (faster than pip version) ─────────────────────────────
RUN ARCH=amd64 && \
    LATEST=$(curl -sSL https://api.github.com/repos/sundowndev/phoneinfoga/releases/latest \
        | grep tag_name | cut -d'"' -f4) && \
    curl -sSL "https://github.com/sundowndev/phoneinfoga/releases/download/${LATEST}/phoneinfoga_Linux_${ARCH}.tar.gz" \
        | tar -xzf - -C /usr/local/bin/ phoneinfoga && \
    chmod +x /usr/local/bin/phoneinfoga && echo "[OK] phoneinfoga binary" || \
    echo "[WARN] phoneinfoga binary download failed (pip version available)"

# ── Force-fix httpx (downstream tools like ghunt/holehe/duckpy downgrade it) ─
RUN /opt/mcp-venv/bin/pip install --upgrade --force-reinstall "httpx==0.28.1" && \
    echo "[OK] httpx pinned to 0.28.1 after all tool installs"

# ── Copy server file ──────────────────────────────────────────────────────────
RUN mkdir -p /opt/spectre /tmp/spectre
COPY spectre.py /opt/spectre/spectre.py

# ── Copy & register entrypoint ────────────────────────────────────────────────
COPY entrypoint.sh /opt/spectre/entrypoint.sh
RUN chmod +x /opt/spectre/entrypoint.sh

# ── Expose MCP Streamable HTTP port ──────────────────────────────────────────
EXPOSE 8001

# ── Working directory ─────────────────────────────────────────────────────────
WORKDIR /opt/spectre

ENTRYPOINT ["/opt/spectre/entrypoint.sh"]
