# GitHub Copilot Implementation Guide

This folder contains a complete 20-phase implementation plan and GitHub Copilot prompts for the Agentic AI Framework (hello_world platform).

## Contents

| File | Description |
|------|-------------|
| [SETUP-WINDOWS.md](./SETUP-WINDOWS.md) | Windows 11 installation guide |
| [project-overview.md](./project-overview.md) | Project summary, tech stack, and constraints |
| [20-phase-plan.md](./20-phase-plan.md) | Complete implementation roadmap |
| [phase-prompts/](./phase-prompts/) | Individual Copilot prompts for each phase |
| [copilot-instructions.md](./copilot-instructions.md) | **Copy to `.github/copilot-instructions.md`** |
| [claude.md](./claude.md) | Project guidance for Claude Code |

## Phase Prompts

| Phase | Title | Focus |
|-------|-------|-------|
| [01](./phase-prompts/phase-01-config.md) | Project Setup & Configuration | Backend |
| [02](./phase-prompts/phase-02-mongodb.md) | MongoDB Connection & Models | Backend |
| [03](./phase-prompts/phase-03-llm-provider.md) | LLM Provider Abstraction | Backend |
| [04](./phase-prompts/phase-04-base-agent.md) | Base Agent Implementation | Backend |
| [05](./phase-prompts/phase-05-base-chain.md) | Base Chain Implementation | Backend |
| [06](./phase-prompts/phase-06-base-orchestrator.md) | Base Orchestrator Implementation | Backend |
| [07](./phase-prompts/phase-07-greeter-agent.md) | Greeter Agent Implementation | Backend |
| [08](./phase-prompts/phase-08-service-layer.md) | Hello World Service Layer | Backend |
| [09](./phase-prompts/phase-09-api-routes.md) | Hello World API Routes | Backend |
| [10](./phase-prompts/phase-10-error-handling.md) | Backend Error Handling & Logging | Backend |
| [11](./phase-prompts/phase-11-backend-tests.md) | Backend Unit Tests | Backend |
| [12](./phase-prompts/phase-12-frontend-setup.md) | Frontend Project Setup | Frontend |
| [13](./phase-prompts/phase-13-frontend-auth.md) | Frontend Authentication | Frontend |
| [14](./phase-prompts/phase-14-api-client.md) | Frontend API Client Layer | Frontend |
| [15](./phase-prompts/phase-15-hello-world-ui.md) | Hello World UI Components | Frontend |
| [16](./phase-prompts/phase-16-frontend-state.md) | Frontend State Management | Frontend |
| [17](./phase-prompts/phase-17-frontend-error-handling.md) | Frontend Error Handling & Loading | Frontend |
| [18](./phase-prompts/phase-18-integration-tests.md) | Integration Testing | Full Stack |
| [19](./phase-prompts/phase-19-observability.md) | Observability & Metrics | Full Stack |
| [20](./phase-prompts/phase-20-documentation.md) | Documentation & Deployment | Full Stack |

## How to Use

### 0. Setup Copilot Instructions (Important!)
Copy the Copilot instructions file to your repository:
```powershell
# From project root
mkdir -p .github
cp issues/export/copilot-instructions.md .github/copilot-instructions.md
```
This tells Copilot about project conventions, patterns, and common mistakes to avoid.

### 1. Start with the Overview
Read [project-overview.md](./project-overview.md) to understand the architecture and constraints.

### 2. Follow the Phases in Order
Each phase builds on the previous. Open the corresponding prompt file and:
1. Copy the "Copilot Prompt" section
2. Paste into GitHub Copilot Chat (VS Code or JetBrains)
3. Let Copilot propose a plan
4. Review and edit the generated code
5. Run the suggested tests
6. Update `docs/implementation-log.md` with your progress

### 3. Use the Human Checklists
Each phase ends with a checklist. Complete all items before moving to the next phase.

## Tips for Working with GitHub Copilot

- **Open relevant files** before pasting the prompt so Copilot has context
- **Review all suggestions** - don't blindly accept generated code
- **Run tests frequently** - catch issues early
- **Keep changes small** - one phase at a time
- **Ask for explanations** - "Explain why you chose this approach"

## Quick Reference

### Key Files
- Backend config: `backend/app/config.py`
- LLM providers: `backend/app/common/providers/llm.py`
- Base agent: `backend/app/common/base/agent.py`
- Hello World platform: `backend/app/platforms/hello_world/`
- Frontend entry: `frontend/src/main.tsx`

### Key Conventions
- Use `AWS_BEDROCK` (not `BEDROCK`) for Bedrock provider
- Use `default_model` (not `model`) for LLM provider params
- Use `datetime.now(timezone.utc)` (not `datetime.utcnow()`)
- Use Pydantic v2 `model_config` (not `class Config`)

### Test Commands
```bash
# Backend
cd backend && .venv/bin/python -m pytest -v

# Skip integration tests
cd backend && .venv/bin/python -m pytest -m "not integration" -v
```

## Support

- See [CLAUDE.md](../../CLAUDE.md) in the project root for additional project-specific guidance
- Each phase prompt includes documentation templates for tracking progress
