# Changelog

All notable changes to the ART (Attacker-Reachable Sink Triage) Kaggle Community
Benchmark. Dates are local (2026-09-24); entries are newest-first per working
session.

## [2026-09-24] — Session 5: production hardening (code review)

### Fixed
- **ART score index alignment** (`01_label_triage`): bucket hits by evaluation
  `param_id`, not positional zip of `completed.result`; missing/errored items
  count as misses (was able to mis-bucket under `on_failure="continue"`).
- **Persona / CoT / trap scoring**: same param-id accuracy; removed soft
  `assert score >= 0` and item-level `assert_true(ok)` / CoT length gates that
  polluted assertions without changing the float metric.
- **Proof-marker**: empty provider completions explicitly return `0.0`.
- **Charts**: empty/NaN latency no longer crashes `cost_vs_art` scatter.
- Unit tests: `scripts/test_scoring_alignment.py`.

### Docs
- README notes Kaggle collection UI Pass/100 aggregation vs real `rewards.score`.

## [2026-09-24] — Session 4: v5 re-run, ablations, analysis refresh

### Ran
- Pushed adjudicated content: `art-label-triage` **v5** (v4 push ERRORED on Model
  Proxy 429 during validation; identical content re-pushed and Completed),
  `art-overconfidence-trap` **v5**, `art-proof-marker-poc` **v4**.
- Full 7-model matrix on all three core tasks; gemma proof-marker recovered after
  a 429 retry.
- Ablations published + run: `art-persona-redteam` / `art-persona-auditor`
  (flash/haiku/nano) and `art-overconfidence-cot` (haiku/sonnet).
- A4 stretch: two extra label-triage reps for the tied-top flash/gemma models
  (all COMPLETED; retained downloads show stable ART 1.0).
- Sonnet proof-marker re-run (A3): **still 0.0** — empty completion reproduces.

### Results (headline)
- Top cluster ART **0.917 → 1.000** after gold adjudication (ceiling lifted).
- Claude/nano still separate on patched twins (sonnet 0.90, haiku 0.85, nano 0.767).
- Personas do not systematically worsen patch-respect; CoT does not fix haiku trap.
- Regenerated `results/ANALYSIS_SUMMARY.md`, charts in `assets/`,
  `results/kaggle_leaderboard_v4.csv`, `results/ABLATIONS_AND_REPS.md`;
  refreshed README, DEV draft, SUGGESTIONS.

## [2026-09-24] — Session 3: contest alignment

Grounded in the DEV × Kaggle Benchmarking Challenge rules (deadline Oct 11
11:59 PM PDT; judged on Insights / Writing Quality / Creativity; official
template with sections *What I Benchmarked / Models Tested / Findings / My
Benchmark* and tags `devchallenge, kagglechallenge, ai, machinelearning`).

### Added
- `CHANGELOG.md` (this file).
- `SUGGESTIONS.md` — gap analysis against the contest judging criteria with
  per-item status tracking (done / pending / blocked-on-Kaggle-token).
- `scripts/analyze_results.py`: exact two-sided sign test over discordant
  twin pairs per model — new `twin_discordant_pairs` and `twin_sign_p`
  columns in `results/twin_gap.csv`, new "Sign p" column in
  `results/ANALYSIS_SUMMARY.md`.
- `dev/SUBMISSION_DRAFT.md` restructured onto the official template:
  - new "The itch" opening (the Iridium WP-pipeline false-positive story the
    contest explicitly rewards — "a specific itch, not a general one");
  - mechanism-first layout: twin methodology diagram + suite design now come
    before any results;
  - new "Models Tested" section arguing the lineup (tier/family spread, 50×
    price range, qwen→gemma swap);
  - new "What I'd actually wire into a triage pipeline" recommendation table;
  - probe-framing caveat slimmed and moved after the results (opens on the
    finding, qualifies immediately after);
  - new "What actually changed our thinking" lead over the adjudication
    section (the two meta-findings are now the centerpiece);
  - sign-test sentence added to the uncertainty paragraph;
  - template tags + publish-checklist comment added to the header.

## [2026-09-24] — Session 2: parser hardening, anomaly diagnosis, 7-chart set

