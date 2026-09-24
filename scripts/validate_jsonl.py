#!/usr/bin/env python3
"""Validate dataset/items.jsonl escaping, schema, and line limits."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "dataset" / "items.jsonl"
LABELS = {"reachable_vuln", "safe", "vacuous_noise", "patched"}


def main() -> int:
    if not PATH.is_file():
        print(f"MISSING {PATH}", file=sys.stderr)
        return 1
    errors: list[str] = []
    twin_roles: dict[str, set[str]] = {}
    with PATH.open(encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, 1):
            raw = line.rstrip("\n")
            if not raw.strip():
                errors.append(f"L{lineno}: empty line")
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError as exc:
                errors.append(f"L{lineno}: json error {exc}")
                continue
            roundtrip = json.dumps(obj, ensure_ascii=False)
            if json.loads(roundtrip) != obj:
                errors.append(f"L{lineno}: round-trip mismatch")
            snip = obj.get("snippet")
            if not isinstance(snip, str):
                errors.append(f"L{lineno}: snippet must be str")
                continue
            nlines = len(snip.strip("\n").splitlines())
            if nlines < 1 or nlines > 35:
                errors.append(f"L{lineno}: snippet lines={nlines} not in 1..35")
            if obj.get("gold_label") not in LABELS:
                errors.append(f"L{lineno}: bad gold_label {obj.get('gold_label')!r}")
            tid = obj.get("twin_id")
            role = obj.get("twin_role")
            if tid:
                twin_roles.setdefault(str(tid), set()).add(str(role))
            for leak in ("patched", "vulnerable", "sanitize_safe", "FIXED", "now safe"):
                if leak.lower() in snip.lower() and "rationale" not in snip.lower():
                    # Allow only in rationale field, not snippet identifiers.
                    if any(
                        bad in snip
                        for bad in (
                            "process_input_patched",
                            "sanitize_safe",
                            "vulnerable_handler",
                            "// FIXED",
                            "// now safe",
                        )
                    ):
                        errors.append(f"L{lineno}: possible name leakage ({leak})")
    for tid, roles in twin_roles.items():
        if roles != {"vuln", "patched"}:
            errors.append(f"twin {tid}: expected roles vuln+patched, got {roles}")
    if errors:
        print("FAIL")
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    print(f"OK {PATH} ({sum(1 for _ in PATH.open())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
