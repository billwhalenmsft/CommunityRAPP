# 🛠️ Getting Started with RAPP — Setup Guide for Solution Engineers

> **Who is this for?** SEs, SSPs, and anyone new to RAPP, VS Code, or coding tools. No prior experience needed.
> 
> **Based on:** Bill Whalen's VS Code Setup Guide for Solution Engineers

---

## What is RAPP?

**RAPP** (Rapid AI Agent Production Pipeline) is a platform for building and running AI agents — smart assistants that can help with sales, customer service, finance, healthcare, and more.

You can:
- 💬 **Chat** with AI agents through a web interface
- 🎬 **Run demos** to see agents in action
- ⚡ **Build new agents** from customer conversations
- 🏪 **Browse** a library of 30+ pre-built agents

---

## Part 1: Account Preparation

Before installing tools, make sure your accounts are ready.

### GitHub Account
1. Go to **https://github.com** and sign in (or create a free account)
2. You'll use this to download RAPP code and collaborate

### Link Your Microsoft + GitHub Accounts
This enables Copilot licensing and internal features:
1. Go to **https://docs.opensource.microsoft.com/github/opensource/accounts/linking/**
2. Follow the steps to connect your Microsoft identity to GitHub

### Join Microsoft GitHub Orgs (Internal Microsoft)
Go to **https://repos.opensource.microsoft.com/** and join:
- `Microsoft`
- `MicrosoftDocs`
- `Azure-Samples`

---

## Part 2: Install the Tools (One-Time Setup)

### Tool Checklist

| Tool | Download | Why You Need It |
|------|----------|-----------------|
| **VS Code** | https://code.visualstudio.com/ | Your code editor (like Word, but for code) |
| **Node.js 20+ LTS** | https://nodejs.org/ | JavaScript runtime — needed for MCP servers |
| **Python 3.11** | https://www.python.org/downloads/ | RAPP is built with Python (use 3.11 for Azure Functions) |
| **Git** | https://git-scm.com/downloads | Downloads and manages code |
| **Azure CLI** | https://aka.ms/installazurecli | Manages your Azure resources |
| **Azure Developer CLI** | https://aka.ms/install-azd | Template-based deployments |
| **Azure Functions Core Tools** | https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local | Runs the RAPP backend locally |

### Installation Tips
- **Python:** ⚠️ Check **"Add Python to PATH"** during install!
- **Node.js:** Use the **LTS** version (not Current)
- **VS Code:** ✅ Check **"Add to PATH"** if asked

### Verify Everything Installed
Open a terminal and run each command — you should see version numbers:

```
node --version       # v20+ expected
npm --version        # 10+ expected
python --version     # 3.11.x expected
git --version        # 2.x expected
az version           # 2.x expected
azd version          # 1.x expected
func --version       # 4.x expected
```

---

## Part 3: Install VS Code Extensions

Open VS Code, then paste this in the terminal to install everything at once:

```bash
code --install-extension github.copilot-chat
code --install-extension ms-azuretools.vscode-azure-mcp-server
code --install-extension ms-azuretools.vscode-azure-github-copilot
code --install-extension ms-azuretools.vscode-azurefunctions
code --install-extension ms-azuretools.vscode-azureresourcegroups
code --install-extension ms-azuretools.vscode-azurestorage
code --install-extension ms-azuretools.vscode-azurestaticwebapps
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-vscode.powershell
code --install-extension ritwickdey.liveserver
code --install-extension redhat.vscode-yaml
code --install-extension humao.rest-client
code --install-extension ms-copilotstudio.vscode-copilotstudio
code --install-extension teamsdevapp.ms-teams-vscode-extension
code --install-extension teamsdevapp.vscode-ai-foundry
```

### What These Are For

| Category | Extensions | Purpose |
|----------|-----------|---------|
| **AI & Copilot** | GitHub Copilot, AI Toolkit, AI Foundry | AI pair programming |
| **Azure** | Azure Tools, Functions, Storage, Static Web Apps | Cloud resource management |
| **Python** | Python, Pylance, Debugpy | Python development |
| **Teams & Copilot Studio** | Teams Toolkit, Copilot Studio | Build agents for M365 |
| **Utilities** | Live Server, YAML, REST Client, PowerShell | Day-to-day productivity |

---

## Part 4: Configure VS Code Settings

Press **Ctrl+Shift+P** → type **"Open User Settings (JSON)"** → press Enter.

Add these settings (merge with existing):

```json
{
  "github.copilot.nextEditSuggestions.enabled": true,
  "chat.instructionsFilesLocations": {
    ".github/instructions": true
  },
  "chat.useAgentSkills": true,
  "chat.agent.maxRequests": 500
}
```

---

## Part 5: Set Up MCP Servers

MCP (Model Context Protocol) servers let Copilot use external tools like Azure, GitHub, and Microsoft 365 directly.

The RAPP project already has MCP servers configured in `.vscode/mcp.json`. After cloning (Part 6), these load automatically:

| MCP Server | What It Does |
|------------|-------------|
| **M365 Agents Toolkit** | Build Teams/Copilot agents |
| **Azure Diagram MCP** | Generate architecture diagrams |
| **Work IQ** | Access M365 data (email, calendar, files, Teams) |
| **Azure MCP** (via extension) | Manage Azure resources |

---

## Part 6: Get the RAPP Code

### Step 1: Open VS Code

