# %%
"""ART Task 1: label attacker-reachable sink triage (core blocker)."""
from dataclasses import dataclass

import pandas as pd
import kaggle_benchmarks as kbench

# %%
LABELS = ("reachable_vuln", "safe", "vacuous_noise", "patched")
# === BEGIN EMBEDDED_ITEMS ===
EMBEDDED_ITEMS = [{'id': 'twin_sql_php_vuln', 'twin_id': 'twin_sql_php', 'twin_role': 'vuln', 'vuln_class': 'sqli', 'showcase': True, 'language': 'php', 'gold_label': 'reachable_vuln', 'snippet': '<?php\nfunction process_user_data($conn) {\n    $id = $_GET["id"];\n    $sql = "SELECT * FROM users WHERE id = " . $id;\n    return mysqli_query($conn, $sql);\n}\n', 'rationale': 'Attacker-controlled id concatenated into SQL.'}, {'id': 'twin_sql_php_patched', 'twin_id': 'twin_sql_php', 'twin_role': 'patched', 'vuln_class': 'sqli', 'showcase': False, 'language': 'php', 'gold_label': 'patched', 'snippet': '<?php\nfunction process_user_data($conn) {\n    $id = (int)$_GET["id"];\n    $stmt = mysqli_prepare($conn, "SELECT * FROM users WHERE id = ?");\n    mysqli_stmt_bind_param($stmt, "i", $id);\n    mysqli_stmt_execute($stmt);\n    return mysqli_stmt_get_result($stmt);\n}\n', 'rationale': 'Cast to int plus prepared statement closes injection.'}, {'id': 'twin_xss_php_vuln', 'twin_id': 'twin_xss_php', 'twin_role': 'vuln', 'vuln_class': 'xss', 'showcase': False, 'language': 'php', 'gold_label': 'reachable_vuln', 'snippet': '<?php\nfunction process_user_data() {\n    $name = $_GET["name"];\n    echo "<h1>Hello " . $name . "</h1>";\n}\n', 'rationale': 'Unescaped GET reflected into HTML.'}, {'id': 'twin_xss_php_patched', 'twin_id': 'twin_xss_php', 'twin_role': 'patched', 'vuln_class': 'xss', 'showcase': False, 'language': 'php', 'gold_label': 'patched', 'snippet': '<?php\nfunction process_user_data() {\n    $name = $_GET["name"];\n    echo "<h1>Hello " . htmlspecialchars($name, ENT_QUOTES, "UTF-8") . "</h1>";\n}\n', 'rationale': 'htmlspecialchars ENT_QUOTES UTF-8 escapes output.'}, {'id': 'twin_cmd_php_vuln', 'twin_id': 'twin_cmd_php', 'twin_role': 'vuln', 'vuln_class': 'cmdi', 'showcase': False, 'language': 'php', 'gold_label': 'reachable_vuln', 'snippet': '<?php\nfunction process_user_data() {\n    $host = $_GET["host"];\n    system("ping -c 1 " . $host);\n}\n', 'rationale': 'GET host concatenated into shell command.'}, {'id': 'twin_cmd_php_patched', 'twin_id': 'twin_cmd_php', 'twin_role': 'patched', 'vuln_class': 'cmdi', 'showcase': False, 'language': 'php', 'gold_label': 'patched', 'snippet': '<?php\nfunction process_user_data() {\n    $host = escapeshellarg($_GET["host"]);\n    system("ping -c 1 " . $host);\n}\n', 'rationale': 'escapeshellarg wraps the argument safely.'}, {'id': 'twin_auth_php_vuln', 'twin_id': 'twin_auth_php', 'twin_role': 'vuln', 'vuln_class': 'auth_bypass', 'showcase': False, 'language': 'php', 'gold_label': 'reachable_vuln', 'snippet': '<?php\nfunction process_user_data() {\n    $title = $_POST["title"];\n    update_option("site_title", $title);\n}\n', 'rationale': 'Privilege-sensitive write with no capability check.'}, {'id': 'twin_auth_php_patched', 'twin_id': 'twin_auth_php', 'twin_role': 'patched', 'vuln_class': 'auth_bypass', 'showcase': False, 'language': 'php', 'gold_label': 'patched', 'snippet': '<?php\nfunction process_user_data() {\n    if (!current_user_can("manage_options")) {\n        return;\n    }\n    $title = $_POST["title"];\n    update_option("site_title", $title);\n}\n', 'rationale': 'Early current_user_can manage_options gate.'}, {'id': 'twin_sql_py_vuln', 'twin_id': 'twin_sql_py', 'twin_role': 'vuln', 'vuln_class': 'sqli', 'showcase': False, 'language': 'python', 'gold_label': 'reachable_vuln', 'snippet': 'def process_user_data(conn, request):\n    user_id = request.args["id"]\n    sql = f"SELECT * FROM users WHERE id = {user_id}"\n    return conn.execute(sql).fetchall()\n', 'rationale': 'f-string interpolates attacker id into SQL.'}, {'id': 'twin_sql_py_patched', 'twin_id': 'twin_sql_py', 'twin_role': 'patched', 'vuln_class': 'sqli', 'showcase': False, 'language': 'python', 'gold_label': 'patched', 'snippet': 'def process_user_data(conn, request):\n    user_id = int(request.args["id"])\n    sql = "SELECT * FROM users WHERE id = ?"\n    return conn.execute(sql, (user_id,)).fetchall()\n', 'rationale': 'int cast plus bound parameter.'}, {'id': 'twin_path_py_vuln', 'twin_id': 'twin_path_py', 'twin_role': 'vuln', 'vuln_class': 'path_traversal', 'showcase': False, 'language': 'python', 'gold_label': 'reachable_vuln', 'snippet': 'import os\n\ndef process_user_data(base_dir, request):\n    name = request.args["file"]\n    path = os.path.join(base_dir, name)\n    with open(path, "r", encoding="utf-8") as handle:\n        return handle.read()\n', 'rationale': 'User file name joined without basename restriction.'}, {'id': 'twin_path_py_patched', 'twin_id': 'twin_path_py', 'twin_role': 'patched', 'vuln_class': 'path_traversal', 'showcase': False, 'language': 'python', 'gold_label': 'patched', 'snippet': 'import os\n\ndef process_user_data(base_dir, request):\n    name = os.path.basename(request.args["file"])\n    path = os.path.join(base_dir, name)\n    with open(path, "r", encoding="utf-8") as handle:\n        return handle.read()\n', 'rationale': 'basename strips path traversal segments.'}, {'id': 'twin_deser_py_vuln', 'twin_id': 'twin_deser_py', 'twin_role': 'vuln', 'vuln_class': 'insecure_deser', 'showcase': False, 'language': 'python', 'gold_label': 'reachable_vuln', 'snippet': 'import pickle\n\ndef process_user_data(request):\n    raw = request.get_data()\n    return pickle.loads(raw)\n', 'rationale': 'pickle.loads on attacker body enables RCE gadgets.'}, {'id': 'twin_deser_py_patched', 'twin_id': 'twin_deser_py', 'twin_role': 'patched', 'vuln_class': 'insecure_deser', 'showcase': False, 'language': 'python', 'gold_label': 'patched', 'snippet': 'import hashlib\nimport hmac\nimport pickle\n\nSHARED_SECRET = b"lab-signing-key"\n\ndef process_user_data(request):\n    raw = request.get_data()\n    signature = request.headers.get("X-Signature", "")\n    expected = hmac.new(SHARED_SECRET, raw, hashlib.sha256).hexdigest()\n    if not hmac.compare_digest(signature, expected):\n        return None\n    return pickle.loads(raw)\n', 'rationale': 'HMAC-SHA256 signature gate closes the deserialization sink.'}, {'id': 'twin_lfi_php_vuln', 'twin_id': 'twin_lfi_php', 'twin_role': 'vuln', 'vuln_class': 'lfi', 'showcase': False, 'language': 'php', 'gold_label': 'reachable_vuln', 'snippet': '<?php\nfunction process_user_data() {\n    $page = $_GET["page"];\n    include $page . ".php";\n}\n', 'rationale': 'GET page controls include path.'}, {'id': 'twin_lfi_php_patched', 'twin_id': 'twin_lfi_php', 'twin_role': 'patched', 'vuln_class': 'lfi', 'showcase': False, 'language': 'php', 'gold_label': 'patched', 'snippet': '<?php\nfunction process_user_data() {\n    $allowed = ["home", "about", "contact"];\n    $page = $_GET["page"];\n    if (!in_array($page, $allowed, true)) {\n        return;\n    }\n    include $page . ".php";\n}\n', 'rationale': 'Strict allowlist before include.'}, {'id': 'safe_const_php', 'twin_id': None, 'twin_role': 'none', 'language': 'php', 'gold_label': 'safe', 'snippet': '<?php\nfunction process_user_data($conn) {\n    $sql = "SELECT id, email FROM users WHERE active = 1";\n    return mysqli_query($conn, $sql);\n}\n', 'rationale': 'No attacker-controlled input in query.'}, {'id': 'safe_bound_py', 'twin_id': None, 'twin_role': 'none', 'language': 'python', 'gold_label': 'safe', 'snippet': 'def process_user_data(conn):\n    return conn.execute(\n        "SELECT id, email FROM users WHERE active = ?",\n        (1,),\n    ).fetchall()\n', 'rationale': 'Constant bound param; no request input.'}, {'id': 'vacuous_comment_php', 'twin_id': None, 'twin_role': 'none', 'language': 'php', 'gold_label': 'vacuous_noise', 'snippet': '<?php\nfunction process_user_data() {\n    // Example only: eval($_GET["x"]);\n    return "ok";\n}\n', 'rationale': 'Dangerous call appears only inside a comment.'}, {'id': 'vacuous_dead_py', 'twin_id': None, 'twin_role': 'none', 'language': 'python', 'gold_label': 'vacuous_noise', 'snippet': 'def process_user_data(request):\n    if False:\n        return eval(request.args["code"])\n    return {"status": "ok"}\n', 'rationale': 'eval is behind if False; never reachable.'}, {'id': 'vacuous_string_php', 'twin_id': None, 'twin_role': 'none', 'language': 'php', 'gold_label': 'vacuous_noise', 'snippet': '<?php\nfunction process_user_data() {\n    $docs = "Never call system($_GET[cmd]) in production.";\n    return $docs;\n}\n', 'rationale': 'Sink appears only inside a documentation string.'}, {'id': 'safe_len_py', 'twin_id': None, 'twin_role': 'none', 'language': 'python', 'gold_label': 'safe', 'snippet': 'def process_user_data(request):\n    name = request.args.get("name", "")\n    return {"name_length": len(name)}\n', 'rationale': 'Attacker input flows only into len(); no dangerous sink present.'}]
# === END EMBEDDED_ITEMS ===


