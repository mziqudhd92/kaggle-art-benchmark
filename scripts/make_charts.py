#!/usr/bin/env python3
"""Render DEV-post charts from results CSVs + confusion markdown.

Outputs into assets/:
- raw_vs_patched_accuracy.png : grouped bars, raw vs patched twin accuracy (+ Wilson CI)
- confusion_top_model.png     : 4x4 confusion heatmap for the top-ART model
"""
from __future__ import annotations

import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets"
TOP_MODEL = "gemini-3.5-flash"  # cheapest of the tied-0.917 top cluster
C_RAW, C_PATCHED = "#4C72B0", "#DD8452"


def grouped_bars() -> None:
    df = pd.read_csv(ROOT / "results" / "twin_gap.csv")
    df = df.sort_values(["art_score", "twin_gap"], ascending=[False, True]).reset_index(drop=True)
    labels = [m.replace("-2026-03-17", "").replace("-20251001", "").replace("-20250929", "") for m in df["model"]]
    x = np.arange(len(df))
    w = 0.38

    fig, ax = plt.subplots(figsize=(9.2, 4.6), dpi=150)
    ax.bar(x - w / 2, df["raw_vuln_accuracy"], w, label="Raw vuln accuracy (vulnerable twins)", color=C_RAW)
    err = np.array([
        df["patched_twin_accuracy"] - df["patched_ci_low"],
        df["patched_ci_high"] - df["patched_twin_accuracy"],
    ])
    bars = ax.bar(
        x + w / 2, df["patched_twin_accuracy"], w,
        label="Patched twin accuracy (Wilson 95% CI)", color=C_PATCHED,
        yerr=err, capsize=3, error_kw={"linewidth": 1.1, "ecolor": "#555555"},
    )
    for xi, (_, row) in zip(x, df.iterrows()):
        ax.text(xi + w / 2, row["patched_ci_high"] + 0.02, f"Δ{row['twin_gap']:.2f}",
                ha="center", va="bottom", fontsize=8, color="#8a4b1f")
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, 0.02, f"{b.get_height():.2f}",
                ha="center", va="bottom", fontsize=8, color="white", fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=28, ha="right", fontsize=9)
    ax.set_ylim(0, 1.12)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_ylabel("Accuracy")
    ax.set_title("All models find the vuln (blue, 1.00) — they differ on respecting the patch (orange)\n"
                 "Δ = Twin Gap; bars annotated with patched accuracy; N=8 per class, one run", fontsize=10)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2, fontsize=9, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25)
    fig.subplots_adjust(bottom=0.34)
    fig.savefig(OUT / "raw_vs_patched_accuracy.png")
    plt.close(fig)
    print(f"wrote {OUT / 'raw_vs_patched_accuracy.png'}")


def confusion_heatmap() -> None:
    labels = ["reachable_vuln", "safe", "vacuous_noise", "patched"]
    path = ROOT / "results" / f"confusion_{TOP_MODEL}.md"
    text = path.read_text(encoding="utf-8")
    rows = re.findall(r"^\|\s*(reachable_vuln|safe|vacuous_noise|patched)\s*\|(.+)\|\s*$", text, re.M)
    mat = np.zeros((4, 4), dtype=int)
    for i, (_, rest) in enumerate(rows):
        vals = [int(v) for v in re.findall(r"\d+", rest)]
        mat[i, : len(vals)] = vals[:4]

    fig, ax = plt.subplots(figsize=(5.6, 4.6), dpi=150)
    im = ax.imshow(mat, cmap="Blues", vmin=0, vmax=mat.max())
    ax.set_xticks(range(4), labels, rotation=30, ha="right", fontsize=9)
    ax.set_yticks(range(4), labels, fontsize=9)
    ax.set_xlabel("Predicted", fontsize=10)
    ax.set_ylabel("Gold", fontsize=10)
    thresh = mat.max() / 2
    for i in range(4):
        for j in range(4):
            ax.text(j, i, mat[i, j], ha="center", va="center", fontsize=11,
                    color="white" if mat[i, j] > thresh else "#1f2a44",
                    fontweight="bold" if mat[i, j] > 0 else "normal")
    ax.set_title(f"Confusion — {TOP_MODEL} (ART 0.917, tied top)\n"
                 "8/8 vulns found; misses concentrate on gold=safe → patched", fontsize=10)
    fig.colorbar(im, ax=ax, shrink=0.85)
    fig.tight_layout()
    fig.savefig(OUT / "confusion_top_model.png")
    plt.close(fig)
    print(f"wrote {OUT / 'confusion_top_model.png'}")


