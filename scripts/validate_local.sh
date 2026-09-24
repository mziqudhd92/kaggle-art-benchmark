#!/usr/bin/env bash
# Local gate: JSONL + slug match + smoke-run each core task (needs MODEL_PROXY_*).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

python scripts/validate_jsonl.py

declare -A EXPECTED=(
  [tasks/01_label_triage.py]=art-label-triage
  [tasks/01b_persona_redteam.py]=art-persona-redteam
  [tasks/01c_persona_auditor.py]=art-persona-auditor
  [tasks/02_proof_marker_poc.py]=art-proof-marker-poc
  [tasks/03_overconfidence_trap.py]=art-overconfidence-trap
  [tasks/03b_overconfidence_cot.py]=art-overconfidence-cot
)

for file in "${!EXPECTED[@]}"; do
  name="${EXPECTED[$file]}"
  if ! grep -q "@kbench.task(name=\"${name}\")" "$file"; then
    echo "SLUG MISMATCH: $file missing @kbench.task(name=\"${name}\")" >&2
    exit 1
  fi
  echo "slug ok: $file -> $name"
done

# Prompt isolation spot-check: triage must not reference twin metadata keys in prompt builders.
if grep -n 'twin_id\|twin_role\|gold_label\|rationale' tasks/01_label_triage.py | grep -v '^[^:]*:.*#' | grep -E 'prompt|f"|f'\''|format' >/dev/null 2>&1; then
  echo "WARN: inspect 01_label_triage.py for metadata leakage into prompts" >&2
fi

for task in tasks/01_label_triage.py tasks/02_proof_marker_poc.py tasks/03_overconfidence_trap.py; do
  echo "Running $task ..."
  python "$task"
done

echo "validate_local: OK"