@dataclass
class TriageVerdict:
    label: str
    explanation: str


def load_items():
    return list(EMBEDDED_ITEMS)

def build_prompt(language: str, snippet: str) -> str:
    # Prompt isolation: never include twin_id, twin_role, gold_label, or rationale.
    return (
        "You are labeling a short code snippet for AppSec triage.\n"
        "Choose exactly one label:\n"
        "- reachable_vuln: attacker-controlled input reaches a dangerous sink without an effective control\n"
        "- patched: attacker-controlled input still reaches the sink, but an effective standard control on the path "
        "(cast, prepared statement, output escaping, auth/capability gate, allowlist, signature check) neutralizes it\n"
        "- safe: attacker-controlled input never reaches a dangerous sink — the input is absent, or it only flows "
        "into non-dangerous operations (length check, comparison, dict key)\n"
        "- vacuous_noise: dangerous-looking text is commented, dead, or only in a string/docs\n\n"
        f"Language: {language}\n"
        "Code:\n"
        f"{snippet}\n"
        "Return structured fields label and explanation (2-4 sentences)."
    )


def _normalize_label(label: str | None) -> str | None:
    if not label:
        return None
    cleaned = str(label).strip()
    return cleaned if cleaned in LABELS else None


def _hits_by_param_id(completed_df: pd.DataFrame) -> dict[int, bool]:
    """Map evaluation row id → hit. Missing/errored rows are absent (scored as miss)."""
    hits: dict[int, bool] = {}
    if completed_df is None or len(completed_df) == 0:
        return hits
    for _, crow in completed_df.iterrows():
        pid = crow.get("id")
        if pid is None or (isinstance(pid, float) and pd.isna(pid)):
            continue
        hits[int(pid)] = bool(crow.get("result"))
    return hits


