# Phase 1 — Foundations

**Goal:** install both tools locally, run their canonical examples, and build a working mental model of what each one does (and doesn't do).

**Estimated effort:** 3–5 hours, mostly reading and clicking around the UIs.

## Learning objectives

By the end of this phase you should be able to answer:

1. What is the difference between a **prompt eval** (promptfoo) and a **benchmark run** (Moonshot)?
2. In promptfoo, what are `prompts`, `providers`, `tests`, and `assertions`? How do they compose?
3. In Moonshot, what is the relationship between a **dataset**, a **recipe**, a **cookbook**, and an **endpoint**?
4. Why does Moonshot pin Python 3.11? (Hint: PyTorch + `aiverify-test-engine` deps.)
5. When would you reach for promptfoo vs. Moonshot vs. both?

## Concepts cheat sheet

### promptfoo mental model

```
Prompt(s) × Provider(s) × Test cases  →  Outputs  →  Assertions  →  Pass/Fail + Score
```

- **Prompt**: the text/template fed to the model (can be a string, a file, or a function).
- **Provider**: the model backend (`openai:gpt-4o`, `anthropic:claude-...`, or `file://my_provider.py`).
- **Test case**: variables substituted into the prompt + the assertions to apply to the output.
- **Assertion**: machine-checkable rule (`equals`, `contains`, `llm-rubric`, `javascript`, `python`).

### Moonshot mental model

```
Dataset (inputs) + Metric (grader) + Prompt template  =  Recipe
Recipe + Recipe + ...                                 =  Cookbook
Cookbook  ×  Endpoint(s)                              =  Run  →  Report
```

- **Endpoint**: a configured connection to a model (your custom Bedrock/Ollama wrapper goes here).
- **Recipe**: one evaluation unit (e.g. "BBQ bias on age").
- **Cookbook**: a curated bundle of recipes (e.g. "MLCommons AILuminate v1.0").
- **Connector**: the Python class that knows how to call your endpoint.

## Deliverables

### 1.0 — Add gitignore entry for eval venvs

Add to repo-root `.gitignore`:

```
# Evaluation tool venvs (Moonshot, etc.)
evals/.venv-*/
```

One-time setup; future Python eval tools (e.g. `evals/.venv-ragas/`) are covered automatically.

### 1.1 — Install promptfoo

```bash
# you-run
npx promptfoo@latest --version       # quick sanity check, no install needed
npm install -g promptfoo              # global install (or use npx everywhere)
promptfoo --version
```

Then run the canonical example:

```bash
# you-run
mkdir -p /tmp/pf-hello && cd /tmp/pf-hello
promptfoo init --no-interactive
promptfoo eval                        # uses OpenAI by default — set OPENAI_API_KEY or edit config
promptfoo view                        # opens the local results UI on :15500
```

**What to notice:**
- The generated `promptfooconfig.yaml` — keep it open while reading the docs.
- The web viewer shows a matrix of prompts × providers × tests.
- Re-running `eval` is cached unless inputs change.

### 1.2 — Install Moonshot

> **Important:** Moonshot strictly requires **Python 3.11**. Do **not** install it into the project's existing `backend/.venv` if that's a different version. Use a dedicated venv under `evals/` (colocated with the code that uses it).

**Convention for this repo:** Python eval tooling gets its own venv under `evals/.venv-<tool>/`. This keeps the venv next to the code that uses it, allows multiple tools with different Python versions to coexist, and is excluded from git via a single pattern (see below). promptfoo is Node — no venv needed.

```bash
# you-run  (from repo root)
mkdir -p evals
python3.11 -m venv evals/.venv-moonshot
source evals/.venv-moonshot/bin/activate
pip install "aiverify-moonshot[all]"
python -m moonshot -i moonshot-data -i moonshot-ui   # downloads cookbooks + UI assets
python -m moonshot web                                # serves UI on :3000
```

In a second terminal, also try the interactive CLI:

```bash
# you-run
source evals/.venv-moonshot/bin/activate
python -m moonshot cli interactive
# inside the shell, try:  list cookbooks   |   list recipes   |   list endpoints
```

**Gitignore:** repo root `.gitignore` already ignores `.venv/`, but the `-moonshot` suffix wouldn't be caught — a pattern for `evals/.venv-*/` is added in 1.0 below.

**What to notice:**
- `moonshot-data/` is a separate repo Moonshot clones; this is where cookbooks and datasets live as JSON.
- The UI walks you through a guided flow: pick endpoints → pick cookbooks → run.
- `endpoints/` directory contains JSON files — connectors are referenced by name from there.

### 1.3 — Read these primary sources (in order)

1. promptfoo — [Configuration reference](https://www.promptfoo.dev/docs/configuration/guide/) (skim) and [Assertions](https://www.promptfoo.dev/docs/configuration/expected-outputs/) (read carefully).
2. Moonshot — [Concepts](https://aiverify-foundation.github.io/moonshot/) (recipes, cookbooks, endpoints).
3. AI Verify Foundation — ["Starter Kit for LLM-based App Testing"](https://aiverify-foundation.github.io/ai-verify/) — explains *why* the cookbooks are structured the way they are.

### 1.4 — Write a 1-page comparison

In `docs/ai_framework/Evaluations/phase1-foundations/notes.md` (yours, not mine), answer:

- One use case where promptfoo is the right tool and Moonshot is overkill.
- One use case where Moonshot is the right tool and promptfoo can't help.
- One use case where you'd use both.

This forces you to internalize the split before writing any code.

## Acceptance criteria

- [ ] `promptfoo eval` runs successfully against any provider you have keys for.
- [ ] `python -m moonshot web` shows the UI and at least one cookbook is listed.
- [ ] You can explain, without looking, what an "assertion" is in promptfoo and what a "recipe" is in Moonshot.
- [ ] `notes.md` is written.

## Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| `pip install aiverify-moonshot` fails on torch wheel | Python ≠ 3.11 | Use `python3.11 -m venv` explicitly |
| Moonshot UI won't start | Node < 20.11.1 | `nvm install 20.11.1 && nvm use 20.11.1` |
| `promptfoo init` writes a config that calls OpenAI you don't want | default template | Edit `providers:` to use `echo` or a local Ollama for the hello-world |
| Moonshot data download stalls | git LFS not installed | `apt install git-lfs && git lfs install` then retry `python -m moonshot -i moonshot-data` |

## Reading list (deeper)

- promptfoo: [How it works](https://www.promptfoo.dev/docs/intro/) → [Test cases](https://www.promptfoo.dev/docs/configuration/test-cases/) → [LLM-as-judge rubrics](https://www.promptfoo.dev/docs/configuration/expected-outputs/model-graded/).
- Moonshot: [Architecture diagram](https://github.com/aiverify-foundation/moonshot#architecture) → browse `moonshot-data/cookbooks/*.json` to see real recipe wiring.
- Background: ["Holistic Evaluation of Language Models" (HELM)](https://crfm.stanford.edu/helm/) — the academic ancestor of cookbook-style evaluation.

## Exit criteria → next phase

You have both tools running and a written comparison. You're now ready to make them talk to *your* models instead of OpenAI defaults — that's Phase 2.
