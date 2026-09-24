#!/usr/bin/env python3
"""Analyze ART downloads: twin gap, confusion matrices, taxonomy, case studies."""

from __future__ import annotations

import csv
import ast
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = ROOT / "results" / "downloads" / "art-label-triage"
ITEMS_PATH = ROOT / "dataset" / "items.jsonl"
OUT = ROOT / "results"
LABELS = ["reachable_vuln", "safe", "vacuous_noise", "patched"]

# Human-only class tags for write-up (never sent to models).
VULN_CLASS = {
    "twin_sql_php": "sqli",
    "twin_xss_php": "xss",
    "twin_auth_php": "auth_bypass",
    "twin_cmd_php": "cmdi",
    "twin_sql_py": "sqli",
    "twin_path_py": "path_traversal",
    "twin_lfi_php": "lfi",
    "twin_deser_py": "insecure_deser",
}

LOCKED = {
    "gemini-3.5-flash",
    "gemini-3.7-flash",
    "gemini-2.5-pro",
    "claude-haiku-4-5-20251001",
    "claude-sonnet-4-5-20250929",
    "gemma-4-31b-it",
    "gpt-5.4-nano-2026-03-17",
}

TIERS = {
    "gemini-3.5-flash": "flash",
    "gemini-3.7-flash": "flash",
    "gemini-2.5-pro": "heavy",
    "claude-haiku-4-5-20251001": "flash",
    "claude-sonnet-4-5-20250929": "mid",
    "gemma-4-31b-it": "mid",
    "gpt-5.4-nano-2026-03-17": "flash",
}


def load_items() -> list[dict]:
    rows = []
    with ITEMS_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    for row in rows:
        tid = row.get("twin_id")
        row["vuln_class"] = VULN_CLASS.get(tid, "filler")
    return rows


LABEL_VARIANT_RE = [
    # canonical JSON: "label": "patched"
    re.compile(r'"label"\s*:\s*"(reachable_vuln|safe|vacuous_noise|patched)"'),
    # schema-ish: label=patched / label: patched (single tokens only, no prose)
    re.compile(r'\blabel\s*[=:]\s*"?(reachable_vuln|safe|vacuous_noise|patched)"?\s*$'),
]


def _extract_label(text: str, depth: int = 0) -> str | None:
    """Pull the predicted label out of one agent message.

    Transcripts may nest the payload several times (JSON string containing a
    JSON object, Python-repr dicts). Returns None when unambiguous extraction
    fails — callers reconcile against the verifier score instead of guessing.
    """
    if depth > 4 or not text or not text.strip():
        return None
    # 1) JSON object (possibly wrapped in a JSON string one or more times)
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            lab = str(obj.get("label", ""))
            return lab if lab in LABELS else None
        if isinstance(obj, str):
            return _extract_label(obj, depth + 1)
    except (json.JSONDecodeError, TypeError):
        pass
    # 2) Python-repr dict, e.g. TriageVerdict-style {'label': 'patched', ...}
    if text.lstrip().startswith("{"):
        try:
            obj = ast.literal_eval(text)
            if isinstance(obj, dict):
                lab = str(obj.get("label", ""))
                return lab if lab in LABELS else None
        except (ValueError, SyntaxError):
            pass
    # 3) embedded JSON label field
    m = LABEL_VARIANT_RE[0].search(text)
    if m:
        return m.group(1)
    # 4) `label: <token>` only on a line whose content is the assignment
    for line in reversed(text.splitlines()):
        line = line.strip()
        if not line:
            continue
        m = LABEL_VARIANT_RE[1].search(line)
        if m:
            return m.group(1)
    # unstructured prose: refuse to guess
    return None


def parse_pred_label(atif: dict) -> str | None:
    """Extract the predicted label from the item ATIF.

    Bare-word search over free prose was removed: an explanation mentioning
    "safe" while predicting "patched" previously parsed as `safe`.
    """
    for step in reversed(atif.get("steps") or []):
        if step.get("source") != "agent":
            continue
        label = _extract_label(step.get("message") or "")
        if label is not None:
            return label
    return None


def parse_explanation(atif: dict) -> str:
    for step in reversed(atif.get("steps") or []):
        if step.get("source") != "agent":
            continue
        msg = step.get("message") or ""
        try:
            if msg.startswith('"'):
                msg = json.loads(msg)
            obj = json.loads(msg) if isinstance(msg, str) and msg.strip().startswith("{") else None
            if isinstance(obj, dict) and obj.get("explanation"):
                return str(obj["explanation"])
        except (json.JSONDecodeError, TypeError):
            pass
        return str(msg)[:800]
    return ""