def compute_art_score(items: list, hits_by_id: dict[int, bool]) -> float:
    """Weighted ART: 40% vuln + 40% patched + 20% filler. Errored items count as miss."""
    raw_hits = raw_n = patched_hits = patched_n = filler_hits = filler_n = 0
    for idx, row in enumerate(items):
        hit = bool(hits_by_id.get(idx, False))
        role = row.get("twin_role")
        if role == "vuln":
            raw_n += 1
            raw_hits += int(hit)
        elif role == "patched":
            patched_n += 1
            patched_hits += int(hit)
        else:
            filler_n += 1
            filler_hits += int(hit)
    raw_acc = (raw_hits / raw_n) if raw_n else 0.0
    patched_acc = (patched_hits / patched_n) if patched_n else 0.0
    filler_acc = (filler_hits / filler_n) if filler_n else 0.0
    return float((0.4 * raw_acc) + (0.4 * patched_acc) + (0.2 * filler_acc))


# %%
@kbench.task(name="art-label-item", store_task=False)
def art_label_item(llm, language: str, snippet: str, gold_label: str) -> bool:
    prompt = build_prompt(language, snippet)
    verdict = llm.prompt(prompt, schema=TriageVerdict)
    label = _normalize_label(getattr(verdict, "label", None))
    if label is None:
        return False
    return label == gold_label


# %%
@kbench.task(name="art-label-triage")
def art_label_triage(llm) -> float:
    """ART score: 40% vulnerable + 40% patched + 20% safe/vacuous accuracy.

    Returns a float in [0, 1]. Note: Kaggle *collection* leaderboards currently
    show Pass/Fail aggregation for Score floats; the ranked metric is this return
    value (also in run rewards.score).
    """
    items = load_items()
    df = pd.DataFrame(
        [
            {
                "language": row["language"],
                "snippet": row["snippet"],
                "gold_label": row["gold_label"],
            }
            for row in items
        ]
    )
    results = art_label_item.evaluate(
        llm=[llm],
        evaluation_data=df,
        on_failure="continue",
        n_jobs=1,
    )
    completed = results.completed_runs.as_dataframe()
    hits = _hits_by_param_id(completed)
    score = compute_art_score(items, hits)
    return max(0.0, min(1.0, round(score, 6)))


# %%
art_label_triage.run(kbench.llm)
