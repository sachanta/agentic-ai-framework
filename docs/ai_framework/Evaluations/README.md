# LLM Evaluation Stack — promptfoo + Moonshot

Production-ready evaluation infrastructure for the agentic-ai-framework, built around two complementary tools:

| Tool | Role | Cadence | Owner of |
|------|------|---------|----------|
| **promptfoo** | Fast dev-loop evals, PR gates, regression tests | Per commit / per PR | Per-agent prompt + behavior contracts |
| **Moonshot** | Deep audits, curated benchmarks, red-teaming | Weekly / pre-release | Trust & safety posture, model comparisons |

The two are not redundant. promptfoo lives next to the code and fails CI when an agent regresses. Moonshot lives one layer up and answers "is this model+app safe enough to ship at all?" using IMDA's starter kit and MLCommons-style cookbooks.

## Why both?

- **promptfoo** is YAML-first, opinionated for developer ergonomics, and shines in CI. Cheap to author tests, cheap to run.
- **Moonshot** is heavier (Python 3.11 + optional web UI) but ships curated cookbooks for bias, toxicity, hallucination, jailbreak resistance, and the MLCommons AILuminate taxonomy. You get vetted test sets without authoring them.

Both will share one provider layer that wraps the project's existing `LLMProviderType` abstraction, so eval models stay in sync with what runs in `backend/app/platforms/*`.

## Phase map

Each phase has its own folder with a `spec.md`. Phases are sized so each one delivers something usable on its own.

| # | Phase | Outcome |
|---|-------|---------|
| 1 | [Foundations](./phase1-foundations/spec.md) | Both tools installed locally; you can run the canonical hello-world for each and explain what each piece does. |
| 2 | [Provider Integration](./phase2-provider-integration/spec.md) | Custom promptfoo Python provider + custom Moonshot connector that both call into `app.common.providers.llm`. One config, two tools. |
| 3 | [promptfoo Dev Loop](./phase3-promptfoo-dev-loop/spec.md) | Per-agent eval suites (`writing`, `preference`, `custom_prompt`) with assertions, golden cases, and adversarial cases. Run locally in seconds. |
| 4 | [Moonshot Audits](./phase4-moonshot-audits/spec.md) | Curated cookbooks running against your agents end-to-end. Red-team report. Baseline scores recorded. |
| 5 | [Production Hardening](./phase5-production-hardening/spec.md) | promptfoo as a required PR check; Moonshot scheduled weekly with results archived; dashboards + governance playbook. |

## Directory layout (target)

After all phases:

```
evals/
├── promptfoo/
│   ├── promptfooconfig.yaml          # root config
│   ├── providers/
│   │   └── framework_provider.py     # bridges to app.common.providers.llm
│   ├── suites/
│   │   ├── writing_agent.yaml
│   │   ├── preference_agent.yaml
│   │   └── custom_prompt_agent.yaml
│   ├── datasets/
│   └── redteam/
└── moonshot/
    ├── connectors/
    │   └── framework_connector.py
    ├── endpoints/                    # JSON endpoint configs
    ├── cookbooks/                    # custom cookbooks (project-specific)
    ├── recipes/                      # custom recipes
    └── results/                      # gitignored, archived to S3 in Phase 5
```

## How to work through the phases

1. Read the phase `spec.md` end-to-end first.
2. Check the **Learning objectives** — these are what you should be able to explain at the end.
3. Work through **Deliverables** in order. Each is independently verifiable.
4. Run the **Acceptance criteria** before moving to the next phase.
5. The **Reading list** at the bottom is for going deeper; not required to complete the phase.

## Conventions used in these specs

- Code blocks marked `# claude-implements` are blocks I will write for you.
- Code blocks marked `# you-run` are commands you should run yourself to learn the tool.
- "Pitfalls" sections list things that wasted time during research — read them before debugging.
