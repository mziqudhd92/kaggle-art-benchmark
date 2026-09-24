#!/usr/bin/env python3
"""Build dataset/items.jsonl with explicit twin pairs (no name leakage)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dataset" / "items.jsonl"

# Each twin pair: identical function/variable names; only the control differs.
PAIRS: list[dict] = [
    {
        "twin_id": "twin_sql_php",
        "vuln_class": "sqli",
        "showcase": True,
        "language": "php",
        "vuln": '''<?php
function process_user_data($conn) {
    $id = $_GET["id"];
    $sql = "SELECT * FROM users WHERE id = " . $id;
    return mysqli_query($conn, $sql);
}
''',
        "patched": '''<?php
function process_user_data($conn) {
    $id = (int)$_GET["id"];
    $stmt = mysqli_prepare($conn, "SELECT * FROM users WHERE id = ?");
    mysqli_stmt_bind_param($stmt, "i", $id);
    mysqli_stmt_execute($stmt);
    return mysqli_stmt_get_result($stmt);
}
''',
        "rationale_vuln": "Attacker-controlled id concatenated into SQL.",
        "rationale_patched": "Cast to int plus prepared statement closes injection.",
    },
    {
        "twin_id": "twin_xss_php",
        "vuln_class": "xss",
        "showcase": False,
        "language": "php",
        "vuln": '''<?php
function process_user_data() {
    $name = $_GET["name"];
    echo "<h1>Hello " . $name . "</h1>";
}
''',
        "patched": '''<?php
function process_user_data() {
    $name = $_GET["name"];
    echo "<h1>Hello " . htmlspecialchars($name, ENT_QUOTES, "UTF-8") . "</h1>";
}
''',
        "rationale_vuln": "Unescaped GET reflected into HTML.",
        "rationale_patched": "htmlspecialchars ENT_QUOTES UTF-8 escapes output.",
    },
    {
        "twin_id": "twin_cmd_php",
        "vuln_class": "cmdi",
        "showcase": False,
        "language": "php",
        "vuln": '''<?php
function process_user_data() {
    $host = $_GET["host"];
    system("ping -c 1 " . $host);
}
''',
        "patched": '''<?php
function process_user_data() {
    $host = escapeshellarg($_GET["host"]);
    system("ping -c 1 " . $host);
}
''',
        "rationale_vuln": "GET host concatenated into shell command.",
        "rationale_patched": "escapeshellarg wraps the argument safely.",
    },
    {
        "twin_id": "twin_auth_php",
        "vuln_class": "auth_bypass",
        "showcase": False,
        "language": "php",
        "vuln": '''<?php
function process_user_data() {
    $title = $_POST["title"];
    update_option("site_title", $title);
}
''',
        "patched": '''<?php
function process_user_data() {
    if (!current_user_can("manage_options")) {
        return;
    }
    $title = $_POST["title"];
    update_option("site_title", $title);
}
''',
        "rationale_vuln": "Privilege-sensitive write with no capability check.",
        "rationale_patched": "Early current_user_can manage_options gate.",
    },
    {
        "twin_id": "twin_sql_py",
        "vuln_class": "sqli",
        "showcase": False,
        "language": "python",
        "vuln": '''def process_user_data(conn, request):
    user_id = request.args["id"]
    sql = f"SELECT * FROM users WHERE id = {user_id}"
    return conn.execute(sql).fetchall()
''',
        "patched": '''def process_user_data(conn, request):
    user_id = int(request.args["id"])
    sql = "SELECT * FROM users WHERE id = ?"
    return conn.execute(sql, (user_id,)).fetchall()
''',
        "rationale_vuln": "f-string interpolates attacker id into SQL.",
        "rationale_patched": "int cast plus bound parameter.",
    },
    {
        "twin_id": "twin_path_py",
        "vuln_class": "path_traversal",
        "showcase": False,
        "language": "python",
        "vuln": '''import os

def process_user_data(base_dir, request):
    name = request.args["file"]
    path = os.path.join(base_dir, name)
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()
''',
        "patched": '''import os

def process_user_data(base_dir, request):
    name = os.path.basename(request.args["file"])
    path = os.path.join(base_dir, name)
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()
''',
        "rationale_vuln": "User file name joined without basename restriction.",
        "rationale_patched": "basename strips path traversal segments.",
    },
    {
        # v4: patched side was `pickle.loads -> json.loads`, which removes the sink
        # rather than adding a control — all 7 models labeled it `safe` and "failed".
        # Keeping the pickle sink behind an HMAC signature gate makes `patched`
        # unambiguous while preserving the twin diff.
        "twin_id": "twin_deser_py",
        "vuln_class": "insecure_deser",
        "showcase": False,
        "language": "python",
        "vuln": '''import pickle

def process_user_data(request):
    raw = request.get_data()
    return pickle.loads(raw)
''',
        "patched": '''import hashlib
import hmac
import pickle

SHARED_SECRET = b"lab-signing-key"

def process_user_data(request):
    raw = request.get_data()
    signature = request.headers.get("X-Signature", "")
    expected = hmac.new(SHARED_SECRET, raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    return pickle.loads(raw)
''',
        "rationale_vuln": "pickle.loads on attacker body enables RCE gadgets.",
        "rationale_patched": "HMAC-SHA256 signature gate closes the deserialization sink.",
    },
    {
        "twin_id": "twin_lfi_php",
        "vuln_class": "lfi",
        "showcase": False,
        "language": "php",
        "vuln": '''<?php
function process_user_data() {
    $page = $_GET["page"];
    include $page . ".php";
}
''',
        "patched": '''<?php
function process_user_data() {
    $allowed = ["home", "about", "contact"];
    $page = $_GET["page"];
    if (!in_array($page, $allowed, true)) {
        return;
    }
    include $page . ".php";
}
''',
        "rationale_vuln": "GET page controls include path.",
        "rationale_patched": "Strict allowlist before include.",
    },
]

FILLERS: list[dict] = [
    {
        "id": "safe_const_php",
        "twin_id": None,
        "twin_role": "none",
        "language": "php",
        "gold_label": "safe",
        "snippet": '''<?php
function process_user_data($conn) {
    $sql = "SELECT id, email FROM users WHERE active = 1";
    return mysqli_query($conn, $sql);
}
''',
        "rationale": "No attacker-controlled input in query.",
    },
    {
        "id": "safe_bound_py",
        "twin_id": None,
        "twin_role": "none",
        "language": "python",
        "gold_label": "safe",
        "snippet": '''def process_user_data(conn):
    return conn.execute(
        "SELECT id, email FROM users WHERE active = ?",
        (1,),
    ).fetchall()
''',
        "rationale": "Constant bound param; no request input.",
    },
    {
        "id": "vacuous_comment_php",
        "twin_id": None,
        "twin_role": "none",
        "language": "php",
        "gold_label": "vacuous_noise",
        "snippet": '''<?php
function process_user_data() {
    // Example only: eval($_GET["x"]);
    return "ok";
}
''',
        "rationale": "Dangerous call appears only inside a comment.",
    },
    {
        "id": "vacuous_dead_py",
        "twin_id": None,
        "twin_role": "none",
        "language": "python",
        "gold_label": "vacuous_noise",
        "snippet": '''def process_user_data(request):
    if False:
        return eval(request.args["code"])
    return {"status": "ok"}
''',
        "rationale": "eval is behind if False; never reachable.",
    },
    {
        "id": "vacuous_string_php",
        "twin_id": None,
        "twin_role": "none",
        "language": "php",
        "gold_label": "vacuous_noise",
        "snippet": '''<?php
function process_user_data() {
    $docs = "Never call system($_GET[cmd]) in production.";
    return $docs;
}
''',
        "rationale": "Sink appears only inside a documentation string.",
    },
    {
        # v4: was `safe_escape_py` (html.escape + f-string HTML). Attacker input
        # reaching an output sink closed by a control is `patched` by the prompt's
        # own definition, so all 7 models answered `patched` and "failed". This
        # replacement keeps attacker input present but routes it only to a
        # non-dangerous operation, making `safe` unambiguous.
        "id": "safe_len_py",
        "twin_id": None,
        "twin_role": "none",
        "language": "python",
        "gold_label": "safe",
        "snippet": '''def process_user_data(request):
    name = request.args.get("name", "")
    return {"name_length": len(name)}
''',
        "rationale": "Attacker input flows only into len(); no dangerous sink present.",
    },
]


def _lines(snippet: str) -> int:
    return len(snippet.strip("\n").splitlines())


def main() -> None:
    rows: list[dict] = []
    for pair in PAIRS:
        for role, gold, rat_key in (
            ("vuln", "reachable_vuln", "rationale_vuln"),
            ("patched", "patched", "rationale_patched"),
        ):
            snippet = pair[role].strip("\n") + "\n"
            assert _lines(snippet) <= 35, (pair["twin_id"], role, _lines(snippet))
            rows.append(
                {
                    "id": f"{pair['twin_id']}_{role}",
                    "twin_id": pair["twin_id"],
                    "twin_role": role,
                    "vuln_class": pair["vuln_class"],
                    "showcase": bool(pair.get("showcase")) and role == "vuln",
                    "language": pair["language"],
                    "gold_label": gold,
                    "snippet": snippet,
                    "rationale": pair[rat_key],
                }
            )
    rows.extend(FILLERS)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Wrote {len(rows)} items -> {OUT}")


if __name__ == "__main__":
    main()
