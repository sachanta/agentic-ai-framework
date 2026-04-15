# Windows 11 Enterprise Setup Guide

Complete installation and setup instructions for the Agentic AI Framework on Windows 11 Enterprise.

---

## Prerequisites Overview

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Backend runtime |
| Node.js | 18+ | Frontend runtime |
| MongoDB | 7.0+ | Database |
| Weaviate | 1.24+ | Vector database for RAG |
| Docker Desktop | Latest | Required for Weaviate |
| Ollama | Latest | Local LLM (optional) |
| Git | Latest | Version control |
| VS Code | Latest | IDE with Copilot |

---

## Step 1: Install Git

### Option A: Git for Windows (Recommended)
1. Download from https://git-scm.com/download/win
2. Run installer with default options
3. Verify installation:
   ```powershell
   git --version
   ```

### Option B: Via winget
```powershell
winget install Git.Git
```

---

## Step 2: Install Python 3.11+

### Option A: Python.org Installer (Recommended)
1. Download Python 3.11+ from https://www.python.org/downloads/
2. Run installer
3. **IMPORTANT**: Check "Add Python to PATH" during installation
4. Check "Install pip"
5. Verify installation:
   ```powershell
   python --version
   pip --version
   ```

### Option B: Via winget
```powershell
winget install Python.Python.3.11
```

### Option C: Via Microsoft Store
1. Open Microsoft Store
2. Search for "Python 3.11"
3. Install

### Post-Install: Upgrade pip
```powershell
python -m pip install --upgrade pip
```

---

## Step 3: Install Node.js 18+

### Option A: Node.js Installer (Recommended)
1. Download LTS version from https://nodejs.org/
2. Run installer with default options
3. Verify installation:
   ```powershell
   node --version
   npm --version
   ```

### Option B: Via winget
```powershell
winget install OpenJS.NodeJS.LTS
```

### Option C: Via nvm-windows (for managing multiple versions)
1. Download nvm-windows from https://github.com/coreybutler/nvm-windows/releases
2. Install nvm
3. Install Node.js:
   ```powershell
   nvm install 18
   nvm use 18
   ```

---

## Step 4: Install MongoDB

### Option A: MongoDB Community Server (Recommended)
1. Download from https://www.mongodb.com/try/download/community
2. Choose "Windows x64" and "msi" package
3. Run installer:
   - Choose "Complete" installation
   - Check "Install MongoDB as a Service"
   - Check "Install MongoDB Compass" (GUI tool)
4. MongoDB will start automatically as a Windows service
5. Verify installation:
   ```powershell
   # Check service is running
   Get-Service MongoDB

   # Or connect with mongosh
   mongosh --eval "db.version()"
   ```

### Option B: Via winget
```powershell
winget install MongoDB.Server
```

### Option C: MongoDB Atlas (Cloud - No Local Install)
1. Create free account at https://www.mongodb.com/atlas
2. Create a free cluster
3. Get connection string for your `.env` file

### Verify MongoDB is Running
```powershell
# Check Windows service
Get-Service -Name "MongoDB"

# Start if not running
Start-Service -Name "MongoDB"

# Test connection
mongosh --eval "db.stats()"
```

---

## Step 5: Install Docker Desktop

Docker is required to run Weaviate (vector database).

### Download and Install
1. Download from https://www.docker.com/products/docker-desktop/
2. Run installer
3. Restart your computer when prompted
4. Start Docker Desktop from Start Menu
5. Wait for Docker to fully start (whale icon in system tray stops animating)

### Alternative: Via winget
```powershell
winget install Docker.DockerDesktop
```

### Verify Installation
```powershell
docker --version
docker run hello-world
```

### Enable WSL 2 Backend (Recommended)
Docker Desktop on Windows works best with WSL 2:
1. Open Docker Desktop Settings
2. Go to "General"
3. Ensure "Use the WSL 2 based engine" is checked

### Troubleshooting Docker
If Docker won't start:
```powershell
# Enable required Windows features (run as Administrator)
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Restart computer, then set WSL 2 as default
wsl --set-default-version 2
```

---

## Step 6: Install Weaviate (Vector Database)

Weaviate is used for RAG (Retrieval-Augmented Generation) features.

### Option A: Docker Compose (Recommended)

Create `weaviate/docker-compose.yml` in your project root:
```powershell
# Create directory
New-Item -ItemType Directory -Path weaviate -Force
cd weaviate

# Create docker-compose.yml
@"
version: '3.4'
services:
  weaviate:
    image: cr.weaviate.io/semitechnologies/weaviate:1.24.1
    ports:
      - "8080:8080"
      - "50051:50051"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'none'
      ENABLE_MODULES: ''
      CLUSTER_HOSTNAME: 'node1'
    volumes:
      - weaviate_data:/var/lib/weaviate
    restart: unless-stopped

volumes:
  weaviate_data:
"@ | Out-File -FilePath docker-compose.yml -Encoding utf8
```

