---
title: "Attacker-Reachable Sink Triage (ART): models find vulns — then flinch on the patch"
published: false
tags: devchallenge, kagglechallenge, ai, machinelearning
cover_image: ../assets/twin_method.png
---

*This is a submission for the [Kaggle Benchmarking Challenge](https://dev.to/challenges/kaggle-2026-09-23)*

<!-- Publish checklist:
  1. Create the post via the official template prefill so front matter matches.
  2. Upload all assets/*.png to the DEV image CDN and replace relative paths.
  3. Attach cover_image (twin_method.png works).
  4. Set published: true before Oct 11, 11:59 PM PDT.
  5. Re-check the Kaggle benchmark collection URL still loads.
-->

## What I Benchmarked

I built **ART — Attacker-Reachable Sink Triage**: a small diagnostic probe that asks whether LLMs can tell a **reachable vulnerability** from its **patched twin**, from **safe** code, and from **vacuous noise** (dangerous-looking text that only lives in a comment, a dead branch, or a string).

The itch is practical. Triage pipelines that use LLMs to flag candidate sinks drown in **false positives on already-patched code**: the model spots `system(`, skips the `escapeshellarg()` one line up, and files a report nobody needed. Public coding leaderboards measure “did you find a bug?” They rarely measure “did you respect the fix?”

ART’s mechanism is **minimal-pair twins**: same function name, same identifiers, same shape — only the security control differs. Prompts receive **snippet + language only**; twin ids, gold labels, and rationales never enter the model context.

![How a twin pair works: identical shape, only the control differs; prompts see snippet + language only](../assets/twin_method.png)

**Suite (core):**

| Task | What it measures | Score |
| --- | --- | --- |
| `art-label-triage` | 4-way label: `reachable_vuln` / `patched` / `safe` / `vacuous_noise` | ART = 40% vuln + 40% patched + 20% filler accuracy |
| `art-overconfidence-trap` | On patched twins only: “is there a *confirmed* exploit right now?” (gold = no) | Fraction not overclaimed |
| `art-proof-marker-poc` | Emit a minimal lab PoC containing `ART_PROOF_OK` (proof over speculation) | 1.0 / 0.0 |

Dataset: **8 twin pairs** (SQLi, XSS, auth bypass, command injection, path traversal, LFI, insecure deserialization — PHP + Python) plus **6 controls**. N is intentionally small: one misclassification moves Twin Gap by **12.5%**. This is a targeted qualitative probe, not a large-N significance claim.

**Real-world grounding (why synthetic, not raw CVEs):** Snippets are strictly synthetic so models cannot win by memorizing a published write-up, and so each twin differs by **one control** rather than multi-file framework noise. The *classes* are not arbitrary toys — they mirror recurring production CVE patterns (e.g. WordPress-plugin-style PHP SQLi / capability-gated option writes / LFI includes; Flask- or Django-request-style Python SQLi, path traversal, and insecure `pickle` deserialization). Failing a patched twin here is meant to map to the same failure mode as over-flagging a real fix in those ecosystems.

**Ablations (also public):** red-team vs auditor personas (`art-persona-redteam`, `art-persona-auditor`) and forced data-flow CoT on the trap (`art-overconfidence-cot`).

## Models Tested

Seven locked Community Benchmark models, chosen for spread on the axes that matter for triage — not for chasing a single SOTA slug:

| Model | Tier | Why |
| --- | --- | --- |
| `gemini-3.5-flash` | flash | Primary fast Gemini |
| `gemini-3.7-flash` | flash | Second Gemini flash (auto-selected on push; kept locked) |
| `gemini-2.5-pro` | heavy | Strong Gemini baseline — does cost buy patch-respect? |
| `claude-haiku-4-5-20251001` | flash | Cheap Claude |
| `claude-sonnet-4-5-20250929` | mid | Strong Claude / explanation quality |
| `gemma-4-31b-it` | mid | Open-weights instruct |
| `gpt-5.4-nano-2026-03-17` | flash | Nano / price floor |

Family coverage: Google, Anthropic, OpenAI, and open weights. Price span is roughly **50×** per full triage run (~$0.004 nano → ~$0.18 pro).

`qwen3-next-80b-a3b-instruct` was attempted during the lock window but returned heavy-load **429**s on all three core tasks; it was replaced by `gemma-4-31b-it` and the swap is documented in `MODELS.md`.

## Findings

All seven models scored **100% raw vuln detection**. ART separates them on **patched twins and controls** — exactly the failure mode the probe was built for.

Numbers below are from **art-label-triage v6** (adjudicated gold + production scoring). ART = `0.4·raw + 0.4·patched + 0.2·filler`.

| Model | ART | Raw | Patched | Controls | Twin Gap | Cost USD | Latency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `gemini-2.5-pro` | **1.000** | 1.000 | 1.000 | 1.000 | 0.000 | 0.181 | 7.9s |
| `gemini-3.5-flash` | **1.000** | 1.000 | 1.000 | 1.000 | 0.000 | 0.108 | 2.9s |
| `gemini-3.7-flash` | **1.000** | 1.000 | 1.000 | 1.000 | 0.000 | 0.028 | 9.1s |
| `gemma-4-31b-it` | **1.000** | 1.000 | 1.000 | 1.000 | 0.000 | 0.007 | 12.3s |
| `claude-sonnet-4-5-20250929` | 0.950 | 1.000 | 0.875 | 1.000 | 0.125 | 0.060 | 3.1s |
| `claude-haiku-4-5-20251001` | 0.850 | 1.000 | 0.625 | 1.000 | **0.375** | 0.020 | 1.7s |
| `gpt-5.4-nano-2026-03-17` | 0.817 | 1.000 | 0.875 | 0.333 | 0.125 | 0.004 | 1.3s |

![Raw vs patched twin accuracy with Wilson 95% CIs](../assets/raw_vs_patched_accuracy.png)

**Headline:** cheaper/faster models are not “worse at finding sinks” — they are worse at **respecting the patch**. Heavy Gemini Pro does not beat Flash or Gemma here (all four top models are perfect on this probe).

![Patch-respect per dollar: ART vs cost (log), bubble = latency](../assets/cost_vs_art.png)

**Cost finding:** `gemma-4-31b-it` and the Gemini flash tier match pro-tier ART at roughly **1–4% of the cost**.

### What I’d wire into a triage pipeline

| Constraint | Pick | Why |
| --- | --- | --- |
| Open weights / on-prem | `gemma-4-31b-it` | ART 1.000 at ~$0.007/run |
| Latency-sensitive | `gemini-3.5-flash` | ART 1.000, ~2.9s mean |
| Claude-family stacks | `claude-sonnet` + a patch-respect guardrail | Strong explanations, but still a non-zero patch-overclaim rate |

### Ablations

| Model | Baseline ART | Red-team persona | Auditor persona |
| --- | ---: | ---: | ---: |
| `gemini-3.5-flash` | 1.000 | 1.000 | 1.000 |
| `claude-haiku` | 0.850 | 0.875 | 0.938 |
| `gpt-5.4-nano` | 0.817 | 0.688 | 0.938 |

Red-team persona did **not** systematically inflate patch-overclaim. Forced data-flow CoT on the overconfidence trap did **not** close haiku’s gap (trap 0.625 → CoT 0.50).

### What actually changed our thinking

Two build moments taught more than any leaderboard cell:

1. **All seven models disagreed with two gold labels — in the same direction — and the models were right.** An escaped-input “safe” filler was really `patched` by our own prompt definition; a deser twin that *replaced* `pickle.loads` with `json.loads` was really `safe`. Those two items capped every model at ART **0.917** and faked our largest failure class. After adjudication (HMAC-gated pickle + `len()`-only safe filler), the top cluster reaches **1.000** and remaining errors are genuine patch misses.

2. **A leaderboard 0.0 that wasn’t a capability.** Sonnet’s proof-marker score is **0.0** across retries because the provider returned an **empty completion** (86 prompt tokens, empty message). Single-shot 0/1 cells are noise until you read the transcript.

![Failure taxonomy after gold adjudication](../assets/failure_taxonomy.png)

**Honest uncertainty:** N=8 pairs + 6 controls. An exact sign test on discordant twin pairs: haiku’s 3/8 patched misses gives p = 0.25 at this N. The probe framing isn’t humility — it’s arithmetic.

**Note on the Kaggle collection UI:** multi-task collection pages currently aggregate Score floats as Pass/Fail (Overall ≈ % tasks completed), so the collection chart can look flat at 100. The ranked metric is the ART float in each run’s `rewards.score` and in the tables above.

### Code vs thought (Haiku)

1. **Path twin:** Haiku claims `basename("../../../etc/passwd")` still traverses — it does not; gold `patched` is correct (**Ignored Sanitizer**).
2. **Auth twin:** Haiku admits `current_user_can` works, then still labels `reachable_vuln` by shifting to a different risk (**overclaim**).

### What I’d measure next

- Dynamic sandbox execution for the proof-marker (assert on printed output, not source text).
- Multi-file / multi-hop taint (controller → service → DAO).
- Language expansion (C/C++ memory-safety, Rust/Go concurrency).
- Larger N once the gold-audit loop is routine.

## My Benchmark

**Required link:** [Attacker-Reachable Sink Triage (ART)](https://www.kaggle.com/benchmarks/moranzavdi/attacker-reachable-sink-triage-art)

**Source code (MIT):** https://github.com/mziqudhd92/kaggle-art-benchmark

Public tasks:

- https://www.kaggle.com/benchmarks/tasks/moranzavdi/art-label-triage
- https://www.kaggle.com/benchmarks/tasks/moranzavdi/art-proof-marker-poc
- https://www.kaggle.com/benchmarks/tasks/moranzavdi/art-overconfidence-trap
- https://www.kaggle.com/benchmarks/tasks/moranzavdi/art-persona-redteam
- https://www.kaggle.com/benchmarks/tasks/moranzavdi/art-persona-auditor
- https://www.kaggle.com/benchmarks/tasks/moranzavdi/art-overconfidence-cot

Try it yourself:

```bash
kaggle b t run art-label-triage -m gemini-3.5-flash --wait
```

### Safety

All snippets are **synthetic**, for defensive triage research only. No real plugin zips, no targeting of live systems.

### Credit

Inspired by proof-over-speculation tooling (Iridium); this entry is a standalone Kaggle Community Benchmark.
