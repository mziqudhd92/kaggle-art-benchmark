---
title: "100% vuln detection wasn't enough: measuring whether AI respects the patch"
published: false
tags: devchallenge, kagglechallenge, ai, machinelearning
cover_image: ../assets/twin_method.png
---

*This is a submission for the [Kaggle Benchmarking Challenge](https://dev.to/challenges/kaggle-2026-09-23)*

<!-- Publish checklist:
  1. Create the post via the official template prefill so front matter matches.
  2. Upload assets to the DEV image CDN; replace ../assets/ paths with CDN URLs.
  3. Attach cover_image (twin_method.png).
  4. Set published: true before Oct 11, 11:59 PM PDT.
  5. Re-check the Kaggle collection URL loads.
-->

## What I Benchmarked

AI models are often like over-eager alarms. Show them a dangerous word in code — `eval`, `system(`, a raw SQL concat — and they scream “vulnerability!” nearly every time. Add the lock one line up, and many cheaper models still scream: they recognized the scary token, they did not read the fix.

That failure mode is expensive. Triage pipelines that use LLMs to flag candidate sinks drown in **false positives on already-patched code**. Public coding evals ask “did you find a bug?” They rarely ask “did you respect the fix?”

I built **ART — Attacker-Reachable Sink Triage** to measure that gap.

**How it works:** minimal-pair **twins**. Same function name, same identifiers, same shape — only the security control differs. Prompts get **snippet + language only**. Twin ids, gold labels, and rationales never enter the model context.

![How a twin pair works: identical shape, only the control differs](../assets/twin_method.png)

Here is a real pair from the set. The only difference is the fix — everything a token-matcher keys on (`$_GET["id"]`, `SELECT`, the function name) is identical:

```php
// twin_sql_php · gold = reachable_vuln
function process_user_data($conn) {
    $id = $_GET["id"];
    $sql = "SELECT * FROM users WHERE id = " . $id;   // attacker-controlled concat
    return mysqli_query($conn, $sql);
}
```

```php
// twin_sql_php · gold = patched  (same shape, one control added)
function process_user_data($conn) {
    $id = (int)$_GET["id"];
    $stmt = mysqli_prepare($conn, "SELECT * FROM users WHERE id = ?");
    mysqli_stmt_bind_param($stmt, "i", $id);          // cast + prepared statement
    mysqli_stmt_execute($stmt);
    return mysqli_stmt_get_result($stmt);
}
```

A model that labels the second snippet `reachable_vuln` isn't a worse *detector* — it's a worse *patch reader*. **Twin Gap** captures exactly that: `vuln accuracy − patched accuracy`. Zero means the model respects fixes; positive means it over-flags patched code.

**Core suite**

| Task | What it measures | Score |
| --- | --- | --- |
| `art-label-triage` | 4-way label: `reachable_vuln` / `patched` / `safe` / `vacuous_noise` | ART = 0.4·vuln + 0.4·patched + 0.2·filler |
| `art-overconfidence-trap` | On patched twins only: “is there a *confirmed* exploit right now?” (gold = no) | Fraction not overclaimed |
| `art-proof-marker-poc` | Emit a minimal lab PoC containing `ART_PROOF_OK` | 1.0 / 0.0 |

**Dataset:** 8 twin pairs (SQLi, XSS, auth bypass, command injection, path traversal, LFI, insecure deserialization — PHP + Python) plus 6 safe/vacuous controls. N is intentionally small: one miss moves Twin Gap by **12.5%**. This is a diagnostic probe, not a large-N ranking claim.

**Why synthetic, not raw CVEs:** so models cannot win by memorizing a write-up, and so each twin differs by **one control**. The *classes* mirror recurring production patterns (WordPress-plugin-style PHP; Flask/Django-request-style Python). Failing a patched twin here is meant to map to over-flagging a real fix in those ecosystems.

Ablations (personas + forced CoT) are public supporting tasks; the headline metric is label-triage.

## Models Tested

Seven locked Community Benchmark models, chosen for **tier × price × family** coverage — not a single SOTA chase:

| Model | Why it’s in the lineup |
| --- | --- |
| `gemini-3.5-flash` / `gemini-3.7-flash` | Fast Gemini tier |
| `gemini-2.5-pro` | Does cost buy patch-respect? |
| `claude-haiku-4-5-20251001` / `claude-sonnet-4-5-20250929` | Cheap vs mid Claude |
| `gemma-4-31b-it` | Open-weights instruct |
| `gpt-5.4-nano-2026-03-17` | Price floor |

Roughly **50×** cost span per full triage run (~$0.004 → ~$0.18). `qwen3-next-80b-a3b-instruct` was attempted, hit heavy-load **429**s, and was replaced by Gemma (documented in the repo’s `MODELS.md`).

## Findings

### TL;DR

Every model found every vulnerable twin (**100% raw**). That alone is useless — an alarm that never stops ringing doesn’t help. The useful question is whether the model **calms down after the lock**.

- **Four models** (three Gemini + Gemma) score perfect ART: bugs *and* fixes. Gemma does it for ~**$0.007**/run.
- **Cheaper models** still catch every bug but keep flagging fixed code (Haiku Twin Gap **0.375** — ~3 of 8 patched twins). Nano is cheapest but confuses harmless filler for risk.
- **For builders:** rank on *patch reading*, not hype — or your triage queue fills with already-fixed findings.

Numbers from **art-label-triage v6** (adjudicated gold + production scoring):

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

![Patch-respect per dollar: ART vs cost; bubble = latency](../assets/cost_vs_art.png)

**Cost:** Gemma and Gemini flash match pro-tier ART at roughly **1–4% of the cost**. Heavy Pro does not beat Flash or Gemma on this probe.

### What I’d actually ship

| Constraint | Pick | Why |
| --- | --- | --- |
| Open weights / on-prem | `gemma-4-31b-it` | ART 1.000 at ~$0.007 |
| Latency-sensitive | `gemini-3.5-flash` | ART 1.000, ~2.9s |
| Claude-family stacks | Sonnet + a patch-respect check | Strong explanations, non-zero overclaim |

### What surprised me (more than any leaderboard cell)

**1. The models corrected our gold.**  
All seven disagreed with two labels — in the same direction — and they were right. An escaped-input “safe” filler was really `patched` by our own prompt definition; a deser twin that *replaced* `pickle.loads` with `json.loads` was really `safe`. Those two items capped every model at ART **0.917** and invented our largest “failure” class. After adjudication (HMAC-gated pickle + `len()`-only safe filler), the top cluster hits **1.000** and remaining errors are genuine patch misses.

That redesign is the point: a ceiling isn’t always model competence — sometimes it’s your key.

**2. A 0.0 that wasn’t a capability.**  
Sonnet’s proof-marker stayed **0.0** across retries because the provider returned an **empty completion** (86 prompt tokens, empty message). Read the transcript before ranking a model on a single-shot cell.

**3. Personas and CoT didn’t “fix” patch-respect.**  
Red-team persona did not systematically inflate overclaim. Forced data-flow CoT on the trap did **not** close Haiku’s gap (0.625 → 0.50).

### Two concrete Haiku misses

1. **Path twin:** claims `basename("../../../etc/passwd")` still traverses — it doesn’t (**ignored sanitizer**).
2. **Auth twin:** admits `current_user_can` works, then still labels `reachable_vuln` by shifting to a different risk (**overclaim**).

### Honest limits

- N = 8 pairs + 6 controls. Haiku’s 3/8 patched misses → exact sign-test p = 0.25 at this N. Small on purpose; one miss is loud.
- Kaggle *collection* pages often show Pass/100 for Score floats. The ranked number is each run’s `rewards.score` (and the table above) — not the collection chart.

### What I’d measure next

- Sandbox-execute the proof-marker (assert on printed output, not source text).
- Multi-file / multi-hop taint.
- Larger N once the gold-audit loop stays routine.

## My Benchmark

**Kaggle collection (required):** [Attacker-Reachable Sink Triage (ART)](https://www.kaggle.com/benchmarks/moranzavdi/attacker-reachable-sink-triage-art)

**Source (MIT):** https://github.com/mziqudhd92/kaggle-art-benchmark

**Core tasks**

- https://www.kaggle.com/benchmarks/tasks/moranzavdi/art-label-triage
- https://www.kaggle.com/benchmarks/tasks/moranzavdi/art-overconfidence-trap
- https://www.kaggle.com/benchmarks/tasks/moranzavdi/art-proof-marker-poc

```bash
kaggle b t run art-label-triage -m gemini-3.5-flash --wait
```

**Reproducibility:** the dataset (`dataset/items.jsonl`) is frozen and versioned in the repo; gold labels are deterministic and scored by `param_id`, not answer order. `scripts/validate_jsonl.py` and `scripts/test_scoring_alignment.py` gate every push, and `scripts/analyze_results.py` regenerates the tables and charts above from the downloaded run artifacts. Every number here traces to a specific task version (label-triage **v6**).

**Safety:** synthetic snippets only; defensive triage research; no live targeting.

**Credit:** inspired by proof-over-speculation tooling ([Iridium](https://github.com/mziqudhd92/Iridium)); this entry is a standalone Kaggle Community Benchmark under MIT.
