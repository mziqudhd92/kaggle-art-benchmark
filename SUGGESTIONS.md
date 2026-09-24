# SUGGESTIONS — DEV × Kaggle Benchmarking Challenge

Improvement plan grounded in the contest details
([announcement post](https://dev.to/devteam/join-the-kaggle-benchmarking-challenge-2500-in-prizes-for-five-winners-18ml),
[official template prefill](https://dev.to/new?prefill=---%0Atitle%3A%20%0Apublished%3A%20%0Atags%3A%20devchallenge%2C%20kagglechallenge%2C%20ai%2C%20machinelearning%0A---),
rules at `dev.to/challenges/kaggle-2026-09-23`).

**Deadline:** Oct 11, 11:59 PM PDT · **Winners:** Nov 5 · **Judged on:**
Insights Shared · Writing Quality · Creativity in Approach.

Status legend: ✅ done · 📋 pending — publish-day manual step.

## A. Insights Shared — "teach us something real"

| # | Suggestion | Status |
| --- | --- | --- |
| A1 | **v4/v5 re-run** — pushed adjudicated gold (`art-label-triage` v5, trap v5, poc v4); 7-model matrix; results+charts regenerated. Top cluster **0.917→1.000**. | ✅ |
| A2 | **Ablations** — `01b`/`01c` on flash/haiku/nano; `03b` on haiku+sonnet. Personas don't systematically inflate overclaim; CoT doesn't fix haiku trap. | ✅ |
| A3 | **Sonnet proof-marker re-run** — still 0.0 / empty completion (reproducible infra anomaly). | ✅ |
| A4 | **k≥3 reps for tied-top** — two extra label-triage runs for flash/gemma; retained scores stable at 1.0. | ✅ |
| A5 | Lead insights with the two meta-findings (gold wrong; leaderboard 0.0 = infra). | ✅ draft |
| A6 | Exact sign test over discordant twin pairs. | ✅ |

## B. Writing Quality

| # | Suggestion | Status |
| --- | --- | --- |
| B1 | Official template sections + tags. | ✅ |
| B2 | Open with the itch; Credit one-liner in footer. | ✅ |
| B3 | "Why these models" paragraph. | ✅ |
| B4 | Actionable recommendation table (v5 numbers). | ✅ |
| B5 | Caveat after findings. | ✅ |
| B6 | Cover image + chart alt text on DEV CDN. | 📋 |
| B7 | Read-through of rendered post before publish. | 📋 |

## C. Creativity in Approach

| # | Suggestion | Status |
| --- | --- | --- |
| C1 | Mechanism-first layout. | ✅ |
| C2 | Cost-vs-ART scatter. | ✅ |
| C3 | Twin design + adjudication story. | ✅ |

## D. Compliance checklist (publish day)

- [ ] 📋 Post via official template prefill (front matter + tags).
- [ ] 📋 Benchmark collection link verified against **v5** tasks (+ optional ablations attached in UI).
- [ ] 📋 All 7 `assets/*.png` uploaded to DEV CDN.
- [ ] 📋 Cover image attached.
- [ ] 📋 Published (not draft) before **Oct 11, 11:59 PM PDT**.

## Suggested order of operations (remaining)

1. 📋 Refresh nothing else in-repo — tables/charts already v5.
2. 📋 Optional: attach ablation tasks to the Kaggle benchmark collection in the UI.
3. 📋 Publish DEV post Oct 7–8 via template.
