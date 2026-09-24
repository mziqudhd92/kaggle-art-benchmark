# Ablations & repetitions (v4/v5 era) — 2026-09-24

## Task versions after this session

| Task | Version | Public |
| --- | --- | --- |
| art-label-triage | **5** (adjudicated gold; v4 push ERRORED on 429, content re-pushed as v5) | yes |
| art-overconfidence-trap | **5** | yes |
| art-proof-marker-poc | **4** | yes |
| art-persona-redteam | **1** | yes |
| art-persona-auditor | **1** | yes |
| art-overconfidence-cot | **1** | yes |

## Core leaderboard (Kaggle `rewards.score`)

### art-label-triage v5

| Model | ART |
| --- | ---: |
| gemini-2.5-pro / 3.5-flash / 3.7-flash / gemma-4-31b-it | **1.000** |
| claude-sonnet-4-5-20250929 | 0.900 |
| claude-haiku-4-5-20251001 | 0.850 |
| gpt-5.4-nano-2026-03-17 | 0.767 |

Ceiling lift vs v3: top cluster **0.917 → 1.000** after gold adjudication. Separation remains on Claude/nano patched misses.

### art-overconfidence-trap v5

| Model | Score |
| --- | ---: |
| sonnet / gemma / nano | 1.0 |
| gemini-2.5-pro / 3.5-flash / 3.7-flash | 0.875 |
| haiku | **0.5** |

### art-proof-marker-poc v4 (+ retries)

| Model | Score | Note |
| --- | ---: | --- |
| all except sonnet | 1.0 | gemma recovered after 429 retry |
| claude-sonnet | **0.0** | empty provider completion again (86 prompt tokens, `message=''`) — **reproduces**; infrastructure anomaly |

## Ablations (A2)

### Persona vs baseline ART (label-triage v5)

| Model | Baseline ART | Red-team persona | Auditor persona |
| --- | ---: | ---: | ---: |
| gemini-3.5-flash | 1.000 | **1.000** | 0.938 |
| claude-haiku | 0.850 | **0.875** | 0.750 |
| gpt-5.4-nano | 0.767 | 0.750 | **0.812** |

Takeaway: red-team persona does **not** systematically inflate patch-overclaim on this probe (haiku slightly up; nano flat/down). Auditor persona slightly hurts flash/haiku, helps nano.

### Overconfidence CoT vs baseline (trap)

| Model | Trap baseline | Forced CoT |
| --- | ---: | ---: |
| claude-haiku | 0.50 | **0.50** (no help) |
| claude-sonnet | 1.00 | **0.875** (slightly worse) |
| gemini-3.7-flash (auto) | 0.875 | 0.75 |

Takeaway: data-flow CoT did **not** close haiku's trap gap on this suite.

## A4 repetitions (top cluster)

Two extra `art-label-triage` runs for gemini-3.5-flash / gemini-3.7-flash / gemma-4-31b-it all **COMPLETED**. Kaggle download retains only the latest run per model; those latest scores are all **1.0**. Combined with the primary matrix scores also at 1.0, the tied-top cluster is **stable perfect** on v5 gold (no observed spread in retained artifacts).
