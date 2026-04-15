# Phase 5 — Production Hardening

**Goal:** evaluations stop being something humans remember to run. promptfoo gates every PR; Moonshot runs on a schedule; results are durable; regressions page someone.

**Estimated effort:** 6–10 hours.

## Learning objectives

1. The right set of CI signals (block, warn, info) — over-blocking trains people to ignore CI.
2. How to store eval artifacts so a future engineer can reconstruct "what did Haiku score on bias-BBQ in March 2026?"
3. The governance loop: who reviews regressions, who approves model swaps, who signs off on red-team findings.
4. Cost containment patterns when evals run unattended.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Pull Request                                                │
│  └─► promptfoo eval (changed agents only)                    │
│       ├─► PASS → merge                                       │
│       └─► FAIL → block + comment matrix on PR                │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Weekly cron (GitHub Actions)                                │
│  └─► Moonshot Standard cookbook on production endpoint       │
│       └─► Upload report to S3 + post summary to Slack        │
│            └─► If score drops > N% from baseline → page      │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Pre-release (manual trigger)                                │
│  └─► Moonshot Deep cookbook + red-team                       │
│       └─► Generates release-eval-report.pdf                  │
│            └─► Required attachment on release PR             │
└──────────────────────────────────────────────────────────────┘
```

## Deliverables

### 5.1 — promptfoo as a PR check

**File:** `.github/workflows/promptfoo-pr.yml` — *I'll implement this.*

Key design choices:

| Concern | Decision |
|---------|----------|
| Which suites run? | Only suites whose underlying agent files changed (path-filter). Full suite on `main` push. |
| Which provider? | Ollama via container (zero per-PR cost) for 80% of cases; Bedrock for ones tagged `requires-real-model`. |
| Where do results go? | Posted as a sticky PR comment via `promptfoo share` or matrix-as-markdown. |
| Caching? | promptfoo's built-in cache, keyed on prompt+input+model. Persisted to GHA cache. |
| Threshold? | Block if pass rate < baseline; warn if any individual case flips. |

Expected cost per PR run: **~\$0** (Ollama) to **~\$0.50** (with `requires-real-model` cases).

### 5.2 — Moonshot scheduled run

**File:** `.github/workflows/moonshot-weekly.yml` — *I'll implement this.*

```yaml
# claude-implements (sketch)
on:
  schedule: [{cron: '0 9 * * MON'}]
  workflow_dispatch:

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install "aiverify-moonshot[all]"
      - run: python -m moonshot -i moonshot-data
      # copy our connectors + endpoints + cookbooks into the moonshot dir
      - run: ./evals/moonshot/scripts/install-custom-assets.sh
      - run: python -m moonshot cli run-cookbook standard-suite -e framework-bedrock-haiku
      - uses: aws-actions/configure-aws-credentials@v4
      - run: aws s3 cp ./moonshot-data/results/ s3://${{ secrets.EVAL_BUCKET }}/moonshot/$(date +%F)/ --recursive
      - run: ./evals/moonshot/scripts/post-summary.sh   # to Slack
```

### 5.3 — Results storage

**Layout in S3 (or any blob store):**

```
s3://agentic-ai-evals/
├── promptfoo/
│   └── <run-id>/
│       ├── results.json
│       ├── matrix.html
│       └── manifest.json   # commit SHA, suite versions, model versions
└── moonshot/
    └── <YYYY-MM-DD>/
        ├── runs/
        ├── reports/
        └── manifest.json
```

`manifest.json` is the rosetta stone — without it, a results.json from 6 months ago is unintelligible.

**Retention policy:** infinite for `manifest.json` + headline scores; 90 days for full prompt/output dumps (often contain user data).

### 5.4 — Regression detection

**File:** `evals/scripts/check_regression.py` — *I'll implement this.*

Compares latest Moonshot scores to baseline (`BASELINE.md` from Phase 4). Triggers:

- **Page** (PagerDuty): drop ≥10% on any safety-critical recipe (toxicity, bias, jailbreak).
- **Alert** (Slack): drop ≥5% on any recipe.
- **Info** (Slack): score change ±2% — context for the team.

Run as a GHA step after every Moonshot run.

### 5.5 — Governance playbook

**File:** `evals/GOVERNANCE.md` — *you draft, I review.*

Documents:

- **Who** owns the eval stack (one named person).
- **When** baselines get refreshed (after every approved model swap).
- **How** a model swap is approved: must run Deep cookbook + red-team, must have <5% regression on safety recipes, must be reviewed by [role].
- **What** counts as a release-blocking finding from red-team (e.g. "any successful jailbreak in a HIGH severity attack module").
- **Escalation** path for a Sev-1 eval regression in production.

### 5.6 — Cost guardrails

- Per-job budget cap (GHA timeout + a `BUDGET_USD` env that the connector enforces).
- Weekly cost report: sum of token usage across all runs, posted to Slack.
- Auto-disable scheduled Moonshot run if the previous 4 runs cost > \$N total — forces a human to re-enable.

### 5.7 — Dashboard

Lightweight option: a static HTML page generated from the last 12 weeks of `manifest.json` files, deployed to S3+CloudFront. Shows score trends per recipe per endpoint.

Heavier option: ship metrics to Grafana Cloud / Datadog.

Pick one. Document the choice in `GOVERNANCE.md`.

## Acceptance criteria

- [ ] PR to a file under `backend/app/platforms/newsletter/agents/writing/` triggers `promptfoo-pr.yml` and only that agent's suite runs.
- [ ] Deliberately regressing a prompt blocks the PR.
- [ ] Weekly Moonshot workflow has run successfully at least once on a Monday.
- [ ] Results visible in S3 with valid `manifest.json`.
- [ ] A simulated 12% score drop on toxicity recipe triggers a page (test in dry-run mode first).
- [ ] `GOVERNANCE.md` exists and names an owner.
- [ ] Dashboard URL works.

## Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| PRs blocked constantly by flaky LLM-rubric | Threshold too tight, grader non-determinism | Raise rubric model size; require 2/3 reruns to fail |
| GHA workflow times out on Moonshot | Standard cookbook >6h on free runner | Use larger runner or split across matrix; or run on self-hosted runner with persistent moonshot-data |
| Bedrock costs spike | A Moonshot run got triggered on a draft cookbook | Add cost cap; require workflow_dispatch confirmation for Deep runs |
| Slack alerts ignored | Too noisy | Tighten thresholds; ensure first-line response is always one named person |
| Eval results contain PII | Moonshot stored real user inputs | Add a redaction pass in `framework_invoke.py` before logging |

## Reading list

- [GitHub Actions cost optimization](https://docs.github.com/en/billing/managing-billing-for-github-actions/about-billing-for-github-actions)
- [SRE-style alert design](https://sre.google/sre-book/practical-alerting/) — the "page only on what a human must act on now" rule applies to eval regressions too.
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework) — useful framing for `GOVERNANCE.md`.
- [Anthropic Responsible Scaling Policy](https://www.anthropic.com/responsible-scaling-policy) — example of how a serious org structures eval-driven release gates.

## Exit criteria — DONE

When this phase passes its acceptance criteria, the eval stack runs without anyone thinking about it. Your job becomes:

- Read the weekly Slack summary (5 min/week).
- Approve or deny PRs that promptfoo flagged (case-by-case).
- Refresh adversarial datasets quarterly.
- Run Deep cookbook before each release.

Anything more is yak-shaving until something breaks.