Launch VS Code from your Start Menu or Applications.

### Step 2: Open the Terminal

Click **Terminal** → **New Terminal** (or press **Ctrl+`**).

> 💡 **What is a terminal?** It's where you type commands. Think of it like texting instructions to your computer.

### Step 3: Clone the Code

Type these commands one at a time, pressing **Enter** after each:

```bash
cd Desktop
git clone https://github.com/billwhalenmsft/CommunityRAPP-BillWhalen.git
cd CommunityRAPP-BillWhalen
code .
```

VS Code will reopen with the RAPP project loaded. You'll see folders like `agents/`, `demos/`, `utils/` in the left panel.

### Step 4: Install Dependencies

In the terminal:
```bash
pip install -r requirements.txt
```

### Step 5: Authenticate

```bash
az login
azd auth login
```

Follow the browser prompts to sign in with your Microsoft account.

---

## Part 7: Run RAPP

### Option A: Just the Web UI (Quickest — No Azure Needed)

Browse the interface and play demos without any Azure setup:

```bash
python -m http.server 8080
```

Then open in your browser:
- **http://localhost:8080/welcome.html** — Welcome page
- **http://localhost:8080/index.html** — Chat UI
- **http://localhost:8080/demos/demos.html** — Demo Showcase

### Option B: Full RAPP with AI Chat (Needs Azure)

**Windows:**
```powershell
.\run.ps1
```

**Mac/Linux:**
```bash
./run.sh
```

Then open **http://localhost:8080/index.html** and configure the endpoint:
1. Click the ⚙️ gear icon → **Endpoints**
2. Add URL: `http://localhost:7071/api/businessinsightbot_function`
3. Start chatting! 🎉

### Option C: Use the Deployed Version (No Local Setup)

If RAPP is already deployed to Azure, just open:
- **https://rapp-kt6i6mlby5wzi.azurewebsites.net/api/ui/** — Welcome page
- **https://rapp-kt6i6mlby5wzi.azurewebsites.net/api/ui/index.html** — Chat UI
- **https://rapp-kt6i6mlby5wzi.azurewebsites.net/api/ui/demos/demos.html** — Demos

---

## Part 8: Explore the Interface

### Chat UI Toolbar

| Button | Icon | What it does |
|--------|------|--------------|
| ☰ | Hamburger | Sidebar (chat history, settings) |
| 🏪 | Grid | App Store |
| 📖 | Book | Production guide |
| 🎬 | Play circle | **Demo Hub** — browse and play demos |
| ⚙️ | Gear | Settings (endpoints, theme, voice) |

### Running a Demo

1. Click the **🎬 Demo Hub** button
2. Search for a demo (try "SMA4" or "sales")
3. Click a card to load it
4. Use the teleprompter bar:
   - **▶️ Next** — play next step
   - **⏩ Auto** — auto-play all steps
   - **⏹️ Stop** — stop the demo

---

## Part 9: GitHub Copilot Tips

### Key Shortcuts

| Shortcut | What It Does |
|----------|-------------|
| `Ctrl+Shift+I` | Open Copilot Chat |
| `Tab` | Accept code suggestion |
| `Esc` | Dismiss suggestion |
| `Ctrl+Enter` | Send chat message |
| `Ctrl+`` ` | Toggle terminal |
| `Ctrl+P` | Quick open file |
| `Ctrl+Shift+F` | Search across files |

### Copilot Modes
- **Agent Mode** — Give high-level goals, Copilot plans and executes
- **Edit Mode** — Copilot suggests inline code changes
- **Ask Mode** — Ask questions about code

### Context Commands
Use these in Copilot Chat for better answers:
- `@workspace` — Context about your project
- `@terminal` — Context from terminal output
- `@azure` — Azure resource management help

### Instruction Files
Create a `copilot-instructions.md` in your repo root to tell Copilot about your project's tech stack, conventions, and key files. This dramatically improves suggestions.

---

## Part 10: Try These First!

### 🥇 Play a Demo (No Setup Required)
1. Open the Chat UI → click 🎬 Demo Hub
2. Search for "SMA4 Workbench" → click it
3. Watch a 12-step sales cockpit demo play out

### 🥈 Chat with the AI (Needs Azure)
Type in the chat:
- *"What can you do?"*
- *"Remember that I prefer morning meetings"*
- *"Load the call center demo"*

### 🥉 Build an Agent (Advanced)
Type: *"Start a RAPP pipeline for an IT helpdesk agent"*

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `python` not found | Reinstall Python with "Add to PATH" checked, restart VS Code |
| `func` not found | Install Azure Functions Core Tools, restart terminal |
| Port 7071 in use | `Stop-Process -Name func -Force` (Windows) |
| Module not found | `pip install -r requirements.txt` |
| Chat not responding | Check endpoint URL in ⚙️ Settings → Endpoints |
| Copilot not working | Sign in to GitHub in VS Code, check Copilot extension is installed |

---

## Quick Reference: Recommended Tool Versions

| Tool | Version |
|------|---------|
| VS Code | Latest stable |
| Node.js | v20+ LTS |
| Python | 3.11.x |
| Git | 2.x |
| Azure CLI | 2.x |
| Azure Developer CLI | 1.x |
| Azure Functions Core Tools | 4.x |

---

**Questions?** Contact billwhalen@microsoft.com or ask in the RAPP chat! 🤖
