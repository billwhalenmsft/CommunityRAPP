# 🚀 Getting Started with RAPP — A Complete Beginner's Guide

> **Who is this for?** Anyone new to RAPP, VS Code, or coding tools. No prior experience needed.

---

## What is RAPP?

**RAPP** (Rapid AI Agent Production Pipeline) is a platform for building and running AI agents — smart assistants that can help with sales, customer service, finance, healthcare, and more.

You can:
- 💬 **Chat** with AI agents through a web interface
- 🎬 **Run demos** to see agents in action
- ⚡ **Build new agents** from customer conversations
- 🏪 **Browse** a library of 30+ pre-built agents

---

## Part 1: Install the Tools (One-Time Setup)

You need three things installed. If you already have them, skip to [Part 2](#part-2-get-the-code).

### 1A. Install VS Code

VS Code is a free code editor from Microsoft. It's where you'll open and work with RAPP.

1. Go to **https://code.visualstudio.com**
2. Click the big **Download** button
3. Run the installer — accept all defaults
4. ✅ Check **"Add to PATH"** if asked (important!)

> 💡 **What is VS Code?** Think of it like Microsoft Word, but for code. It shows files, lets you edit them, and has a built-in terminal (command line).

### 1B. Install Python 3.11

Python is the programming language RAPP is built with.

1. Go to **https://www.python.org/downloads/**
2. Download **Python 3.11.x** (not 3.12 or 3.13 — Azure Functions needs 3.11)
3. Run the installer
4. ⚠️ **IMPORTANT:** Check the box that says **"Add Python to PATH"** on the first screen!
5. Click **Install Now**

**Verify it worked:** Open a new terminal (see below) and type:
```
python --version
```
You should see `Python 3.11.x`

### 1C. Install Git

Git is how you download and manage code.

1. Go to **https://git-scm.com/downloads**
2. Download for your operating system
3. Run the installer — accept all defaults

### 1D. Install Azure Functions Core Tools

This lets you run the RAPP backend on your computer.

1. Go to **https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local**
2. Download **v4.x** for your OS
3. Run the installer

**Or install via command line:**
```
npm install -g azure-functions-core-tools@4 --unsafe-perm true
```

> 💡 **Don't have npm?** Install Node.js first from https://nodejs.org (LTS version).

---

## Part 2: Get the Code

### Step 1: Open VS Code

- **Windows:** Click the VS Code icon on your desktop or Start Menu
- **Mac:** Open VS Code from Applications

### Step 2: Open the Terminal in VS Code

The terminal is a text-based command line built into VS Code.

1. Click **Terminal** in the top menu bar
2. Click **New Terminal**
3. A panel appears at the bottom of VS Code — this is your terminal

> 💡 **What is a terminal?** It's where you type commands instead of clicking buttons. Think of it like texting your computer instructions.

### Step 3: Clone (Download) the RAPP Code

In the terminal, type these commands one at a time and press **Enter** after each:

```bash
cd Desktop
```
*(This moves to your Desktop folder)*

```bash
git clone https://github.com/billwhalenmsft/CommunityRAPP-BillWhalen.git
```
*(This downloads the RAPP code — it will take a few seconds)*

```bash
cd CommunityRAPP-BillWhalen
```
*(This moves into the RAPP folder)*

### Step 4: Open the Project in VS Code

In the terminal, type:
```bash
code .
```
*(The dot means "this folder" — VS Code will reopen with the RAPP project loaded)*

You should now see a file explorer on the left showing folders like `agents/`, `demos/`, `utils/`, etc.

---

## Part 3: Install Dependencies

Still in the VS Code terminal:

```bash
pip install -r requirements.txt
```

This installs all the Python libraries RAPP needs. It may take 1-2 minutes.

> ⚠️ If you get an error about `pip` not found, try `pip3 install -r requirements.txt` or `python -m pip install -r requirements.txt`

---

## Part 4: Run RAPP Locally

### Option A: Just the Web UI (Quickest — No Azure Needed)

You can browse the RAPP interface and demos without any Azure setup:

1. In the VS Code terminal, type:
   ```bash
   python -m http.server 8080
   ```

2. Open your web browser and go to:
   - **http://localhost:8080/welcome.html** — Welcome page
   - **http://localhost:8080/index.html** — Chat UI
   - **http://localhost:8080/demos/demos.html** — Demo Showcase

3. In the Chat UI, click the **🎬 button** in the top-right to open the Demo Hub and play scripted demos

> 💡 This mode lets you explore the UI and play demos, but the AI chat won't respond (it needs an API backend). See Option B for full functionality.

### Option B: Full RAPP with AI Chat (Needs Azure)

To get AI responses, you need Azure credentials configured:

1. **Windows:**
   ```powershell
   .\run.ps1
   ```

2. **Mac/Linux:**
   ```bash
   ./run.sh
   ```

3. If successful, you'll see:
   ```
   Azure Functions Core Tools
   Functions:
       businessinsightbot_function: http://localhost:7071/api/businessinsightbot_function
   ```

4. Open **http://localhost:8080/index.html** in your browser
5. Click the ⚙️ gear icon → **Endpoints** → add your Azure Function URL:
   - **URL:** `http://localhost:7071/api/businessinsightbot_function`
   - **Name:** Local Dev
6. Start chatting! 🎉

> ⚠️ **Need Azure credentials?** See [Setting Up Azure](#setting-up-azure) below.

---

## Part 5: Explore the Interface

### The Chat UI (`index.html`)

This is the main RAPP interface. Here's what the toolbar buttons do:

| Button | Icon | What it does |
|--------|------|--------------|
| ☰ | Hamburger menu | Open sidebar (chat history, settings) |
| 🏪 | Grid | Open App Store |
| 📖 | Book | Open production guide |
| 🎬 | Play circle | **Demo Hub** — browse and play agent demos |
| ⚙️ | Gear | Settings (endpoints, theme, voice) |

### Running a Demo

1. Click the **🎬 Demo Hub** button
2. Browse or search for a demo (try "SMA4" or "sales")
3. Click a demo card to load it
4. Use the teleprompter bar at the bottom:
   - **▶️ Next** — play next step
   - **⏩ Auto** — auto-play all steps (3-second delay)
   - **⏹️ Stop** — stop the demo

### The Demo Showcase (`demos/demos.html`)

A separate page for browsing all agent demos:
- Filter by category (Sales, Finance, Healthcare, etc.)
- Search by name or description
- Click **"Play in RAPP"** to open any demo in the Chat UI
- Click **"JSON"** to download the raw demo file

---

## Part 6: Try These First!

### 🥇 Play a Demo (No Setup Required)

1. Open the Chat UI
2. Click 🎬 Demo Hub
3. Search for "SMA4 Workbench"
4. Click it → watch a 12-step sales cockpit demo play out

### 🥈 Chat with the AI (Needs Azure)

Type any of these in the chat:
- *"What can you do?"*
- *"Remember that I prefer morning meetings"*
- *"Show me the demo list"*
- *"Load the call center demo"*

### 🥉 Build an Agent (Advanced)

Type in the chat:
- *"Start a RAPP pipeline for an IT helpdesk agent"*

This walks you through the full agent creation process.

---

## Setting Up Azure

If you're starting from scratch and need Azure credentials:

### Quick Setup (Recommended)

1. **Deploy to Azure** — Click this button in the [README](../README.md):

   [![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fkody-w%2FEntraCopilotAgent365%2Fmain%2Fazuredeploy.json)

2. Fill in the form (resource group name, region)
3. Wait for deployment to complete (~5 minutes)
4. Click **Outputs** → copy the setup script
5. Run the script — it creates `local.settings.json` automatically

### Manual Setup

If you already have Azure resources, create `local.settings.json` in the project root:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage__blobServiceUri": "https://YOUR-STORAGE.blob.core.windows.net",
    "AzureWebJobsStorage__queueServiceUri": "https://YOUR-STORAGE.queue.core.windows.net",
    "AzureWebJobsStorage__tableServiceUri": "https://YOUR-STORAGE.table.core.windows.net",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_OPENAI_ENDPOINT": "https://YOUR-RESOURCE.cognitiveservices.azure.com/",
    "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4o",
    "AZURE_OPENAI_API_VERSION": "2024-08-01-preview",
    "AZURE_STORAGE_ACCOUNT_NAME": "YOUR-STORAGE-ACCOUNT"
  }
}
```

Then run `az login` and start the function app.

---

## Common Issues

### "Python not found" or "pip not found"

- Make sure Python 3.11 is installed with **"Add to PATH" checked**
- Close and reopen VS Code after installing Python
- Try `python3` instead of `python`

### "func not found"

- Install Azure Functions Core Tools (see [Part 1D](#1d-install-azure-functions-core-tools))
- Close and reopen your terminal after installing

### "Port 7071 already in use"

Another instance is running. Close it first:
- **Windows:** `Stop-Process -Name func -Force` (in PowerShell)
- **Mac/Linux:** `pkill -f "func host start"`

### "Module not found" errors

```bash
pip install -r requirements.txt
```

### The chat isn't responding

- Make sure the function app is running (`.\run.ps1` or `./run.sh`)
- Check that the endpoint URL in ⚙️ Settings → Endpoints matches your running URL
- Check the terminal for error messages

---

## VS Code Tips for Beginners

### Useful Keyboard Shortcuts

| Shortcut | What it does |
|----------|-------------|
| `Ctrl+`` ` (backtick) | Toggle terminal |
| `Ctrl+Shift+E` | Show file explorer |
| `Ctrl+P` | Quick open a file by name |
| `Ctrl+Shift+F` | Search across all files |
| `Ctrl+S` | Save current file |
| `Ctrl+Z` | Undo |

### The File Explorer

- Left panel shows all project files and folders
- Click any file to open it
- Right-click for options (rename, delete, etc.)
- Key folders:
  - `agents/` — AI agent code
  - `demos/` — Demo scripts (JSON files)
  - `utils/` — Utility functions
  - `docs/` — Documentation

### The Terminal

- Bottom panel where you type commands
- You can have multiple terminals (click the `+` button)
- Use ↑ arrow to repeat previous commands

---

## What's Next?

| Goal | Where to Go |
|------|-------------|
| Learn about the architecture | [README.md](../README.md) |
| Build a custom agent | [QUICK_START.md](../QUICK_START.md) |
| Run the RAPP pipeline | Type "rapp" in the chat |
| Deploy to Azure | [docs/DEPLOYMENT.md](DEPLOYMENT.md) |
| Set up Power Platform | [docs/POWER_PLATFORM_INTEGRATION.md](POWER_PLATFORM_INTEGRATION.md) |
| Troubleshoot issues | [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md) |

---

**Questions?** Open an issue on GitHub or ask in the RAPP chat — the AI assistant can help you navigate the platform! 🤖
