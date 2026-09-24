# Case study 1: claude-haiku-4-5-20251001 / twin_path_py_patched

- gold: `patched`
- pred: `reachable_vuln`
- correct: False
- vuln_class: path_traversal

## The Trap

```python
import os

def process_user_data(base_dir, request):
    name = os.path.basename(request.args["file"])
    path = os.path.join(base_dir, name)
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()
```

## Model reasoning

This code constructs a file path from user-controlled input (request.args["file"]) combined with a base directory using os.path.join(). While os.path.basename() is used to extract the filename component, an attacker can still exploit this with path traversal payloads like "../../../etc/passwd" which basename() does not block—it only removes directory separators but basename() passes through relative path components. An attacker can thus read arbitrary files outside the base_dir, reaching the dangerous open() sink.

## Reality

Gold label is `patched`. Haiku hallucinates a bypass: `os.path.basename("../../../etc/passwd")` returns `"passwd"`, so `join(base_dir, name)` stays under `base_dir`. This is a classic **Ignored Sanitizer** / wrong mental model of `basename`, not a gold-label bug.
