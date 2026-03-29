# 👻 SPECTRE 

<p align="center">
  <b>Surveillance, Penetration, Exploitation & Cyber Threat Reconnaissance Engine</b><br>
  <i>The ultimate OSINT + Pentest MCP Server for AI Agent.</i>
</p>

<p align="center">
  <a href="https://github.com/ItisPhoenix/Spectre-v1/stargazers"><img src="https://img.shields.io/github/stars/ItisPhoenix/Spectre-v1?style=for-the-badge&color=blue" alt="Stars"></a>
  <a href="https://github.com/ItisPhoenix/Spectre-v1/network/members"><img src="https://img.shields.io/github/forks/ItisPhoenix/Spectre-v1?style=for-the-badge&color=green" alt="Forks"></a>
  <a href="https://github.com/ItisPhoenix/Spectre-v1/issues"><img src="https://img.shields.io/github/issues/ItisPhoenix/Spectre-v1?style=for-the-badge&color=red" alt="Issues"></a>
  <img src="https://img.shields.io/badge/Tools-139-purple?style=for-the-badge" alt="Tools">
  <img src="https://img.shields.io/badge/Platform-Kali%20Linux-orange?style=for-the-badge" alt="Platform">
</p>

---

## ⚡ Powering Your Ai Agent
**SPECTRE** transforms your AI agent into a sophisticated security researcher. By running a containerized Kali Linux environment exposed via **Server-Sent Events (SSE)**, it grants AI Agent direct access to **139+ industrial-grade tools**.

### 🌟 Key Capabilities
*   **🔍 Advanced OSINT:** Deep-dive into identities, emails, social footprints, and domain infrastructure.
*   **💀 Offensive Pentesting:** Direct integration with Metasploit, password crackers, and network exploitation suites.
*   **🌐 Web Intelligence:** Automated vulnerability scanning, WAF bypassing, and high-speed dorking.
*   **🤖 AI-Native:** Designed from the ground up for the Model Context Protocol (MCP).

---

## 🚀 Quick Start
```bash
# 1. Spin up the engine
docker compose up -d --build

# 2. Connect your AI (e.g. Gemini CLI)
gemini mcp add --transport sse --trust spectre http://localhost:8001/sse
```

---

## 🛠️ Tool Ecosystem
| Domain | Lead Tools |
| :--- | :--- |
| **Identity** | `sherlock`, `maigret`, `holehe`, `ghunt` |
| **Network** | `nmap`, `masscan`, `naabu`, `httpx` |
| **Web App** | `nuclei`, `nikto`, `gobuster`, `ffuf`, `katana` |
| **Exploit** | `msfconsole`, `searchsploit`, `cve_lookup` |
| **Crypto** | `btc_address`, `eth_address`, `crypto_tx` |

---

## 📚 Documentation
For detailed installation steps, manual configuration, and tool documentation, please refer to our:
👉 **[Full HOW TO Guide](./HOW_TO.md)**

---

## ⚖️ Ethical Use
This tool is for **authorised penetration testing and research only**. By using this software, you agree to comply with all applicable local and international laws.

<p align="center">
  <i>"Knowledge is the best defense."</i>
</p>