def per_class_heatmap() -> None:
    """Model x vuln_class twin accuracy (vuln+patched halves pooled)."""
    df = pd.read_csv(ROOT / "results" / "per_class_accuracy.csv")
    models = list(df["model"].unique())
    models.sort(key=lambda m: -float(df[df["model"] == m]["accuracy"].mean()))
    classes = sorted(df["vuln_class"].unique())
    grid = np.full((len(models), len(classes)), np.nan)
    for _, row in df.iterrows():
        grid[models.index(row["model"]), classes.index(row["vuln_class"])] = row["accuracy"]

    fig, ax = plt.subplots(figsize=(7.6, 4.4), dpi=150)
    im = ax.imshow(grid, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(classes)), [c.replace("_", "\n") for c in classes], fontsize=8.5)
    ax.set_yticks(range(len(models)), [m.replace("-2026-03-17", "").replace("-20251001", "").replace("-20250929", "") for m in models], fontsize=8.5)
    for i in range(len(models)):
        for j in range(len(classes)):
            v = grid[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8,
                        color="#1f2a44", fontweight="bold" if v < 1 else "normal")
    ax.set_title("Twin accuracy by vulnerability class (vuln + patched halves pooled)\n"
                 "insecure_deser 0.5 everywhere = the v3 gold-label artifact, fixed in v4", fontsize=9.5)
    fig.colorbar(im, ax=ax, shrink=0.8, label="accuracy")
    fig.tight_layout()
    fig.savefig(OUT / "per_class_heatmap.png")
    plt.close(fig)
    print(f"wrote {OUT / 'per_class_heatmap.png'}")


def cost_art_scatter() -> None:
    """Cost (log) vs ART score; bubble = latency."""
    df = pd.read_csv(ROOT / "results" / "twin_gap.csv")
    fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=150)
    colors = {"heavy": "#6a3d9a", "mid": "#4C72B0", "flash": "#DD8452"}
    for _, row in df.iterrows():
        try:
            latency = float(row["mean_latency_seconds"])
        except (TypeError, ValueError):
            latency = 1.0
        if latency != latency or latency <= 0:  # NaN or non-positive
            latency = 1.0
        ax.scatter(row["total_cost_usd"], row["art_score"],
                   s=30 + 260 * latency,
                   color=colors.get(row["tier"], "#888"), alpha=0.75,
                   edgecolor="white", linewidth=1.2, zorder=3)
    for k, (_, row) in enumerate(df.iterrows()):
        name = row["model"].replace("-2026-03-17", "").replace("-20251001", "").replace("-20250929", "")
        # stagger above/below so adjacent labels never collide on log-x
        ax.annotate(name, (row["total_cost_usd"], row["art_score"]),
                    textcoords="offset points", xytext=(0, 12 if k % 2 == 0 else -20),
                    ha="center", fontsize=8)
    ax.margins(x=0.08)
    ax.set_xscale("log")
    ax.set_xlabel("Total cost per full run, USD (log scale)")
    ax.set_ylabel("ART score")
    ax.set_ylim(0.6, 1.05)
    ax.set_title("Patch-respect per dollar: gemma-4-31b and the Gemini flash tier\n"
                 "match pro-tier ART at 1-3% of the cost (bubble size = mean latency)", fontsize=10)
    ax.grid(alpha=0.25)
    handles = [plt.Line2D([], [], marker="o", ls="", color=c, label=t) for t, c in colors.items()]
    ax.legend(handles=handles, title="tier", fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(OUT / "cost_vs_art.png")
    plt.close(fig)
    print(f"wrote {OUT / 'cost_vs_art.png'}")


def taxonomy_bars() -> None:
    """Aggregate failure taxonomy, horizontal bars."""
    df = pd.read_csv(ROOT / "results" / "failure_taxonomy.csv").sort_values("count")
    fig, ax = plt.subplots(figsize=(7.4, 3.6), dpi=150)
    bars = ax.barh(df["failure_class"], df["count"], color="#C44E52", alpha=0.85)
    for b, (_, row) in zip(bars, df.iterrows()):
        ax.text(b.get_width() + 0.12, b.get_y() + b.get_height() / 2,
                int(row["count"]), va="center", fontsize=9, color="#1f2a44")
    ax.set_xlim(0, df["count"].max() * 1.18)
    ax.set_xlabel("misclassifications across all 7 models (25 items each)")
    ax.set_title("Where the errors live: the top class is dominated by the v3\n"
                 "gold-label artifact on one `safe` filler — fixed in v4", fontsize=9.5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT / "failure_taxonomy.png")
    plt.close(fig)
    print(f"wrote {OUT / 'failure_taxonomy.png'}")


def patched_ci_dotplot() -> None:
    """Forest plot: patched twin accuracy with Wilson 95% CI."""
    df = pd.read_csv(ROOT / "results" / "twin_gap.csv")
    df = df.sort_values("patched_twin_accuracy").reset_index(drop=True)
    labels = [m.replace("-2026-03-17", "").replace("-20251001", "").replace("-20250929", "") for m in df["model"]]
    y = np.arange(len(df))
    fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=150)
    ax.hlines(y, df["patched_ci_low"], df["patched_ci_high"], color="#4C72B0", linewidth=2.4, alpha=0.6)
    ax.scatter(df["patched_twin_accuracy"], y, color="#4C72B0", s=52, zorder=3)
    for yi, (_, row) in zip(y, df.iterrows()):
        ax.text(row["patched_ci_high"] + 0.015, yi, f"{row['patched_twin_accuracy']:.2f}",
                va="center", fontsize=8.5, color="#1f2a44")
    ax.axvspan(0.875, 1.0, color="#DD8452", alpha=0.07)
    ax.text(0.9375, 0.55, "top-cluster\noverlap zone", ha="center", va="center",
            fontsize=8, color="#8a4b1f")
    ax.set_yticks(y, labels, fontsize=9)
    ax.set_xlim(0.2, 1.05)
    ax.set_xlabel("patched twin accuracy (dot) with Wilson 95% CI (line), N=8")
    ax.set_title("Honest uncertainty: single-run CIs overlap across the top cluster —\n"
                 "the ordering inside it is indicative, the Claude/nano drop is not", fontsize=9.5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT / "patched_ci_dotplot.png")
    plt.close(fig)
    print(f"wrote {OUT / 'patched_ci_dotplot.png'}")