Start Weaviate:
```powershell
docker-compose up -d
```

### Option B: Docker Run (Quick Start)
```powershell
docker run -d `
  --name weaviate `
  -p 8080:8080 `
  -p 50051:50051 `
  -e QUERY_DEFAULTS_LIMIT=25 `
  -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true `
  -e PERSISTENCE_DATA_PATH=/var/lib/weaviate `
  -e DEFAULT_VECTORIZER_MODULE=none `
  -e CLUSTER_HOSTNAME=node1 `
  cr.weaviate.io/semitechnologies/weaviate:1.24.1
```

### Option C: Weaviate Cloud (No Local Install)
1. Create free account at https://console.weaviate.cloud/
2. Create a free sandbox cluster
3. Get the cluster URL and API key for your `.env` file

### Verify Weaviate is Running
```powershell
# Check container is running
docker ps | findstr weaviate

# Test REST API
curl http://localhost:8080/v1/.well-known/ready

# Or with PowerShell
Invoke-RestMethod -Uri "http://localhost:8080/v1/.well-known/ready"

# Check schema (should return empty initially)
Invoke-RestMethod -Uri "http://localhost:8080/v1/schema"
```

### Weaviate Management Commands
```powershell
# Start Weaviate
docker start weaviate

# Stop Weaviate
docker stop weaviate

# View logs
docker logs weaviate

# Remove container (data preserved in volume)
docker rm weaviate

# Remove container AND data
docker rm weaviate
docker volume rm weaviate_weaviate_data
```

---

## Step 7: Install Ollama (Optional - for Local LLM)

### Download and Install
1. Download from https://ollama.com/download/windows
2. Run the installer
3. Ollama will start automatically
4. Pull a model:
   ```powershell
   ollama pull llama3
   ```
5. Verify installation:
   ```powershell
   ollama list
   curl http://localhost:11434/api/tags
   ```

### Note
If you don't install Ollama, the application will use fallback greetings instead of LLM-generated ones.

---

## Step 8: Install VS Code with GitHub Copilot

### Install VS Code
1. Download from https://code.visualstudio.com/
2. Run installer
3. Or via winget:
   ```powershell
   winget install Microsoft.VisualStudio.Code
   ```

### Install GitHub Copilot Extension
1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "GitHub Copilot"
4. Install "GitHub Copilot" and "GitHub Copilot Chat"
5. Sign in with your GitHub account (requires Copilot subscription)

### Recommended VS Code Extensions
- Python (Microsoft)
- Pylance
- ES7+ React/Redux/React-Native snippets
- Tailwind CSS IntelliSense
- Prettier - Code formatter
- ESLint

---

## Step 9: Clone the Repository

```powershell
# Navigate to your projects folder
cd C:\Projects  # or your preferred location

# Clone the repository
git clone <repository-url> agentic-ai-framework

# Navigate into the project
cd agentic-ai-framework
```

---

## Step 10: Setup Backend

### Create Virtual Environment
```powershell
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1

# If you get an execution policy error, run this first:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Install Dependencies
```powershell
# Ensure virtual environment is activated (you should see (.venv) in prompt)

# Install the package in development mode
pip install -e ".[dev]"

# Or if pyproject.toml uses different extras:
pip install -e .
pip install pytest pytest-asyncio pytest-cov httpx
```

### Create Environment File
Create `backend/.env`:
```powershell
# Using PowerShell to create .env file
@"
# Application
APP_NAME=Agentic AI Framework
DEBUG=true

# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=agentic_ai

# LLM Configuration
LLM_PROVIDER=ollama
LLM_DEFAULT_MODEL=llama3
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1000

# Ollama
OLLAMA_BASE_URL=http://localhost:11434

# Weaviate
WEAVIATE_URL=http://localhost:8080

# CORS (frontend URL)
CORS_ORIGINS_STR=http://localhost:5173,http://localhost:3000

# Auth
SECRET_KEY=change-this-to-a-secure-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Logging
LOG_LEVEL=INFO
"@ | Out-File -FilePath .env -Encoding utf8
```

### Verify Backend Setup
```powershell
# Make sure virtual environment is activated
.venv\Scripts\Activate.ps1

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, test the API
curl http://localhost:8000/api/v1/docs
```

---

## Step 11: Setup Frontend

### Install Dependencies
```powershell
cd ..\frontend  # Navigate from backend to frontend

# Install npm packages
npm install
```

### Create Environment File (Optional)
Create `frontend/.env`:
```powershell
@"
VITE_API_BASE_URL=http://localhost:8000
VITE_ENABLE_MOCKS=false
"@ | Out-File -FilePath .env -Encoding utf8
```

### Verify Frontend Setup
```powershell
# Start development server
npm run dev

# Open browser to http://localhost:5173
```

---

## Step 12: Verify Full Stack

### Start All Services

Open multiple PowerShell terminals:

