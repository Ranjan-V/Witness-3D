from __future__ import annotations

import json
from pathlib import Path


def plot_metrics(metrics_path: str, output: str) -> None:
    import matplotlib.pyplot as plt
    import numpy as np
    report = json.loads(Path(metrics_path).read_text())
    records = report["records"]
    methods = sorted({r["method"] for r in records})
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    for metric, label in (("abs_rel", "Absolute relative depth error"),
                           ("damaged_fraction", "Fraction of previously correct depths damaged"),
                           ("corrected_fraction", "Fraction of errors corrected"),
                           ("unknown_fraction", "Inconclusive fraction"),
                           ("wall_seconds", "CPU pipeline wall time (s)")):
        values = [[r[metric] for r in records if r["method"] == method and r.get(metric) is not None]
                  for method in methods]
        fig, ax = plt.subplots(figsize=(max(6, len(methods)*1.2), 4))
        ax.bar(methods, [np.mean(v) if v else np.nan for v in values])
        ax.set_ylabel(label)
        ax.tick_params(axis="x", rotation=35)
        fig.tight_layout()
        fig.savefig(output_path / (metric + ".png"), dpi=180)
        plt.close(fig)
    # Descriptive plot only; aggregate CIs are scene-level, not pixel-level.


def plot_ablation(index_path: str, output: str) -> None:
    import matplotlib.pyplot as plt
    root = Path(index_path).parent
    index = json.loads(Path(index_path).read_text())
    points = []
    for run in index["runs"]:
        path = root / run["id"] / "metrics.json"
        if not path.exists():
            continue
        for record in json.loads(path.read_text())["records"]:
            if record.get("claim_detection") is not None:
                points.append((record["claim_detection"].get("recall"),
                               record.get("conditional_premises_pixel_coverage"),
                               run["uncertainty_controls"]))
    fig, ax = plt.subplots(figsize=(6, 4))
    for recall, coverage, widths in points:
        if recall is not None and coverage is not None:
            ax.scatter(coverage, recall, label=str(widths))
    ax.set(xlabel="Measured pixel-box coverage", ylabel="Depth-claim refutation recall", xlim=(0, 1), ylim=(0, 1))
    ax.set_title("Inspect uncertainty controls before comparing detection rates")
    fig.tight_layout()
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)