def twin_method_diagram() -> None:
    """How a twin pair works: identical shape, only the control differs."""
    vuln_code = ("def process_user_data(conn, request):\n"
                 "    uid = request.args[\"id\"]\n"
                 "    sql = f\"SELECT * FROM users\n"
                 "            WHERE id = {uid}\"\n"
                 "    return conn.execute(sql)")
    patched_code = ("def process_user_data(conn, request):\n"
                    "    uid = int(request.args[\"id\"])\n"
                    "    sql = \"SELECT * FROM users\n"
                    "            WHERE id = ?\"\n"
                    "    return conn.execute(sql, (uid,))")
    fig, ax = plt.subplots(figsize=(9.0, 4.0), dpi=150)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.6)
    ax.axis("off")
    for x0, title, code, box_c in ((0.25, "vuln twin  →  reachable_vuln", vuln_code, "#C44E52"),
                                   (5.35, "patched twin  →  patched", patched_code, "#4C72B0")):
        ax.add_patch(plt.Rectangle((x0, 0.55), 4.4, 3.4, fill=True, facecolor="#f7f8fa",
                                   edgecolor=box_c, linewidth=1.6))
        ax.text(x0 + 0.15, 3.62, title, fontsize=10, fontweight="bold", color=box_c, family="monospace")
        ax.text(x0 + 0.15, 2.0, code, fontsize=8.2, family="monospace", va="center", color="#1f2a44")
    ax.annotate("", xy=(5.28, 2.3), xytext=(4.72, 2.3),
                arrowprops=dict(arrowstyle="<->", color="#555", lw=1.6))
    ax.text(5.0, 2.62, "only the\ncontrol differs", ha="center", fontsize=8.5, color="#555")
    ax.text(5.0, 0.18, "identical function name, identifiers and shape  •  prompts see snippet + language only  •  gold labels are scoring-only",
            ha="center", fontsize=8.3, color="#666")
    ax.text(5.0, 4.35, "One twin pair: same sink, same names — the only signal is the control",
            ha="center", fontsize=11, fontweight="bold", color="#1f2a44")
    fig.tight_layout()
    fig.savefig(OUT / "twin_method.png")
    plt.close(fig)
    print(f"wrote {OUT / 'twin_method.png'}")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    grouped_bars()
    confusion_heatmap()
    per_class_heatmap()
    cost_art_scatter()
    taxonomy_bars()
    patched_ci_dotplot()
    twin_method_diagram()


if __name__ == "__main__":
    main()
