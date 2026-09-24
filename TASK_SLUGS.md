# Task decorator name ↔ CLI push slug (must match exactly)

| File | `@kbench.task(name=...)` / push slug |
| --- | --- |
| `tasks/01_label_triage.py` | `art-label-triage` |
| `tasks/01b_persona_redteam.py` | `art-persona-redteam` |
| `tasks/01c_persona_auditor.py` | `art-persona-auditor` |
| `tasks/02_proof_marker_poc.py` | `art-proof-marker-poc` |
| `tasks/03_overconfidence_trap.py` | `art-overconfidence-trap` |
| `tasks/03b_overconfidence_cot.py` | `art-overconfidence-cot` |

```bash
kaggle b t push art-label-triage -f tasks/01_label_triage.py --wait
```
