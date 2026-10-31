import hashlib
import json
import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
TABLES = ROOT / "outputs/tables"
FIGURES = ROOT / "outputs/figures"
REPORTS = ROOT / "outputs/reports"
MODELS = {"if": "Isolation Forest", "ecod": "ECOD", "lof": "LOF"}


def save_figure(figure, name):
    figure.tight_layout()
    figure.savefig(FIGURES / name, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def agreement_figure():
    table = pd.read_csv(TABLES / "model_agreement.csv").query("k_requested == 25")
    figure, axes = plt.subplots(2, 2, figsize=(11, 9))
    for row, (channel, group) in zip(axes, table.groupby("channel")):
        for ax, metric, title in zip(row, ["spearman", "jaccard"], ["Spearman", "Jaccard Top-25"]):
            matrix = np.eye(3)
            for item in group.itertuples(index=False):
                left, right = list(MODELS).index(item.model_left), list(MODELS).index(item.model_right)
                matrix[left, right] = matrix[right, left] = getattr(item, metric)
            ax.imshow(matrix, vmin=0, vmax=1, cmap="Blues")
            ax.set(xticks=range(3), yticks=range(3), xticklabels=list(MODELS.values()),
                   yticklabels=list(MODELS.values()), title=f"{channel}: {title}")
            for i in range(3):
                for j in range(3):
                    ax.text(j, i, f"{matrix[i,j]:.3f}", ha="center", va="center",
                            color="white" if matrix[i,j] > .6 else "#172B3A")
    figure.suptitle("Agreement mengukur kesamaan hasil, bukan akurasi", fontsize=13)
    save_figure(figure, "09_model_agreement.png")


def stability_figure():
    table = pd.read_csv(TABLES / "model_stability.csv").drop_duplicates(["channel", "model", "comparison", "variant"])
    figure, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    for ax, (channel, group) in zip(axes, table.groupby("channel")):
        summaries = group[group.comparison.eq("parameter_or_seed")].groupby("model").spearman.agg(["mean", "min", "max"]).reindex(["if", "lof"])
        mean = summaries["mean"].to_numpy()
        bars = ax.bar(["IF: seed/parameter", "LOF: parameter"], mean, color=["#225F86", "#B3652A"])
        ax.errorbar([0, 1], mean, yerr=[mean - summaries["min"], summaries["max"] - mean], fmt="none", ecolor="#172B3A", capsize=7)
        ax.bar_label(bars, labels=[f"{value:.3f}" for value in mean], padding=6)
        sample = group[group.comparison.eq("subsample_training")]
        text = f"IF fit pada 80% sampel: rho={sample.spearman.iloc[0]:.3f}" if len(sample) else "Uji subsampel tidak tersedia"
        ax.set(title=f"{channel}\n{text}", ylabel="Spearman pada log referensi yang sama", ylim=(0, 1.1))
        ax.grid(axis="y", alpha=.18)
    figure.suptitle("Batang: rerata; garis: rentang varian, bukan confidence interval", fontsize=12)
    save_figure(figure, "10_model_stability.png")


def threshold_figure():
    table = pd.read_csv(TABLES / "threshold_sensitivity.csv").query("model == 'consensus'")
    figure, axes = plt.subplots(2, 2, figsize=(11, 8))
    for column, (channel, group) in enumerate(table.groupby("channel")):
        group = group.sort_values("capacity_percentage")
        bars = axes[0, column].bar(group.capacity_percentage.astype(str), group.selected_count, color="#225F86")
        axes[0, column].bar_label(bars, padding=4)
        axes[0, column].set(title=f"{channel}: kuota antrean", xlabel="Kapasitas (%)", ylabel="Jumlah log terpilih")
        axes[0, column].margins(y=.18)
        axes[1, column].plot(group.capacity_percentage, group.score_at_boundary, marker="o", color="#B3652A")
        axes[1, column].axhline(.99, color="#647681", linestyle="--", label="Filter dashboard 0,99")
        axes[1, column].set(title="Batas skor konsensus pada kuota", xlabel="Kapasitas (%)", ylabel="Skor batas")
        axes[1, column].legend()
    figure.suptitle("Kuota adalah asumsi kapasitas, bukan prevalensi anomali", fontsize=13)
    save_figure(figure, "11_threshold_sensitivity.png")


def validation_and_summaries():
    scores = pd.read_csv(TABLES / "anomaly_scores.csv")
    logs = pd.read_csv(ROOT / "data/processed/sanitized_logs.csv")
    features = pd.read_csv(ROOT / "data/processed/transaction_features.csv")
    metadata = json.loads((ROOT / "data/processed/feature_metadata.json").read_text(encoding="utf-8"))
    audit = json.loads((REPORTS / "audit_validation.json").read_text(encoding="utf-8"))
    coverage = [{"channel": channel, **values} for channel, values in metadata["cold_start"].items()]
    pd.DataFrame(coverage).to_csv(TABLES / "feature_coverage_summary.csv", index=False)
    summaries, threshold_counts = [], []
    for channel, group in scores.groupby("channel"):
        for model in [*MODELS, "consensus"]:
            values = group["consensus_score" if model == "consensus" else f"{model}_score"]
            percentiles = group["consensus_score" if model == "consensus" else f"{model}_percentile"]
            summaries.append({"channel": channel, "model": model, "rows": len(group), "min": values.min(), "median": values.median(),
                              "p95": values.quantile(.95), "p99": values.quantile(.99), "max": values.max(), "mean": values.mean(), "std": values.std(ddof=1)})
            threshold_counts.append({"channel": channel, "model": model, "score_threshold": .99,
                                     "rows_at_or_above_threshold": int(percentiles.ge(.99).sum()),
                                     "high_priority_consensus_capacity": int(group.investigation_priority.eq("tinggi").sum()),
                                     "threshold_reference": "mean_of_percentiles" if model == "consensus" else "within_channel_percentile"})
    pd.DataFrame(summaries).to_csv(TABLES / "score_summary.csv", index=False)
    pd.DataFrame(threshold_counts).to_csv(TABLES / "dashboard_threshold_counts.csv", index=False)
    hashes = [hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest() == source["sha256"] for source in metadata["source_manifest"]]
    with sqlite3.connect(f"file:{(ROOT / 'data/processed/norton_bi.db').as_posix()}?mode=ro", uri=True) as connection:
        foreign_keys = len(connection.execute("PRAGMA foreign_key_check").fetchall())
        facts = connection.execute("SELECT COUNT(*) FROM fact_log").fetchone()[0]
        fact_scores = connection.execute("SELECT COUNT(*) FROM fact_anomaly_scores").fetchone()[0]
        runs = connection.execute("SELECT COUNT(*) FROM dim_run").fetchone()[0]
    eligible = int(np.isfinite(features[metadata["core_features"]].to_numpy(dtype=float)).all(axis=1).sum())
    checks = [
        ("Hash sumber sama dengan manifest", sum(hashes), len(hashes)),
        ("Jumlah log pada fact_log", facts, len(logs)),
        ("Log dengan delapan fitur finite", eligible, len(logs)),
        ("Log dengan hasil skor unik", len(scores) if scores.log_key.is_unique and set(scores.log_key) == set(logs.log_key) else -1, len(logs)),
        ("Jumlah fact skor: log x tiga model", fact_scores, len(logs) * 3),
        ("Baseline run: dua kanal x tiga model", runs, 6),
        ("Pelanggaran foreign key", foreign_keys, 0),
        ("Kegagalan parse timestamp nonmissing", audit["timestamp_parse_failures_nonmissing"], 0),
        ("Rekonsiliasi tabel status/harga/harian", sum(audit[key] for key in ["status_count_reconciles", "price_count_reconciles", "daily_count_reconciles"]), 3),
    ]
    result = {"feature_version": metadata["feature_version"], "scope": "data_integrity_not_anomaly_accuracy",
              "checks": [{"check": label, "observed": int(actual), "expected": expected, "passed": actual == expected} for label, actual, expected in checks]}
    if not all(check["passed"] for check in result["checks"]):
        raise RuntimeError("Rekonsiliasi data untuk knowledge belum lulus.")
    (REPORTS / "knowledge_validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    figure, ax = plt.subplots(figsize=(12, 5.7))
    ax.axis("off")
    cells = [[label, f"{actual:,}", f"{expected:,}", "Sesuai"] for label, actual, expected in checks]
    table = ax.table(cellText=cells, colLabels=["Pemeriksaan", "Teramati", "Diharapkan", "Hasil"], colWidths=[.61, .13, .14, .12], loc="center", cellLoc="left")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2.0)
    for (row, _), cell in table.get_celld().items():
        cell.set_edgecolor("#DAE1E5")
        if row == 0:
            cell.set_facecolor("#225F86")
            cell.set_text_props(color="white", weight="bold")
    ax.set_title("Rekonsiliasi aktual: integritas data, bukan akurasi deteksi", pad=18, fontsize=13)
    save_figure(figure, "12_data_validation.png")


if __name__ == "__main__":
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    validation_and_summaries()
    agreement_figure()
    stability_figure()
    threshold_figure()
    print("Bukti knowledge tersimpan: empat gambar, tiga tabel agregat, dan validasi rekonsiliasi.")
