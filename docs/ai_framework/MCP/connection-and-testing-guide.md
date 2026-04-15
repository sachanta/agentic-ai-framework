# MCP Server — Connection & Testing Guide

A hands-on guide to connecting Claude Desktop, Windsurf, and Claude Code to the Agentic AI Framework MCP server, and then testing every tool across all 5 categories (search, email, cache, RAG, LLM).

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Environment Setup](#2-environment-setup)
3. [Connecting from Claude Desktop](#3-connecting-from-claude-desktop)
4. [Connecting from Windsurf](#4-connecting-from-windsurf)
5. [Connecting from Claude Code](#5-connecting-from-claude-code)
6. [Verifying the Connection](#6-verifying-the-connection)
7. [Testing All 16 Tools](#7-testing-all-16-tools)
   - [Search Tools (4)](#71-search-tools-tavily)
   - [Email Tools (3)](#72-email-tools-resend)
   - [Cache Tools (3)](#73-cache-tools-mongodb)
   - [RAG Tools (2)](#74-rag-tools-weaviate)
   - [LLM Tools (4)](#75-llm-tools)
8. [End-to-End Newsletter Workflow via MCP](#8-end-to-end-newsletter-workflow-via-mcp)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Prerequisites

| Requirement | Purpose |
|-------------|---------|
| Python 3.11+ | MCP server runtime |
| MongoDB (running) | Cache tools, workflow state |
| Weaviate (running) | RAG vector storage |
| Tavily API key | Search tools |
| Resend API key | Email tools |
| LLM provider configured | LLM tools (Ollama, Gemini, OpenAI, Perplexity, or AWS Bedrock) |

**MCP Client (at least one):**
- Claude Desktop (macOS / Windows)
- Windsurf IDE
- Claude Code CLI

---

## 2. Environment Setup

### 2.1 Install Dependencies

```bash
cd backend
pip install -e ".[dev]"
```

This installs the framework including the `mcp>=1.26.0` dependency.

### 2.2 Configure Environment Variables

Copy the example and fill in your keys:

```bash
cp .env.example .env
```

**Minimum required for full tool testing:**

```bash
# ---- Databases ----
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=agentic_ai
WEAVIATE_URL=http://localhost:8080

# ---- Search ----
NEWSLETTER_TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxx

# ---- Email ----
NEWSLETTER_RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxx
NEWSLETTER_FROM_EMAIL=newsletter@yourdomain.com
NEWSLETTER_FROM_NAME=AI Newsletter

# ---- LLM (pick one provider) ----
# Option A: Ollama (local, no API key needed)
LLM_PROVIDER=ollama
LLM_DEFAULT_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434

# Option B: Gemini
LLM_PROVIDER=gemini
LLM_DEFAULT_MODEL=gemini-2.0-flash
GEMINI_API_KEY=AIza...

# Option C: OpenAI
LLM_PROVIDER=openai
LLM_DEFAULT_MODEL=gpt-4
OPENAI_API_KEY=sk-...
```

### 2.3 Verify Backend Services

```bash
# Check MongoDB
mongosh --eval "db.runCommand({ping: 1})"

# Check Weaviate
curl http://localhost:8080/v1/.well-known/ready

# Check Ollama (if using)
curl http://localhost:11434/api/tags
```

### 2.4 Test the MCP Server Directly

Before connecting any client, verify the server starts:

```bash
cd backend
python -m app.mcp
```

You should see no errors and the process should stay running (waiting for stdio input). Press `Ctrl+C` to stop.

---

## 3. Connecting from Claude Desktop

### 3.1 Locate the Config File

| Platform | Config file path |
|----------|-----------------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |

### 3.2 Add the MCP Server Configuration

Open (or create) `claude_desktop_config.json` and add:

```json
{
  "mcpServers": {
    "agentic-ai-framework": {
      "command": "python",
      "args": ["-m", "app.mcp"],
      "cwd": "/absolute/path/to/agentic-ai-framework/backend",
      "env": {
        "NEWSLETTER_TAVILY_API_KEY": "tvly-xxxxxxxxxxxxxxxxxx",
        "NEWSLETTER_RESEND_API_KEY": "re_xxxxxxxxxxxxxxxxxx",
        "NEWSLETTER_FROM_EMAIL": "newsletter@yourdomain.com",
        "NEWSLETTER_FROM_NAME": "AI Newsletter",
        "MONGODB_URI": "mongodb://localhost:27017",
        "MONGODB_DATABASE": "agentic_ai",
        "WEAVIATE_URL": "http://localhost:8080",
        "LLM_PROVIDER": "ollama",
        "LLM_DEFAULT_MODEL": "llama3",
        "OLLAMA_BASE_URL": "http://localhost:11434"
      }
    }
  }
}
```

> **Note:** Replace `/absolute/path/to/agentic-ai-framework/backend` with the actual path on your system. The `env` block is optional if you have a `.env` file in the backend directory, but explicit env vars ensure the server always has the right configuration regardless of working directory.

### 3.3 Restart Claude Desktop

Quit and relaunch Claude Desktop. The MCP server should connect automatically.

### 3.4 Verify in Claude Desktop

In a new conversation, Claude should now show the MCP tools as available. You can ask:

> "What MCP tools are available from the agentic-ai-framework server?"

Claude should list all 16 tools. You can also check the MCP server status in Claude Desktop's developer tools (Help > Developer Tools).

---

## 4. Connecting from Windsurf

### 4.1 Open MCP Configuration

In Windsurf, open the MCP configuration:

1. Open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
2. Search for **"Windsurf: Configure MCP Servers"** (or **"MCP: Configure Servers"**)
3. This opens the MCP configuration file

Alternatively, create or edit the file directly:

| Platform | Config file path |
|----------|-----------------|
| macOS | `~/.codeium/windsurf/mcp_config.json` |
| Windows | `%USERPROFILE%\.codeium\windsurf\mcp_config.json` |
| Linux | `~/.codeium/windsurf/mcp_config.json` |

### 4.2 Add the MCP Server Configuration

```json
{
  "mcpServers": {
    "agentic-ai-framework": {
      "command": "python",
      "args": ["-m", "app.mcp"],
      "cwd": "/absolute/path/to/agentic-ai-framework/backend",
      "env": {
        "NEWSLETTER_TAVILY_API_KEY": "tvly-xxxxxxxxxxxxxxxxxx",
        "NEWSLETTER_RESEND_API_KEY": "re_xxxxxxxxxxxxxxxxxx",
        "NEWSLETTER_FROM_EMAIL": "newsletter@yourdomain.com",
        "NEWSLETTER_FROM_NAME": "AI Newsletter",
        "MONGODB_URI": "mongodb://localhost:27017",
        "MONGODB_DATABASE": "agentic_ai",
        "WEAVIATE_URL": "http://localhost:8080",
        "LLM_PROVIDER": "ollama",
        "LLM_DEFAULT_MODEL": "llama3",
        "OLLAMA_BASE_URL": "http://localhost:11434"
      }
    }
  }
}
```

### 4.3 Reload Windsurf

After saving the config, reload Windsurf:
- Use the Command Palette > **"Developer: Reload Window"**
- Or restart Windsurf entirely

### 4.4 Verify in Windsurf

In Windsurf's Cascade (AI chat), you can verify the connection:

> "List all available MCP tools from the agentic-ai-framework server"

The 16 tools should appear as available MCP tools in the Cascade panel.

---

## 5. Connecting from Claude Code

### 5.1 Project-Level Configuration (Recommended)

Create `.mcp.json` in the project root:

```json
{
  "mcpServers": {
    "agentic-ai-framework": {
      "command": "python",
      "args": ["-m", "app.mcp"],
      "cwd": "./backend"
    }
  }
}
```

Claude Code reads `.env` from the backend directory automatically when the server starts.

### 5.2 User-Level Configuration

To make the server available across all projects, add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "agentic-ai-framework": {
      "command": "python",
      "args": ["-m", "app.mcp"],
      "cwd": "/absolute/path/to/agentic-ai-framework/backend"
    }
  }
}
```

### 5.3 Verify in Claude Code

```bash
claude
# In the Claude Code session:
> /mcp
```

This lists all connected MCP servers and their tools. You should see `agentic-ai-framework` with 16 tools.

---

## 6. Verifying the Connection

Regardless of which client you use, the first step is to verify that all 16 tools are visible. Ask your AI assistant:

> "List all tools available from the agentic-ai-framework MCP server and group them by category."

**Expected response — 16 tools in 5 categories:**

| Category | Count | Tools |
|----------|-------|-------|
| search | 4 | `search__tavily_search_topic`, `search__tavily_search_topics`, `search__tavily_search_and_filter`, `search__tavily_get_trending` |
| email | 3 | `email__send_email`, `email__send_batch`, `email__check_health` |
| cache | 3 | `cache__memory_set`, `cache__memory_get`, `cache__memory_delete` |
| rag | 2 | `rag__store_newsletter`, `rag__search_similar` |
| llm | 4 | `llm__generate`, `llm__chat`, `llm__list_models`, `llm__health_check` |

---

## 7. Testing All 16 Tools

Below are prompts you can use in Claude Desktop, Windsurf, or Claude Code to test each tool. Each section includes the prompt to give the AI, the expected behavior, and what to look for in the result.

### 7.1 Search Tools (Tavily)

**Requires:** `NEWSLETTER_TAVILY_API_KEY`

#### Tool 1: `search__tavily_search_topic`

**Prompt:**
> Use the `search__tavily_search_topic` tool to search for "artificial intelligence breakthroughs" with max_results set to 3.

**Expected result:** JSON array of search results, each with title, URL, content snippet, and relevance score.

**What to verify:**
- Returns up to 3 results
- Each result has a title, url, and content field
- Results are relevant to the query

---

#### Tool 2: `search__tavily_search_topics`

**Prompt:**
> Use `search__tavily_search_topics` to search for these topics in parallel: ["quantum computing", "renewable energy"]. Set max_results_per_topic to 2.

**Expected result:** A dictionary keyed by topic name, each containing a list of search results.

**What to verify:**
- Two keys in the response: "quantum computing" and "renewable energy"
- Each key has up to 2 results
- Parallel search is faster than two sequential searches

---

#### Tool 3: `search__tavily_search_and_filter`

**Prompt:**
> Use `search__tavily_search_and_filter` with topics ["machine learning", "cybersecurity"], max_results 5, and all filters enabled (deduplicate_results=true, apply_quality=true, apply_recency=true).

**Expected result:** A filtered, deduplicated, quality-scored list of articles.

**What to verify:**
- No duplicate articles in the results
- Results are sorted by combined score (relevance + quality + recency)
- Each result has enriched metadata (quality/recency boosts applied)

---

#### Tool 4: `search__tavily_get_trending`

**Prompt:**
> Use `search__tavily_get_trending` to find trending content for topics ["AI", "climate tech"] with max_results 3.

**Expected result:** Trending articles from the last 24 hours, sorted by score.

**What to verify:**
- Results are recent (within last day or so)
- Sorted by relevance/trending score
- Content from high-quality sources

---

### 7.2 Email Tools (Resend)

**Requires:** `NEWSLETTER_RESEND_API_KEY`, `NEWSLETTER_FROM_EMAIL`

> **Warning:** These tools send real emails. Use your own email address as the recipient for testing.

#### Tool 5: `email__send_email`

**Prompt:**
> Use `email__send_email` to send a test email to "your-email@example.com" with subject "MCP Test Email" and html_content "&lt;h1&gt;Hello from MCP!&lt;/h1&gt;&lt;p&gt;This is a test email sent via the Agentic AI Framework MCP server.&lt;/p&gt;".

**Expected result:** An `EmailResult` with success=true, an email_id, and a sent_at timestamp.

**What to verify:**
- Response shows `success: true`
- An `email_id` is returned
- Check your inbox for the actual email

---

#### Tool 6: `email__send_batch`

**Prompt:**
> Use `email__send_batch` to send emails to ["your-email@example.com", "your-other-email@example.com"] with subject "MCP Batch Test" and html_content "&lt;p&gt;Batch email test from MCP.&lt;/p&gt;", batch_size 50.

**Expected result:** An `EmailBatch` with total count, sent count, failed count, and success rate.

**What to verify:**
- `total` matches number of recipients
- `success_rate` is 1.0 (or close)
- Both recipients receive the email

---

#### Tool 7: `email__check_health`

**Prompt:**
> Use `email__check_health` to verify the email service is working.

**Expected result:** Health check object with `healthy: true`, configured `from_email`, and `from_name`.

**What to verify:**
- `healthy` is `true`
- `from_email` and `from_name` match your `.env` values
- No `error` field in the response

---

### 7.3 Cache Tools (MongoDB)

**Requires:** MongoDB running at `MONGODB_URI`

#### Tool 8: `cache__memory_set`

**Prompt:**
> Use `cache__memory_set` with user_id "test-user-1", cache_type "preferences", key "favorite_topics", and value {"topics": ["AI", "robotics", "space"], "tone": "casual"}. Set ttl to 3600.

**Expected result:** `true` (boolean) indicating the value was stored.

**What to verify:**
- Returns `true`
- No errors about invalid cache_type

---

#### Tool 9: `cache__memory_get`

**Prompt:**
> Use `cache__memory_get` with user_id "test-user-1", cache_type "preferences", key "favorite_topics".

**Expected result:** The exact JSON object stored in the previous step.

**What to verify:**
- Returns `{"topics": ["AI", "robotics", "space"], "tone": "casual"}`
- Values match what was stored
- Not null/None (the TTL hasn't expired yet)

---

#### Tool 10: `cache__memory_delete`

**Prompt:**
> Use `cache__memory_delete` with user_id "test-user-1", cache_type "preferences", key "favorite_topics".

**Expected result:** `true` indicating the entry was deleted.

**Follow-up verification:**
> Now use `cache__memory_get` with the same user_id, cache_type, and key.

**Expected:** Returns `null` / `None` since the entry was deleted.

---

### 7.4 RAG Tools (Weaviate)

**Requires:** Weaviate running at `WEAVIATE_URL`

#### Tool 11: `rag__store_newsletter`

**Prompt:**
> Use `rag__store_newsletter` to store a newsletter with user_id "test-user-1", newsletter_id "nl-test-001", content "Artificial intelligence continues to reshape industries. This week, breakthroughs in large language models have enabled new applications in healthcare diagnostics, automated code generation, and scientific research. Researchers at leading labs have demonstrated models that can reason about complex multi-step problems with unprecedented accuracy.", title "AI Weekly Digest", topics ["AI", "LLMs", "healthcare"], and tone "professional".

**Expected result:** A UUID string for the stored document (e.g. `"a1b2c3d4-e5f6-..."`).

**What to verify:**
- Returns a valid UUID string (not null)
- No connection errors to Weaviate

---

#### Tool 12: `rag__search_similar`

**Prompt:**
> Use `rag__search_similar` to search for "language models and healthcare applications" with limit 5 and min_score 0.0.

**Expected result:** A list of matching newsletters with similarity scores.

**What to verify:**
- The newsletter stored in the previous step appears in results
- Each result has a uuid, score, and content metadata
- Scores are between 0.0 and 1.0
- Results ordered by similarity score (highest first)

---

### 7.5 LLM Tools

**Requires:** Configured LLM provider (`LLM_PROVIDER` + corresponding API key)

#### Tool 13: `llm__health_check`

> Start with this tool to verify LLM connectivity before testing generate/chat.

**Prompt:**
> Use `llm__health_check` to verify the LLM provider is working.

**Expected result:** `true` if the provider is reachable, `false` otherwise.

**What to verify:**
- Returns `true`
- If `false`, check your LLM provider config and API keys

---

#### Tool 14: `llm__list_models`

**Prompt:**
> Use `llm__list_models` to see what models are available.

**Expected result:** A list of model name strings.

**What to verify:**
- Returns a non-empty list
- Your configured `LLM_DEFAULT_MODEL` appears in the list (for Ollama)
- For cloud providers, lists available models in your account

---

#### Tool 15: `llm__generate`

**Prompt:**
> Use `llm__generate` with prompt "Write a 3-sentence summary of the benefits of renewable energy.", temperature 0.7, and max_tokens 200.

**Expected result:** An `LLMResponse` with generated text content, token usage stats, and model name.

**What to verify:**
- Response contains coherent, relevant text
- Token count is within the max_tokens limit
- Model name matches your configured provider

---

#### Tool 16: `llm__chat`

**Prompt:**
> Use `llm__chat` with messages [{"role": "system", "content": "You are a helpful newsletter editor."}, {"role": "user", "content": "Suggest 3 catchy subject lines for a newsletter about AI breakthroughs this week."}], temperature 0.8, max_tokens 300.

**Expected result:** An assistant response with 3 subject line suggestions.

**What to verify:**
- Response is contextually appropriate (newsletter subject lines)
- The system message was respected (editor persona)
- Response is within token limit

---

## 8. End-to-End Newsletter Workflow via MCP

This section chains multiple tools together to simulate the newsletter creation pipeline. You can give these instructions to Claude/Windsurf as a single conversation flow.

### Step 1: Health Checks

**Prompt:**
> Before we start, run health checks on all services. Use `llm__health_check` and `email__check_health` to verify everything is working.

---

### Step 2: Research Content

**Prompt:**
> Use `search__tavily_search_and_filter` to find articles on ["artificial intelligence", "quantum computing", "climate technology"] with max_results 10 and all quality filters enabled.

---

### Step 3: Cache Research Results

**Prompt:**
> Store the search results using `cache__memory_set` with user_id "newsletter-demo", cache_type "research", key "weekly-articles", and the search results as the value. Set ttl to 7200 (2 hours).

---

### Step 4: Generate Newsletter Content

**Prompt:**
> Using the search results, use `llm__chat` to generate a newsletter. Send these messages:
> - System: "You are a professional newsletter writer. Write engaging, informative content with clear section headers. Use a professional but accessible tone."
> - User: "Write a newsletter summarizing these articles: [paste top 3-5 article summaries]. Include an intro paragraph, one section per topic, and a closing thought. Keep it under 800 words."

---

### Step 5: Generate Subject Lines

**Prompt:**
> Use `llm__generate` with the prompt: "Generate 3 engaging email subject lines for a newsletter covering AI breakthroughs, quantum computing advances, and climate tech innovations this week. Format as a numbered list."

---

### Step 6: Store in RAG for Future Reference

**Prompt:**
> Use `rag__store_newsletter` to store the generated newsletter with user_id "newsletter-demo", newsletter_id "nl-demo-001", the full newsletter content, title "Weekly Tech Digest", topics ["AI", "quantum computing", "climate tech"], and tone "professional".

---

### Step 7: Send Test Email

**Prompt:**
> Use `email__send_email` to send the newsletter to "your-email@example.com" with the best subject line and the newsletter content as HTML.

---

### Step 8: Verify Everything

**Prompt:**
> Let's verify the full pipeline:
> 1. Use `cache__memory_get` to retrieve the cached research (user_id "newsletter-demo", cache_type "research", key "weekly-articles")
> 2. Use `rag__search_similar` to search for "quantum computing climate" and verify our newsletter is findable
> 3. Confirm the email was sent successfully

---

## 9. Troubleshooting

### Connection Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Server not found" in Claude Desktop | Wrong path in `cwd` | Use absolute path to `backend/` directory |
| "Command not found: python" | Python not in PATH | Use full path: `/usr/bin/python3` or venv path |
| Tools not appearing | Server crashed on startup | Run `python -m app.mcp` manually to see errors |
| "Connection refused" in Windsurf | Config file syntax error | Validate JSON in config file |
| Server starts then dies | Missing `.env` or dependencies | Check `pip install -e .` and `.env` file |

### Tool Execution Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `{"error": "NEWSLETTER_TAVILY_API_KEY not set"}` | Missing Tavily key | Set `NEWSLETTER_TAVILY_API_KEY` in `.env` or MCP `env` block |
| `{"error": "NEWSLETTER_RESEND_API_KEY not set"}` | Missing Resend key | Set `NEWSLETTER_RESEND_API_KEY` in `.env` or MCP `env` block |
| `{"error": "Connection refused"}` for cache tools | MongoDB not running | Start MongoDB: `mongod` or `docker compose up mongodb` |
| `{"error": "..."}` for RAG tools | Weaviate not running | Start Weaviate: `docker compose up weaviate` |
| `{"error": "Tool execution timed out after 60 seconds"}` | Service too slow | Check network, increase timeout in service, or check provider status |
| `{"error": "Invalid cache_type '...'"}` | Wrong cache_type string | Use one of: `preferences`, `research`, `workflow`, `session`, `engagement`, `analytics` |

### Debugging Tips

1. **Run the MCP server manually** to see real-time logs:
   ```bash
   cd backend
   python -m app.mcp 2>mcp-debug.log
   ```

2. **Check Claude Desktop logs** (macOS):
   ```bash
   tail -f ~/Library/Logs/Claude/mcp*.log
   ```

3. **Test individual tools via REST** (bypasses MCP transport):
   ```bash
   cd backend
   uvicorn app.main:app --reload

   # Test search
   curl -X POST http://localhost:8000/api/v1/tools-studio/tools/llm/health_check/try \
     -H 'Content-Type: application/json' \
     -d '{"parameters": {}}'
   ```

4. **Verify Python environment:**
   ```bash
   cd backend
   python -c "from app.mcp.server import create_mcp_server; print('OK')"
   ```

### Using Virtual Environments

If your project uses a virtual environment, update the MCP config to use the venv Python:

```json
{
  "mcpServers": {
    "agentic-ai-framework": {
      "command": "/absolute/path/to/agentic-ai-framework/backend/.venv/bin/python",
      "args": ["-m", "app.mcp"],
      "cwd": "/absolute/path/to/agentic-ai-framework/backend"
    }
  }
}
```

This ensures the MCP server uses the correct Python with all dependencies installed.
