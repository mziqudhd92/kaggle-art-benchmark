# Case study 2: claude-haiku-4-5-20251001 / twin_path_py_patched

- gold: `patched`
- pred: `reachable_vuln`
- correct: False
- vuln_class: path_traversal

## The Trap

```
import os

def process_user_data(base_dir, request):
    name = os.path.basename(request.args["file"])
    path = os.path.join(base_dir, name)
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()
```

## Model reasoning

The `request.args["file"]` contains attacker-controlled input that flows directly to `os.path.join()` after only a `basename()` call. While `basename()` removes directory components, an attacker can still supply arbitrary filenames and access unintended files within the base_dir. The `open()` call is the dangerous sink, and there is no effective control preventing path traversal or unauthorized file access.

## Reality

Gold label is `patched` (control present).