def model_run_dirs() -> dict[str, Path]:
    candidates: dict[str, list[tuple[int, int, Path]]] = defaultdict(list)
    if not DOWNLOADS.is_dir():
        return {}
    for version_dir in DOWNLOADS.iterdir():
        if not version_dir.is_dir():
            continue
        try:
            version = int(version_dir.name)
        except ValueError:
            continue
        for model_dir in version_dir.iterdir():
            if not model_dir.is_dir():
                continue
            slug = model_dir.name
            for run_dir in model_dir.iterdir():
                if not run_dir.is_dir():
                    continue
                try:
                    run_id = int(run_dir.name)
                except ValueError:
                    run_id = 0
                candidates[slug].append((version, run_id, run_dir))
    return {
        slug: max(runs, key=lambda entry: (entry[0], entry[1]))[2]
        for slug, runs in candidates.items()
        if runs
    }


def seconds_between(start: str | None, end: str | None) -> float | None:
    if not start or not end:
        return None
    try:
        return (
            datetime.fromisoformat(end.replace("Z", "+00:00"))
            - datetime.fromisoformat(start.replace("Z", "+00:00"))
        ).total_seconds()
    except ValueError:
        return None


def wilson_interval(hits: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total <= 0:
        return (0.0, 0.0)
    p = hits / total
    denom = 1 + (z * z / total)
    center = (p + z * z / (2 * total)) / denom
    spread = z * math.sqrt((p * (1 - p) / total) + (z * z / (4 * total * total))) / denom
    return (max(0.0, center - spread), min(1.0, center + spread))


def collect_model(items: list[dict], model: str, run_dir: Path) -> dict:
    aggregate = None
    for p in run_dir.glob("art-label-triage-run_id_*.result.json"):
        aggregate = json.loads(p.read_text())
        break
    rewards = (aggregate or {}).get("verifier_result", {}).get("rewards", {})

    rows = []
    for p in sorted(run_dir.glob("art-label-item-run_param_id_*.result.json")):
        m = re.search(r"param_id_(\d+)_", p.name)
        if not m:
            continue
        idx = int(m.group(1))
        if idx >= len(items):
            continue
        item = items[idx]
        res = json.loads(p.read_text())
        if res.get("exception_info"):
            continue
        score = float(res.get("verifier_result", {}).get("rewards", {}).get("score", 0))
        atif_hits = list(run_dir.glob(f"art-label-item-run_param_id_{idx}_*.atif.json"))
        atif = json.loads(atif_hits[0].read_text()) if atif_hits else {}
        pred = parse_pred_label(atif)
        # Reconcile with verifier score (ground truth for correctness):
        # - score=1 but parsed pred != gold  -> parser artifact, trust score
        # - score=0 but parsed pred == gold  -> parser artifact, mark unknown
        # - pred undetermined                -> gold if correct else unknown
        if score >= 1.0:
            pred = item["gold_label"]
        elif pred == item["gold_label"] or pred is None:
            pred = "unknown"
        rows.append(
            {
                "model": model,
                "idx": idx,
                "id": item["id"],
                "twin_id": item.get("twin_id"),
                "twin_role": item.get("twin_role"),
                "vuln_class": item.get("vuln_class"),
                "gold": item["gold_label"],
                "pred": pred or "unknown",
                "correct": score >= 1.0,
                "cost_usd": (res.get("agent_result") or {}).get("cost_usd"),
                "latency_seconds": seconds_between(res.get("started_at"), res.get("finished_at")),
                "explanation": parse_explanation(atif),
                "snippet": item["snippet"],
            }
        )

    raw = [r for r in rows if r["twin_role"] == "vuln"]
    patched = [r for r in rows if r["twin_role"] == "patched"]
    fillers = [r for r in rows if not r.get("twin_id")]
    raw_acc = sum(r["correct"] for r in raw) / len(raw) if raw else 0.0
    patched_acc = sum(r["correct"] for r in patched) / len(patched) if patched else 0.0
    filler_acc = sum(r["correct"] for r in fillers) / len(fillers) if fillers else 0.0
    overall = sum(r["correct"] for r in rows) / len(rows) if rows else 0.0

    recalls = []
    for label in LABELS:
        labeled = [r for r in rows if r["gold"] == label]
        if labeled:
            recalls.append(sum(r["correct"] for r in labeled) / len(labeled))
    macro_recall = sum(recalls) / len(recalls) if recalls else 0.0

    pairs: dict[str, list[bool]] = defaultdict(list)
    for row in rows:
        if row.get("twin_id"):
            pairs[row["twin_id"]].append(row["correct"])
    pair_consistency = (
        sum(len(hits) == 2 and all(hits) for hits in pairs.values()) / len(pairs)
        if pairs
        else 0.0
    )
    # Exact two-sided sign test over discordant twin pairs. Rows are appended
    # in item order (vuln first), so hits[1] is the patched half.
    discordant = [hits for hits in pairs.values() if len(hits) == 2 and hits[0] != hits[1]]
    patched_wrong = sum(1 for hits in discordant if not hits[1])
    if discordant:
        k = len(discordant)
        tail = (
            sum(math.comb(k, i) for i in range(max(patched_wrong, k - patched_wrong), k + 1))
            / 2**k
        )
        twin_sign_p = min(1.0, 2.0 * tail)
    else:
        twin_sign_p = 1.0
    patched_overclaim_rate = (
        sum(r["pred"] == "reachable_vuln" for r in patched) / len(patched)
        if patched
        else 0.0
    )
    vacuous = [r for r in rows if r["gold"] == "vacuous_noise"]
    vacuous_fp_rate = (
        sum(r["pred"] == "reachable_vuln" for r in vacuous) / len(vacuous)
        if vacuous
        else 0.0
    )
    art_score = (0.4 * raw_acc) + (0.4 * patched_acc) + (0.2 * filler_acc)
    patch_ci_low, patch_ci_high = wilson_interval(
        sum(r["correct"] for r in patched), len(patched)
    )
    latencies = [r["latency_seconds"] for r in rows if r["latency_seconds"] is not None]
    return {
        "model": model,
        "n": len(rows),
        "overall": overall,
        "raw_vuln_accuracy": raw_acc,
        "patched_twin_accuracy": patched_acc,
        "filler_accuracy": filler_acc,
        "twin_gap": raw_acc - patched_acc,
        "twin_discordant_pairs": len(discordant),
        "twin_sign_p": twin_sign_p,
        "art_score": art_score,
        "leaderboard_score": rewards.get("score", art_score),
        "overall_accuracy": overall,
        "macro_recall": macro_recall,
        "pair_consistency": pair_consistency,
        "patched_overclaim_rate": patched_overclaim_rate,
        "vacuous_fp_rate": vacuous_fp_rate,
        "patched_ci_low": patch_ci_low,
        "patched_ci_high": patch_ci_high,
        "total_cost": sum(r["cost_usd"] or 0 for r in rows),
        "mean_latency_seconds": sum(latencies) / len(latencies) if latencies else None,
        "rows": rows,
    }


def confusion(rows: list[dict]) -> list[list[int]]:
    idx = {lab: i for i, lab in enumerate(LABELS)}
    mat = [[0 for _ in LABELS] for _ in LABELS]
    for r in rows:
        g, p = r["gold"], r["pred"]
        if g in idx and p in idx:
            mat[idx[g]][idx[p]] += 1
    return mat


def taxonomy_for(rows: list[dict]) -> Counter:
    counts: Counter = Counter()
    for r in rows:
        if r["correct"]:
            continue
        gold, pred = r["gold"], r["pred"]
        if gold == "patched" and pred == "reachable_vuln":
            counts["Ignored Control / Patch Overclaim"] += 1
        elif gold == "patched" and pred == "safe":
            counts["Control Recognized, Label Drift"] += 1
        elif gold == "safe" and pred == "patched":
            counts["Over-attributed Control"] += 1
        elif gold == "vacuous_noise" and pred == "reachable_vuln":
            counts["False Positive on Vacuous"] += 1
        elif gold == "vacuous_noise" and pred == "safe":
            counts["Vacuous vs Safe Confusion"] += 1
        elif gold == "reachable_vuln" and pred in {"safe", "patched", "vacuous_noise"}:
            counts["Missed Reachable Sink"] += 1
        elif gold == "safe" and pred == "reachable_vuln":
            counts["False Positive on Safe"] += 1
        elif pred == "unknown":
            counts["Unparseable Output"] += 1
        else:
            counts["Other Mislabel"] += 1
    return counts


def main() -> None:
    items = load_items()
    OUT.mkdir(parents=True, exist_ok=True)
    case_dir = OUT / "case_studies"
    case_dir.mkdir(exist_ok=True)
    # Generated case studies are rebuilt every run; curated/ survives.
    for stale in case_dir.glob("case_*.md"):
        stale.unlink()

    models = model_run_dirs()
    summaries = []
    all_tax: Counter = Counter()
    per_class_rows = []

    for model, run_dir in sorted(models.items()):
        if model not in LOCKED:
            continue  # skip error shards (qwen 429s) and strays
        data = collect_model(items, model, run_dir)
        if data["n"] == 0:
            continue
        summaries.append(data)
        mat = confusion(data["rows"])
        tax = taxonomy_for(data["rows"])
        all_tax.update(tax)

        # per-class twin accuracy
        by_class: dict[str, list[bool]] = defaultdict(list)
        for r in data["rows"]:
            if r.get("twin_id"):
                by_class[r["vuln_class"]].append(r["correct"])
        for vc, hits in by_class.items():
            per_class_rows.append(
                {
                    "model": model,
                    "vuln_class": vc,
                    "accuracy": sum(hits) / len(hits),
                    "n": len(hits),
                }
            )

        with (OUT / f"confusion_{model}.md").open("w", encoding="utf-8") as handle:
            handle.write(f"# Confusion matrix — {model}\n\n")
            handle.write("| gold \\ pred | " + " | ".join(LABELS) + " |\n")
            handle.write("| --- | " + " | ".join(["---"] * len(LABELS)) + " |\n")
            for i, lab in enumerate(LABELS):
                handle.write("| " + lab + " | " + " | ".join(str(x) for x in mat[i]) + " |\n")
            handle.write("\n## Failure taxonomy\n\n")
            for k, v in tax.most_common():
                handle.write(f"- {k}: {v}\n")

    # Model scorecard: useful score first, with Twin Gap retained as a diagnostic.
    summaries.sort(key=lambda d: (-float(d["art_score"]), float(d["twin_gap"])))
    with (OUT / "twin_gap.csv").open("w", encoding="utf-8", newline="") as handle:
        w = csv.DictWriter(
            handle,
            fieldnames=[
                "model",
                "art_score",
                "overall",
                "macro_recall",
                "raw_vuln_accuracy",
                "patched_twin_accuracy",
                "filler_accuracy",
                "twin_gap",
                "twin_discordant_pairs",
                "twin_sign_p",
                "pair_consistency",
                "patched_overclaim_rate",
                "vacuous_fp_rate",
                "patched_ci_low",
                "patched_ci_high",
                "total_cost_usd",
                "mean_latency_seconds",
                "tier",
            ],
        )
        w.writeheader()
        tiers = TIERS
        for d in summaries:
            w.writerow(
                {
                    "model": d["model"],
                    "art_score": round(float(d["art_score"]), 4),
                    "overall": round(float(d["overall_accuracy"]), 4),
                    "macro_recall": round(float(d["macro_recall"]), 4),
                    "raw_vuln_accuracy": round(float(d["raw_vuln_accuracy"]), 4),
                    "patched_twin_accuracy": round(float(d["patched_twin_accuracy"]), 4),
                    "filler_accuracy": round(float(d["filler_accuracy"]), 4),
                    "twin_gap": round(float(d["twin_gap"]), 4),
                    "twin_discordant_pairs": int(d["twin_discordant_pairs"]),
                    "twin_sign_p": round(float(d["twin_sign_p"]), 4),
                    "pair_consistency": round(float(d["pair_consistency"]), 4),
                    "patched_overclaim_rate": round(float(d["patched_overclaim_rate"]), 4),
                    "vacuous_fp_rate": round(float(d["vacuous_fp_rate"]), 4),
                    "patched_ci_low": round(float(d["patched_ci_low"]), 4),
                    "patched_ci_high": round(float(d["patched_ci_high"]), 4),
                    "total_cost_usd": round(float(d["total_cost"]), 4),
                    "mean_latency_seconds": (
                        round(float(d["mean_latency_seconds"]), 4)
                        if d["mean_latency_seconds"] is not None
                        else ""
                    ),
                    "tier": TIERS.get(d["model"], "unknown"),
                }
            )

    with (OUT / "per_class_accuracy.csv").open("w", encoding="utf-8", newline="") as handle:
        w = csv.DictWriter(handle, fieldnames=["model", "vuln_class", "accuracy", "n"])
        w.writeheader()
        for row in per_class_rows:
            w.writerow(
                {
                    "model": row["model"],
                    "vuln_class": row["vuln_class"],
                    "accuracy": round(row["accuracy"], 4),
                    "n": row["n"],
                }
            )

    with (OUT / "failure_taxonomy.csv").open("w", encoding="utf-8", newline="") as handle:
        w = csv.writer(handle)
        w.writerow(["failure_class", "count"])
        for k, v in all_tax.most_common():
            w.writerow([k, v])

    # Case studies: patched labeled as reachable_vuln with rich explanation
    cases = []
    for d in summaries:
        for r in d["rows"]:
            if r["gold"] == "patched" and r["pred"] == "reachable_vuln" and len(r["explanation"]) > 40:
                cases.append(r)
            if r["id"] == "twin_sql_php_patched" and not r["correct"]:
                cases.insert(0, r)
    seen = set()
    picked = []
    for c in cases:
        key = (c["model"], c["id"])
        if key in seen:
            continue
        seen.add(key)
        picked.append(c)
        if len(picked) >= 2:
            break
    # Fallback: showcase twin success/fail pair from best twin-gap model
    if len(picked) < 2 and summaries:
        best = summaries[0]
        for r in best["rows"]:
            if r["id"] in {"twin_sql_php_vuln", "twin_sql_php_patched"}:
                picked.append(r)
        picked = picked[:2]

    for i, c in enumerate(picked, 1):
        path = OUT / "case_studies" / f"case_{i}_{c['model']}_{c['id']}.md"
        path.write_text(
            f"# Case study {i}: {c['model']} / {c['id']}\n\n"
            f"- gold: `{c['gold']}`\n- pred: `{c['pred']}`\n- correct: {c['correct']}\n"
            f"- vuln_class: {c.get('vuln_class')}\n\n"
            f"## The Trap\n\n```\n{c['snippet']}```\n\n"
            f"## Model reasoning\n\n{c['explanation']}\n\n"
            f"## Reality\n\nGold label is `{c['gold']}` "
            f"({'control present' if c['gold']=='patched' else 'reachable sink'}).\n",
            encoding="utf-8",
        )

    # Markdown summary for DEV draft
    lines = [
        "# ART analysis summary",
        "",
        "## ART scorecard (diagnostic probe, N=8 pairs + 6 controls)",
        "",
        "_Provenance: scored against `dataset/items.jsonl` (v4 gold) using the latest",
        "downloaded task version under `results/downloads/art-label-triage/` (currently v6:",
        "adjudicated items + param-id-aligned ART scoring). Predictions are parsed from ATIF",
        "transcripts and reconciled with the verifier score; unparseable wrong answers",
        "show as `unknown`, not as a guessed label._",
        "",
        "ART score = 40% vulnerable accuracy + 40% patched accuracy + 20% safe/vacuous controls.",
        "",
        "| Model | ART | Overall | Raw | Patched | Fillers | Twin Gap | Sign p | Pair consistency | Patch overclaim | Cost USD | Mean latency |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for d in summaries:
        if d["model"] not in LOCKED:
            continue
        latency = (
            f"{d['mean_latency_seconds']:.2f}s"
            if d["mean_latency_seconds"] is not None
            else "n/a"
        )
        lines.append(
            f"| `{d['model']}` | {d['art_score']:.3f} | {d['overall_accuracy']:.3f} | "
            f"{d['raw_vuln_accuracy']:.3f} | {d['patched_twin_accuracy']:.3f} | "
            f"{d['filler_accuracy']:.3f} | {d['twin_gap']:.3f} | {d['twin_sign_p']:.3f} | "
            f"{d['pair_consistency']:.3f} | {d['patched_overclaim_rate']:.3f} | "
            f"{d['total_cost']:.4f} | {latency} |"
        )
    lines += ["", "## Aggregate failure taxonomy", ""]
    for k, v in all_tax.most_common():
        lines.append(f"- **{k}**: {v}")
    lines += ["", f"Case studies written: {len(picked)} under `results/case_studies/`", ""]
    (OUT / "ANALYSIS_SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
