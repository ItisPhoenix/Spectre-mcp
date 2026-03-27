# ╔══════════════════════════════════════════════════════════════╗
# ║  SPECTRE MCP — Docker Image                                   ║
# ║  Base: Kali Linux (full pentest + OSINT toolset)              ║
# ╚══════════════════════════════════════════════════════════════╝

# Use the official Kali rolling image as a base
FROM kalilinux/kali-rolling:latest

LABEL maintainer="SPECTRE"
LABEL description="SPECTRE MCP — OSINT + Pentest unified MCP server"

# Set environment variables to enable non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive
ENV MCP_TRANSPORT=sse
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8001
ENV TOOL_TIMEOUT=300
ENV SPECTRE_PYTHON=/opt/mcp-venv/bin/python3
ENV SPECTRE_WORDLIST=/usr/share/wordlists/dirb/common.txt

# ── System update & core dependencies ────────────────────────────────────────
RUN apt-get update && apt-get install -y --fix-missing --no-install-recommends \
    python3 \
    python3-venv \
    python3-pip \
    golang \
    curl \
    wget \
    git \
    sudo \
    libnss3 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libgbm1 libasound2 libxshmfence1 \
    libpangocairo-1.0-0 libpango-1.0-0 libatk1.0-0 libcairo2 libgdk-pixbuf2.0-0 libgtk-3-0 \
    nmap masscan nikto sqlmap wpscan gobuster ffuf dirb \
    whatweb wafw00f sslscan testssl.sh dnsrecon dnsenum fierce dmitry \
    theharvester recon-ng libimage-exiftool-perl mat2 exploitdb \
    onesixtyone snmp enum4linux hydra john hashcat aircrack-ng \
    metasploit-framework netexec responder dsniff tcpdump \
    netcat-traditional smbclient impacket-scripts commix \
    dnsutils whois traceroute arp-scan hash-identifier crunch \
    && rm -rf /var/lib/apt/lists/*

# ── Custom Tool Placements ────────────────────────────────────────────────────
# Clone metagoofil and spiderfoot into /opt where spectre.py expects them, and symlink xsstrike
RUN git clone https://github.com/opsdisk/metagoofil.git /opt/metagoofil && \
    git clone https://github.com/smicallef/spiderfoot.git /opt/spiderfoot && \
    cd /opt/spiderfoot && /opt/mcp-venv/bin/pip install -r requirements.txt || true && \
    ln -s /opt/mcp-venv/bin/xsstrike /usr/local/bin/xssstrike || true && \
    ln -s /usr/bin/netexec /usr/local/bin/crackmapexec || true

# ── Wordlists ─────────────────────────────────────────────────────────────────
RUN apt-get update -qq && apt-get install -y --no-install-recommends wordlists \
    && gunzip /usr/share/wordlists/rockyou.txt.gz \
    && rm -rf /var/lib/apt/lists/*

# ── Go-based recon tools ──────────────────────────────────────────────────────
RUN go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest && \
    go install github.com/projectdiscovery/httpx/cmd/httpx@latest && \
    go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest && \
    go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest && \
    go install github.com/projectdiscovery/katana/cmd/katana@latest && \
    go install github.com/projectdiscovery/tlsx/cmd/tlsx@latest && \
    go install github.com/projectdiscovery/dnsx/cmd/dnsx@latest && \
    go install github.com/tomnomnom/assetfinder@latest && \
    go install github.com/hakluke/hakrawler@latest && \
    go install github.com/jaeles-project/gospider@latest && \
    go install github.com/tomnomnom/waybackurls@latest && \
    go install github.com/lc/gau/v2/cmd/gau@latest && \
    cp /root/go/bin/* /usr/local/bin/

# Update nuclei templates
RUN /usr/local/bin/nuclei -update-templates

# ── Amass ─────────────────────────────────────────────────────────────────────
RUN apt-get update -qq && apt-get install -y amass --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# ── Python venv + MCP (pinned) + OSINT tools ─────────────────────────────────
# Pinned: mcp==1.24.0 + fastmcp==2.3.3 — stable pair compatible with Gemini CLI SSE
RUN python3 -m venv /opt/mcp-venv

RUN /opt/mcp-venv/bin/pip install --upgrade pip setuptools wheel -q && \
    /opt/mcp-venv/bin/pip install -q \
    "mcp[cli]==1.24.0" \
    "fastmcp==2.3.3" \
    uvicorn starlette \
    sherlock-project holehe h8mail maigret socialscan ghunt \
    instaloader onionsearch \
    dnspython shodan \
    scrapling[all] \
    requests beautifulsoup4 lxml python-whois rich click \
    osrframework twint-fork xsstrike && \
    /opt/mcp-venv/bin/python3 -m scrapling install && \
    /opt/mcp-venv/bin/pip install phoneinfoga

# ── App ───────────────────────────────────────────────────────────────────────
WORKDIR /opt/spectre
COPY spectre.py .

EXPOSE 8001

# Healthcheck uses SSE transport
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -sf http://localhost:8001/sse || exit 1

ENTRYPOINT ["/opt/mcp-venv/bin/python3", "spectre.py"]
