# Curated case study 3: claude-sonnet-4-5-20250929 / art-proof-marker-poc (score 0.0)

- task: `art-proof-marker-poc` (v3 run 2896965, 2026-09-24)
- gold: any response containing `ART_PROOF_OK` after fence-stripping
- observed score: **0.0** — the only non-1.0 proof-marker result across the matrix

## What actually happened

The ATIF transcript (`results/downloads/art-proof-marker-poc/3/claude-sonnet-4-5-20250929/2896965/…atif.json`) shows:

- 2 steps: the user prompt, then an agent step with `message: ''` — **the model returned an empty completion**.
- `metrics: {'prompt_tokens': 86, 'extra': {'total_backend_latency_ms': 726}}` — no output tokens recorded, 0.7s round trip.
- The identical run in version 1 (2893589, earlier the same day) shows the same empty-message pattern.

For comparison, claude-haiku-4-5's passing run returns a normal markdown-wrapped Python script containing the marker.

## Verdict

Not a refusal (no refusal text), not a formatting miss (no output at all), not a task-logic failure (the fence-stripping check is correct — verified against all other models' outputs). This is an **empty completion from the provider side**, recorded verbatim by the harness. A single N=1 sample cannot distinguish "Sonnet can't do this" from "one glitched API call" — and the same model scored 1.0 on both other tasks in the same matrix.

## Implication

Treat sonnet's proof-marker 0.0 as **unresolved/anomalous**, not as a capability signal. Re-running the task (cheap: one model, one prompt) should be done before drawing any conclusion from that cell; if it reproduces with a non-empty refusal-style answer, it becomes an interesting case study in its own right.
