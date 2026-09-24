# ART analysis summary

## ART scorecard (diagnostic probe, N=8 pairs + 6 controls)

_Provenance: scored against `dataset/items.jsonl` (v4 gold) using the latest
downloaded task version under `results/downloads/art-label-triage/` (currently v6:
adjudicated items + param-id-aligned ART scoring). Predictions are parsed from ATIF
transcripts and reconciled with the verifier score; unparseable wrong answers
show as `unknown`, not as a guessed label._

ART score = 40% vulnerable accuracy + 40% patched accuracy + 20% safe/vacuous controls.

| Model | ART | Overall | Raw | Patched | Fillers | Twin Gap | Sign p | Pair consistency | Patch overclaim | Cost USD | Mean latency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `gemini-2.5-pro` | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.1811 | 7.94s |
| `gemini-3.5-flash` | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.1082 | 2.94s |
| `gemini-3.7-flash` | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.0279 | 9.08s |
| `gemma-4-31b-it` | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.0065 | 12.30s |
| `claude-sonnet-4-5-20250929` | 0.950 | 0.955 | 1.000 | 0.875 | 1.000 | 0.125 | 1.000 | 0.875 | 0.125 | 0.0599 | 3.08s |
| `claude-haiku-4-5-20251001` | 0.850 | 0.864 | 1.000 | 0.625 | 1.000 | 0.375 | 0.250 | 0.625 | 0.375 | 0.0198 | 1.72s |
| `gpt-5.4-nano-2026-03-17` | 0.817 | 0.773 | 1.000 | 0.875 | 0.333 | 0.125 | 1.000 | 0.875 | 0.125 | 0.0036 | 1.28s |

## Aggregate failure taxonomy

- **Ignored Control / Patch Overclaim**: 5
- **Vacuous vs Safe Confusion**: 3
- **Over-attributed Control**: 1

Case studies written: 2 under `results/case_studies/`