### Fixed
- `scripts/analyze_results.py` prediction parser — the old bare-word label
  search let an explanation mentioning "safe" parse as a `safe` prediction on
  a `patched` row. Replaced with structured extraction: recursive unwrapping
  of the transcript's nested JSON-string payloads, Python-repr dicts,
  `"label": …` regex, and `label: <token>` line matches only; refuses to
  guess on prose. Every prediction is reconciled with the verifier score;
  unparseable wrong answers report `unknown`, never a guessed label.
  Unit-tested against the four transcript shapes present in downloads.
- All results regenerated with the fixed parser: true patch-overclaim rates
  restored (sonnet/haiku 0.25, nano 0.375), phantom patched→safe rows gone.
- The analysis loop's no-op model filter (condition that only `continue`d
  for qwen) replaced with a real LOCKED-membership check.

### Added / Changed
- Five new charts in `scripts/make_charts.py` → `assets/` (7 total):
  per-class heatmap, cost-vs-ART scatter (log-x, latency-sized bubbles),
  failure taxonomy bars, Wilson-CI forest plot, twin methodology diagram.
  All visually verified; label collisions fixed on scatter and dotplot.
- `results/case_studies/curated/` — hand-curated case studies survive
  regeneration (the script now purges only generated `case_*.md`); the two
  Haiku case studies moved there, stale duplicate removed.
- Curated case study 3: claude-sonnet's proof-marker 0.0 diagnosed from the
  ATIF as an **empty provider completion** (message `''`, 86 prompt tokens,
  726 ms; identical in both of its runs) — documented as an unresolved
  infrastructure anomaly, not a capability signal.
- `dev/SUBMISSION_DRAFT.md`: cost-finding paragraph, parser-hardening and
  anomaly notes; `README.md` chart documentation; walkthrough notebook now
  points at both analysis scripts.
- New labeled snapshot zip: `kaggle/art-benchmark-v4-adjudicated-20260924.zip`
  (raw `results/downloads*` excluded).

## [2026-09-24] — Session 1: v4 gold-label adjudication (the 0.9167 ceiling fix)

### Fixed
- Two items failed by **all 7 models** were re-adjudicated as ambiguous gold
  labels, not model error. Together they capped the maximum achievable ART
  score at exactly **0.9167** (the entire "tied top" cluster) and
  manufactured the largest failure-taxonomy class:
  - `safe_escape_py` (gold `safe`; escaped attacker input is `patched` by the
    prompt's own definition — "escape" was listed as a control) → replaced by
    `safe_len_py`: attacker input flows only into `len()`, unambiguous `safe`.
  - `twin_deser_py_patched` (the patch *replaced* the sink,
    `pickle.loads` → `json.loads`, which every model defensibly called
    `safe`) → keeps `pickle.loads` behind an HMAC-SHA256 `compare_digest`
    signature gate: input still reaches the sink, control on the path,
    unambiguous `patched`.
- Sharpened the four label definitions in the triage prompt (core
  `tasks/01_label_triage.py` + persona ablations `01b`/`01c`): `patched` =
  effective control on the path; `safe` = input absent or only in
  non-dangerous operations.
- Rebuilt `dataset/items.jsonl` (22 items) and re-embedded into all five
  item-carrying tasks via `scripts/embed_items.py`; `validate_jsonl.py`,
  slug checks, and compile checks pass; embedding verified byte-identical.

### Changed
- `MODELS.md` / `README.md`: `gemini-3.7-flash` documented as the 7th locked
  model (it was silently present in all result tables); run matrix updated.
- `dev/SUBMISSION_DRAFT.md` rewritten: charts embedded, diagnostic-probe
  framing, before/after adjudication story, future roadmap; stale v1-era
  score table replaced with v3 numbers.
- `results/BEFORE_AFTER_SCORING.md`: Round-2 adjudication record appended
  (item-by-item table, ceiling math, re-run status).
- `scripts/make_charts.py` created (initially 2 charts).
- Snapshot zips: `art-benchmark-audit-20260924-v4.zip` (superseded).

## Pending (publish-day only)

- DEV.to post via official template; upload `assets/*.png`; cover image; verify
  benchmark collection still attaches latest task versions.
- Optional: attach ablation tasks to the Kaggle benchmark collection UI.