**Terminal 1 - MongoDB (if not running as service):**
```powershell
# Usually MongoDB runs as a Windows service, check:
Get-Service MongoDB

# If not a service, start manually:
mongod --dbpath C:\data\db
```

**Terminal 2 - Weaviate (via Docker):**
```powershell
# Start Weaviate container
docker start weaviate

# Or if using docker-compose:
cd C:\Projects\agentic-ai-framework\weaviate
docker-compose up -d

# Verify it's running
curl http://localhost:8080/v1/.well-known/ready
```

**Terminal 3 - Backend:**
```powershell
cd C:\Projects\agentic-ai-framework\backend
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

**Terminal 4 - Frontend:**
```powershell
cd C:\Projects\agentic-ai-framework\frontend
npm run dev
```

**Terminal 5 - Ollama (optional):**
```powershell
ollama serve
# Or it may already be running as a background process
```

### Test the Application

1. Open browser to http://localhost:5173 (Frontend)
2. Open browser to http://localhost:8000/api/v1/docs (API Docs)
3. Test the hello-world endpoint:
   ```powershell
   $body = '{"name": "Windows User", "style": "friendly"}'
   Invoke-RestMethod -Uri "http://localhost:8000/api/v1/platforms/hello-world/execute" -Method Post -Body $body -ContentType "application/json"
   ```

---

## Troubleshooting

### Python: "python" is not recognized
```powershell
# Check if Python is in PATH
$env:PATH -split ';' | Select-String -Pattern "Python"

# Add Python to PATH manually if needed
$env:PATH += ";C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311"
$env:PATH += ";C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311\Scripts"
```

### PowerShell: Script execution is disabled
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### MongoDB: Service won't start
```powershell
# Check if data directory exists
New-Item -ItemType Directory -Path C:\data\db -Force

# Check MongoDB logs
Get-Content "C:\Program Files\MongoDB\Server\7.0\log\mongod.log" -Tail 50

# Start service manually
net start MongoDB
```

### Weaviate: Connection refused
```powershell
# Check if Docker is running
docker info

# Check if Weaviate container exists
docker ps -a | findstr weaviate

# Start existing container
docker start weaviate

# Or create new container if doesn't exist
docker run -d --name weaviate -p 8080:8080 -p 50051:50051 `
  -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true `
  cr.weaviate.io/semitechnologies/weaviate:1.24.1

# Check logs for errors
docker logs weaviate --tail 50
```

### Ollama: Connection refused
```powershell
# Check if Ollama is running
Get-Process ollama -ErrorAction SilentlyContinue

# Start Ollama
ollama serve

# Verify
curl http://localhost:11434/api/tags
```

### Port already in use
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process by PID (replace 1234 with actual PID)
taskkill /PID 1234 /F
```

### pip install fails with SSL error
```powershell
# Try with trusted hosts
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -e ".[dev]"
```

### npm install fails
```powershell
# Clear npm cache
npm cache clean --force

# Delete node_modules and try again
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

---

## Quick Reference Commands

### Backend
```powershell
cd backend
.venv\Scripts\Activate.ps1           # Activate venv
deactivate                            # Deactivate venv
uvicorn app.main:app --reload         # Start server
python -m pytest -v                   # Run tests
pip freeze > requirements.txt         # Export dependencies
```

### Frontend
```powershell
cd frontend
npm run dev                           # Start dev server
npm run build                         # Production build
npm run lint                          # Run linter
npm test                              # Run tests
```

### MongoDB
```powershell
mongosh                               # MongoDB shell
mongosh --eval "show dbs"             # List databases
Get-Service MongoDB                   # Check service status
Start-Service MongoDB                 # Start service
Stop-Service MongoDB                  # Stop service
```

### Weaviate (Docker)
```powershell
docker start weaviate                 # Start Weaviate
docker stop weaviate                  # Stop Weaviate
docker logs weaviate                  # View logs
docker ps | findstr weaviate          # Check if running
```

### Ollama
```powershell
ollama serve                          # Start Ollama
ollama list                           # List models
ollama pull llama3                    # Download model
ollama run llama3                     # Interactive chat
```

---

## Environment Summary

After setup, you should have:

| Service | URL | Status Check |
|---------|-----|--------------|
| Frontend | http://localhost:5173 | Open in browser |
| Backend API | http://localhost:8000 | `curl http://localhost:8000/api/v1/docs` |
| API Docs | http://localhost:8000/api/v1/docs | Open in browser |
| MongoDB | localhost:27017 | `mongosh --eval "db.stats()"` |
| Weaviate | http://localhost:8080 | `curl http://localhost:8080/v1/.well-known/ready` |
| Ollama | http://localhost:11434 | `curl http://localhost:11434/api/tags` |

---

## Next Steps

1. Read the [README.md](./README.md) for how to use the phase prompts
2. Start with [Phase 1](./phase-prompts/phase-01-config.md)
3. Track progress in `docs/implementation-log.md`
