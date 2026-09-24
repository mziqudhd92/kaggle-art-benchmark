# %% [markdown]
# [Walkthrough] Evaluating LLMs on Attacker-Reachable Sinks (ART)
#
# Companion notebook for the ART Kaggle tasks.
# Tasks (public):
# - https://www.kaggle.com/benchmarks/tasks/moranzavdi/art-label-triage
# - https://www.kaggle.com/benchmarks/tasks/moranzavdi/art-proof-marker-poc
# - https://www.kaggle.com/benchmarks/tasks/moranzavdi/art-overconfidence-trap

# %%
# !pip install -q kaggle-benchmarks pandas
import json
from pathlib import Path

# On Kaggle, attach / paste a small items.jsonl or use the embedded task source.
# Locally (from repo root of art-benchmark):
items_path = Path("dataset/items.jsonl")
if items_path.exists():
    items = [json.loads(l) for l in items_path.read_text().splitlines() if l.strip()]
    print(f"loaded {len(items)} items; twin pairs:", len({i['twin_id'] for i in items if i.get('twin_id')}))
    print("showcase:", next(i["id"] for i in items if i.get("showcase")))
else:
    print("dataset/items.jsonl not found in this kernel — open the published task notebooks instead.")

# %% [markdown]
# ## How scoring works
# Each twin pair shares identical function names; only the control differs.
# Models that ace `reachable_vuln` but fail `patched` drive **Twin Gap**.
#
# ## Reproduce the analysis
# ```bash
# python scripts/analyze_results.py      # CSVs + confusion matrices + case studies
# python scripts/make_charts.py          # 7 DEV-post graphics -> assets/
# ```
# Charts: raw-vs-patched bars (Wilson CIs), top-model confusion heatmap,
# per-class heatmap, cost-vs-ART scatter, failure taxonomy, patched-CI dot
# plot, twin methodology diagram.
#
# ## CLI (local)
# ```bash
# kaggle b t run art-label-triage -m gemini-3.5-flash --wait
# kaggle b t download art-label-triage -o results -s
# ```
