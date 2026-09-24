# Before / after: ART float scoring (2026-09-24)

## Change

| | Before (soft-assert era) | After (ART float return) |
| --- | --- | --- |
| Task versions | label-triage v1; trap ≤v3; proof ≤v2 | **label-triage v3**, **overconfidence v4**, **proof-marker v3** |
| Parent return | soft `assert ≥ 0` → Kaggle shows **PASS / 100** for all completing models | `return float` ART score = `0.4·raw + 0.4·patched + 0.2·filler` |
| Leaderboard utility | Flat — cannot rank | Ranked floats in `[0,1]` |
| Rewards payload | Component metrics only (`raw_vuln_accuracy`, …) | Primary `rewards.score` (ART) |

## Kaggle leaderboard — Task 1 `art-label-triage`

| Model | Before (UI) | After v3 `rewards.score` | Δ meaning |
| --- | ---: | ---: | --- |
| gemini-3.5-flash | PASS / 100 | **0.917** | Now ranked (tied top) |
| gemini-2.5-pro | PASS / 100 | **0.917** | Now ranked (tied top; filler improved vs prior run) |
| gemma-4-31b-it | PASS / 100 | **0.917** | Now ranked (tied top) |
| claude-sonnet-4-5-20250929 | PASS / 100 | **0.817** | Separated from top cluster |
| claude-haiku-4-5-20251001 | PASS / 100 | **0.783** | Separated |
| gpt-5.4-nano-2026-03-17 | PASS / 100 | **0.683** | Clear bottom on fillers |

Local offline ART from item ATIFs matches Kaggle `rewards.score` exactly (v3).

## Task 2 / Task 3 (v3 / v4)

| Model | Overconfidence trap | Proof-marker PoC |
| --- | ---: | ---: |
| gemini-3.5-flash | 1.0 | 1.0 |
| gemini-2.5-pro | 1.0 | 1.0 |
| gemma-4-31b-it | 1.0 | 1.0 |
| gpt-5.4-nano | 1.0 | 1.0 |
| claude-haiku | **0.75** | 1.0 |
| claude-sonnet | 1.0 | **0.0** |

Diagnostic takeaway: ranking signal is dominated by **Task 1 twin/patched + filler**; Task 2/3 mostly saturated except haiku trap miss and sonnet proof-marker miss.

## Offline twin-gap delta (v1 ATIF analysis → v3 ATIF analysis)

| Model | ART before→after | Twin gap before→after | Notes |
| --- | --- | --- | --- |
| gemini-3.5-flash | 0.917 → 0.917 | 0.125 → 0.125 | Stable top |
| gemma-4-31b-it | 0.917 → 0.917 | 0.125 → 0.125 | Stable top |
| gemini-2.5-pro | 0.883 → **0.917** | 0.125 → 0.125 | Filler 0.667→0.833 |
| claude-sonnet | 0.867 → **0.817** | 0.250 → **0.375** | Patched 0.75→0.625 |
| claude-haiku | 0.783 → 0.783 | 0.375 → 0.375 | Stable |
| gpt-5.4-nano | 0.750 → **0.683** | 0.375 → 0.375 | Filler 0.50→0.17 |

Raw vuln accuracy remains **1.000** for all locked models — the probe still separates on **patched + controls**, not raw detection.

## Artifacts

- `results/before_soft_assert/` — snapshot of pre-rerun ANALYSIS_SUMMARY
- `results/kaggle_leaderboard_v3.csv` — Kaggle `rewards.score` by task/model
- `results/ANALYSIS_SUMMARY.md` — regenerated from v3 downloads
- Public tasks: [label-triage/3](https://www.kaggle.com/benchmarks/tasks/moranzavdi/art-label-triage/3), [trap/4](https://www.kaggle.com/benchmarks/tasks/moranzavdi/art-overconfidence-trap/4), [poc/3](https://www.kaggle.com/benchmarks/tasks/moranzavdi/art-proof-marker-poc/3)
- Benchmark: https://www.kaggle.com/benchmarks/moranzavdi/attacker-reachable-sink-triage-art

## Round 2 (v4): gold-label adjudication — 2026-09-24

**Trigger:** two items were failed by *all 7 models* — a label smell, not a model smell. Together they capped the max achievable ART at exactly **0.9167** (the entire "tied top" cluster) and produced the largest failure-taxonomy class ("Over-attributed Control": 8 of 25 errors).

| Item | v3 gold | Every model said | Why the models were defensible | v4 resolution |
| --- | --- | --- | --- | --- |
| `safe_escape_py` | `safe` | `patched` | Attacker input reaches an output sink, closed by `html.escape` — the prompt itself listed "escape" as a `patched` control | replaced by `safe_len_py`: attacker input flows only into `len()`, no sink at all → unambiguous `safe` |
| `twin_deser_py_patched` | `patched` | `safe` | Patch **replaced** the sink (`pickle.loads` → `json.loads`); by the prompt's definition, no attacker path to a *dangerous* sink is `safe` | patched side keeps `pickle.loads` behind an HMAC-SHA256 `compare_digest` gate → input still reaches the sink, control on path → unambiguous `patched` |

Also sharpened the four label definitions in the triage prompt (core + both persona ablations): `patched` = control *on the path* to the sink; `safe` = input absent or only in non-dangerous operations.

**Status (updated after re-run):** pushed as **art-label-triage v5** (v4 validation ERRORED on Model Proxy 429; content identical, re-pushed successfully). 7-model matrix + ablations completed. Top cluster ART **1.000** (ceiling lifted); Claude/nano still separate on patched twins. See `results/ANALYSIS_SUMMARY.md` and `results/ABLATIONS_AND_REPS.md`.

## Round 3 (2026-09-24): v5 re-run + ablations + sonnet proof retry

| Model | v3 ART | v5 ART | Δ |
| --- | ---: | ---: | --- |
| gemini-2.5-pro / 3.5-flash / 3.7-flash / gemma-4-31b | 0.917 | **1.000** | +0.083 (ceiling removed) |
| claude-sonnet | 0.817 | **0.900** | +0.083 |
| claude-haiku | 0.783 | **0.850** | +0.067 |
| gpt-5.4-nano | 0.683 | **0.767** | +0.084 |

Sonnet proof-marker **0.0 reproduced** (empty completion). Ablations: CoT did not help haiku trap (0.5→0.5); personas did not systematically worsen patch-respect.


## Round 4 (production hardening) — 2026-09-24

Code-review fixes pushed as **art-label-triage v6**, trap v6, proof v5, personas/cot v2.

| Model | v5 ART | v6 ART |
| --- | ---: | ---: |
| gemini / gemma top | 1.000 | 1.000 |
| claude-sonnet | 0.900 | **0.950** |
| claude-haiku | 0.850 | 0.850 |
| gpt-5.4-nano | 0.767 | **0.817** |

Kaggle collection UI still shows Pass/100 (platform Score aggregation). Ranked metric remains `rewards.score` / offline ART tables.
