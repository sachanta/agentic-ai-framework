# Phase 4 — Moonshot Audits

**Goal:** run curated cookbooks against your endpoints, capture a baseline trust & safety report, and add one project-specific cookbook tailored to newsletter agents.

**Estimated effort:** 6–8 hours (most of it run-time, not authoring).

## Learning objectives

1. How to read a Moonshot report — what each metric means and what a "passing" score looks like for *your* risk tolerance.
2. The difference between **benchmarking** (graded against a dataset) and **red-teaming** (adversarial probing) inside Moonshot.
3. How to author a custom recipe and bundle it into a custom cookbook.
4. Why MLCommons AILuminate is a defensible baseline for "we did due diligence" claims.

## Cookbook strategy

Pick a **tiered** approach:

| Tier | Purpose | When to run |
|------|---------|-------------|
| **Smoke** (~5 min) | Sanity check the endpoint works end-to-end | Every time we add a new model |
| **Standard** (~30 min) | Trust & safety baseline — bias, toxicity, hallucination | Weekly + before release |
| **Deep** (~hours) | MLCommons AILuminate full sweep + red-team | Quarterly + before major model swap |

Cookbook selections (concrete recommendations — confirm versions in your installed `moonshot-data`):

- **Smoke**: `cookbook-common-risk-easy` or whichever 2–3 recipe quick cookbook ships with `moonshot-data`.
- **Standard**: `mlcommons-ai-safety-benchmarks-v0.5` (or current minor), plus `bias-bbq-lite`, `toxicity-realtoxicityprompts-sample`.
- **Deep**: `mlcommons-ailuminate-v1` full + `cybersec-cyberseceval` + your custom newsletter cookbook (3.4 below).

## Deliverables

### 4.1 — Endpoints registered

From Phase 2 you already have one connector. Now register multiple endpoints — at minimum:

- `framework-bedrock-haiku` (the production candidate)
- `framework-bedrock-sonnet` (the comparison upgrade target)
- `framework-ollama-llama3` (the local fallback)

Comparing 3 endpoints across the same cookbook is where Moonshot earns its keep — you'll see, e.g., that Sonnet beats Haiku on bias-BBQ by 12 points but is 4× slower.

### 4.2 — Run the smoke cookbook

```bash
# you-run
source ~/venvs/moonshot/bin/activate
python -m moonshot cli interactive
> run cookbook ["smoke-cookbook-name"] -e ["framework-bedrock-haiku"]
> view runs
> view report <run-id>
```

Verify the report renders, then archive the run JSON to `evals/moonshot/results/baseline-smoke-<date>.json`.

### 4.3 — Run the standard cookbook

Same flow, longer wait. Expect the run to take 20–40 min depending on model latency.

**What to inspect in the report:**

- **Per-recipe scores** — which categories the model is weakest in.
- **Failed prompts** (Moonshot stores examples) — read 5–10 of them. Are the failures "fair" or grading artifacts?
- **Cost** — Moonshot tracks tokens; multiply by Bedrock pricing to know what each future audit costs.

### 4.4 — Author a custom newsletter cookbook

This is the part that makes Moonshot project-specific instead of off-the-shelf.

```
evals/moonshot/recipes/
├── newsletter-no-fabrication.json     # uses your real article corpus
├── newsletter-tone-control.json       # asks for tones, grades adherence
└── newsletter-injection-resistance.json  # the injection cases from Phase 3, recast as a recipe

evals/moonshot/cookbooks/
└── newsletter-app-suite.json          # bundles the three above
```

A recipe needs:

- A **dataset** (JSON): list of `{input, target}` records.
- A **metric**: existing one from `moonshot-data/metrics/` or a custom one (Python class).
- A **prompt template**: how to wrap each input.
- A **grading scale**: how scores map to pass/warn/fail.

I will author the JSON and any custom metric; you review the dataset for realism.

### 4.5 — Run red-team

Moonshot's red-team mode is interactive — it sends adversarial prompts and you (or an LLM judge) flag which got through.

```bash
# you-run
> run red-teaming framework-bedrock-haiku
# pick an attack module (e.g. "violent-durable")
# Moonshot streams attacks; you mark hits
```

Output: a red-team report archived next to the cookbook results.

### 4.6 — Document the baseline

Create `evals/moonshot/BASELINE.md` with:

- Date, models tested, cookbook versions
- Headline scores per recipe per endpoint
- Known weaknesses & the team's risk acceptance ("Haiku scores 0.62 on BBQ-age; we accept this because newsletter use case doesn't surface age-sensitive content")
- The bar: which scores would block a release

This document is the artifact you show to a security reviewer.

## Acceptance criteria

- [ ] All three endpoints registered and visible in `list endpoints`.
- [ ] Smoke cookbook run completes against all three.
- [ ] Standard cookbook run completes against the production candidate; report saved.
- [ ] Custom `newsletter-app-suite` cookbook runs and produces a report.
- [ ] One red-team session run; report archived.
- [ ] `BASELINE.md` written and committed.

## Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| Custom recipe not found | JSON schema mismatch with installed Moonshot version | Validate against `moonshot/src/storage/recipe.py` schema; copy from a working recipe |
| Cookbook run hangs | Connector swallows exceptions silently | Add logging in `framework_connector.py`; check `max_concurrency: 1` while debugging |
| Bedrock throttling errors mid-run | `max_calls_per_second` too high | Drop to `2`; Moonshot retries, but burning quota mid-cookbook is wasteful |
| Bias/toxicity scores look "too good" | Datasets are old and model has memorized them | Note this in BASELINE.md; lean on custom cookbook for real signal |
| Report HTML won't open | Moonshot UI not running | `python -m moonshot web` then re-open report from UI |

## Cost reality check

A single Standard cookbook run against one Bedrock Sonnet endpoint can be **\$5–\$30** in tokens depending on which cookbooks are bundled. Read the cookbook JSON before running — count `num_of_prompts` × estimated output tokens. Run smoke first, always.

## Reading list

- [Moonshot CLI command reference](https://aiverify-foundation.github.io/moonshot/user_guide/cli/) — exact command names change between releases; check the version you installed.
- [MLCommons AILuminate v1.0 paper](https://mlcommons.org/benchmarks/ailuminate/) — explains the taxonomy you're scoring against.
- [Anthropic's red-teaming guidance](https://www.anthropic.com/research/red-teaming-language-models-with-language-models) — useful framing for what makes a red-team useful vs. theatrical.

## Exit criteria → next phase

You have a baseline report and a custom cookbook. Phase 5 makes both tools run automatically, archive results, and gate releases.
