# ART analysis summary

## ART scorecard (diagnostic probe, N=8 pairs + 6 controls)

ART score = 40% vulnerable accuracy + 40% patched accuracy + 20% safe/vacuous controls.

| Model | ART | Overall | Raw | Patched | Fillers | Twin Gap | Pair consistency | Patch overclaim | Cost USD | Mean latency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `gemini-3.5-flash` | 0.917 | 0.909 | 1.000 | 0.875 | 0.833 | 0.125 | 0.875 | 0.000 | 0.0898 | 2.81s |
| `gemini-3.7-flash` | 0.917 | 0.909 | 1.000 | 0.875 | 0.833 | 0.125 | 0.875 | 0.000 | 0.0259 | 7.99s |
| `gemma-4-31b-it` | 0.917 | 0.909 | 1.000 | 0.875 | 0.833 | 0.125 | 0.875 | 0.000 | 0.0059 | 11.61s |
| `gemini-2.5-pro` | 0.883 | 0.864 | 1.000 | 0.875 | 0.667 | 0.125 | 0.875 | 0.000 | 0.1807 | 7.94s |
| `claude-sonnet-4-5-20250929` | 0.867 | 0.864 | 1.000 | 0.750 | 0.833 | 0.250 | 0.750 | 0.125 | 0.0570 | 3.34s |
| `claude-haiku-4-5-20251001` | 0.783 | 0.773 | 1.000 | 0.625 | 0.667 | 0.375 | 0.625 | 0.250 | 0.0187 | 1.68s |
| `gpt-5.4-nano-2026-03-17` | 0.750 | 0.727 | 1.000 | 0.625 | 0.500 | 0.375 | 0.625 | 0.250 | 0.0034 | 1.36s |

## Aggregate failure taxonomy

- **Over-attributed Control**: 9
- **Control Recognized, Label Drift**: 7
- **Ignored Control / Patch Overclaim**: 5
- **Vacuous vs Safe Confusion**: 2

Case studies written: 2 under `results/case_studies/`

