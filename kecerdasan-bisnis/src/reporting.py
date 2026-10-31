import json
import sqlite3

import matplotlib.pyplot as plt
import pandas as pd

from src.audit import markdown_table


def store_model_scores(root, scores, config):
    with sqlite3.connect(root / "data/processed/norton_bi.db") as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript("""
            DROP TABLE IF EXISTS fact_anomaly_scores;
            DROP TABLE IF EXISTS dim_run;
            DROP TABLE IF EXISTS dim_model;
            CREATE TABLE dim_model (
                model_key TEXT PRIMARY KEY,
                model_name TEXT NOT NULL
            );
            CREATE TABLE dim_run (
                run_key TEXT PRIMARY KEY,
                model_key TEXT NOT NULL REFERENCES dim_model(model_key),
                channel TEXT NOT NULL,
                analysis_mode TEXT NOT NULL,
                parameters_json TEXT NOT NULL
            );
            CREATE TABLE fact_anomaly_scores (
                log_key TEXT NOT NULL REFERENCES fact_log(log_key),
                run_key TEXT NOT NULL REFERENCES dim_run(run_key),
                raw_score REAL NOT NULL,
                percentile REAL NOT NULL,
                anomaly_rank REAL NOT NULL,
                PRIMARY KEY (log_key, run_key)
            );
        """)
        names = {"if": "Isolation Forest", "ecod": "ECOD", "lof": "Local Outlier Factor"}
        connection.executemany("INSERT INTO dim_model VALUES (?, ?)", names.items())
        parameters = pd.read_csv(root / "outputs/tables/experiment_parameters.csv")
        for channel, group in scores.groupby("channel"):
            for model in names:
                run_key = f"{channel}:{model}:baseline"
                runs = parameters[parameters.channel.eq(channel) & parameters.model.eq(model)]
                records = runs.astype(object).where(runs.notna(), None).to_dict(orient="records")
                run_config = {"experiment_config": config, "recorded_runs": records}
                connection.execute("INSERT INTO dim_run VALUES (?, ?, ?, ?, ?)",
                                   (run_key, model, channel, "retrospective_in_sample", json.dumps(run_config, allow_nan=False)))
                rows = [(row.log_key, run_key, float(getattr(row, f"{model}_score")),
                         float(getattr(row, f"{model}_percentile")), float(getattr(row, f"{model}_rank")))
                        for row in group.itertuples(index=False)]
                connection.executemany("INSERT INTO fact_anomaly_scores VALUES (?, ?, ?, ?, ?)", rows)
        if connection.execute("PRAGMA foreign_key_check").fetchall():
            raise RuntimeError("Relasi data mart skor tidak valid.")


def write_results(root, logs, scores, evaluation, metadata):
    output = root / "outputs"
    agreement = pd.read_csv(output / "tables/model_agreement.csv")
    stability = pd.read_csv(output / "tables/model_stability.csv")
    thresholds = pd.read_csv(output / "tables/threshold_sensitivity.csv")
    parameters = pd.read_csv(output / "tables/experiment_parameters.csv")
    merged = logs.merge(scores.drop(columns="channel"), on="log_key", validate="one_to_one")
    overview = merged.groupby("channel").agg(log_count=("log_key", "size"), accounts=("account_key", "nunique"),
                                             recorded_value=("amount", "sum"))
    priority = merged.groupby(["channel", "investigation_priority"]).size().rename("log_count").reset_index()
    top = merged.sort_values(["channel", "anomaly_rank"]).groupby("channel").head(10)
    top_columns = ["log_key", "channel", "amount", "status_snapshot", "consensus_score", "anomaly_rank",
                   "investigation_priority", "reasons", "supporting_evidence"]
    top[top_columns].to_csv(output / "tables/top_investigation_cases.csv", index=False)
    top_summary = top.groupby("channel").agg(
        selected_log_count=("log_key", "size"), median_recorded_amount=("amount", "median"),
        min_consensus_score=("consensus_score", "min"), max_consensus_score=("consensus_score", "max"),
    ).reset_index()
    comparison_summary = []
    for channel, result in evaluation["channels"].items():
        duplicates = result.get("duplicate_vector_diagnostics", {})
        stability_summary = result.get("parameter_stability", {})
        comparison_summary.append({"channel": channel, "distinct_feature_vectors": duplicates.get("distinct_vectors"),
                                   "max_identical_vectors": duplicates.get("max_identical_vectors"),
                                   "if_mean_stability_spearman": stability_summary.get("if", {}).get("mean_spearman"),
                                   "lof_mean_stability_spearman": stability_summary.get("lof", {}).get("mean_spearman")})
    fig, axes = plt.subplots(2, 3, figsize=(13, 7))
    for row, (channel, group) in zip(axes, scores.groupby("channel")):
        for ax, model, label in zip(row, ["if", "ecod", "lof"], ["Isolation Forest", "ECOD", "LOF"]):
            ax.hist(group[f"{model}_score"], bins=35, color="#225F86" if channel == "cobrandgen" else "#B3652A")
            ax.set(title=f"{channel}: {label}", xlabel="Skor mentah berorientasi anomali", ylabel="Jumlah log")
    fig.tight_layout()
    fig.savefig(output / "figures/08_model_score_distributions.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    sections = [
        "# Metodologi dan Hasil Pemodelan Norton",
        "Eksperimen ini merupakan analisis retrospektif in-sample atas snapshot log, bukan pengukuran generalisasi atau deteksi fraud. Ketiga model di-fit dan diberi skor pada set observasi yang sama untuk membandingkan ranking tanpa ground truth. Data tidak diimputasi, dideduplikasi, atau dibersihkan dengan menghapus nilai ekstrem. Basis data operasional tidak ditulis.",
        "## Populasi, fitur, dan preprocessing", markdown_table(overview.reset_index()),
        "Unit analisis adalah log per kanal. Akun dan referensi transaksi memakai pseudonim yang deterministik dalam snapshot sumber yang sama. Price tetap disebut nilai tercatat. Fitur historis menghitung waktu strictly earlier; baris dengan timestamp sama tidak saling memasukkan histori. Interval dan median harga historis yang belum tersedia tetap missing sebagai bukti konteks, dan tidak menjadi input model inti.",
        "Fitur inti: " + ", ".join(f"`{column}`" for column in metadata["core_features"]) + ". Rincian rumus, coverage, dan unit snapshot akun tersedia pada `../../docs/feature_dictionary.md`. Fitur status/update/tanggal langganan, identifier, dan atribut pribadi tidak menjadi input model.",
        "Transformasi log1p diterapkan pada nilai/jumlah nonnegatif. RobustScaler di-fit per kanal dan fitur konstan dikeluarkan sesuai metadata run. Karena evaluasi utama retrospektif, referensi model/preprocessing mencakup snapshot fit tersebut; hasilnya tidak boleh disebut penilaian masa depan. Fitur akun tersedia sebagai snapshot terpisah, tanpa memaksakan model akun pada riwayat yang jarang.",
        "## Protokol tiga model",
        "Isolation Forest memakai kebalikan score_samples agar skor lebih tinggi berarti lebih anomali. LOF memakai novelty=False dan kebalikan negative_outlier_factor_ pada observasi fit. ECOD memakai decision_scores_ pada observasi fit. Tidak ada scoring holdout gabungan ECOD yang diklaim sebagai replay temporal. [Dokumentasi scikit-learn](https://scikit-learn.org/stable/modules/outlier_detection.html) dan [implementasi resmi ECOD](https://pyod.readthedocs.io/en/latest/_modules/pyod/models/ecod.html) menjadi rujukan kontrak skor.",
        "Skor mentah tidak dibandingkan langsung lintas algoritma atau kanal. Persentil memakai average ranks pada set per kanal dan bukan probabilitas fraud. Konsensus adalah rerata persentil IF, ECOD, dan LOF; ini merupakan antrean tinjauan yang transparan, bukan model terlatih keempat atau bukti kebenaran hasil.",
        "## Parameter dan stabilitas", markdown_table(parameters.round(5)), markdown_table(stability.round(5)),
        "Stabilitas membandingkan log_key yang sama. Perubahan seed hanya berlaku pada model stokastik; perubahan parameter dan sampel referensi dilaporkan menurut eksperimen aktual. Evaluasi temporal pada observasi masa depan dan eksperimen sintetis belum dilakukan. Konfigurasi serta versi paket disimpan dalam model_evaluation.json dan artefak model.",
        "## Agreement dan sensitivitas ambang", markdown_table(agreement.round(5)), markdown_table(thresholds.round(5)),
        "Top-K memakai aturan tie deterministik dan korelasi memakai average ranks sesuai protokol evaluasi. Agreement tinggi hanya berarti hasil konsisten. Banyaknya log yang ditandai mengikuti aturan threshold atau kapasitas tinjauan, bukan estimasi jumlah anomali nyata.",
        "## Prioritas dan bukti investigasi", markdown_table(priority),
        "Prioritas tinggi dialokasikan pada ceil(1% × jumlah log kanal), sedang hingga ceil(5%), dan rendah untuk sisanya berdasarkan ranking konsensus. Ini adalah asumsi kapasitas awal yang dapat disesuaikan; ia tidak menyatakan prevalensi fraud. Ambang skor kontinu pada dashboard merupakan filter tambahan dan tidak identik dengan kuota peringkat.",
        "Ringkasan berikut mencakup sepuluh log dengan peringkat konsensus tertinggi per kanal, atau seluruh log bila jumlahnya kurang dari sepuluh. Contoh per log tidak ditampilkan di dokumen ini.",
        markdown_table(top_summary.round(5)),
        "Kasus individual dan bukti lengkap tetap diproduksi pada CSV internal lokal top_investigation_cases.csv dan anomaly_scores.csv untuk dashboard serta investigasi berizin. Dokumen ini hanya menampilkan agregat. `explanation_kind` menandai alasan deskriptif. Deviasi harga, jumlah log historis, interval, dan konteks pengulangan dapat dihitung ulang; alasan tersebut tidak diklaim sebagai kontribusi fitur yang dihitung dari model. Kasus tanpa deviasi marginal ekstrem memerlukan pemeriksaan kombinasi fitur lebih lanjut; kelangkaan kombinasi belum diuji secara terpisah.",
        "## Rekomendasi dan batas interpretasi", str(evaluation.get("recommendation", "Bandingkan stabilitas, agreement, cakupan, dan bukti bisnis sebelum menetapkan model operasional.")),
        markdown_table(pd.DataFrame(comparison_summary).round(5)),
        "\n\n".join(f"**{channel}**: {result.get('recommendation_rationale', '')}" for channel, result in evaluation["channels"].items()),
        "Encoding waktu versi 2 mempertahankan menit/detik yang tersedia pada sumber. Uji awal dengan pembulatan jam menghasilkan banyak vektor identik dan peringatan LOF; hasil akhir dihitung ulang memakai versi 2 tanpa deduplikasi atau jitter. Metadata mencatat blok fitur identik, requested/effective k, serta warning setiap varian. k disesuaikan bila blok identik terlalu besar; warning hasil tidak valid menghentikan run.",
        "Rekomendasi ini dibatasi pada konsistensi ranking snapshot. Retail berukuran kecil dan terkonsentrasi pada beberapa akun sehingga bersifat eksploratif. Belum tersedia label hasil investigasi, bukti pembayaran, mapping pricing–package, atau riwayat status yang memungkinkan klaim fraud, churn, pendapatan bersih, atau accuracy/precision/recall/F1/ROC-AUC pada anomali nyata.",
        "## Keputusan bisnis yang didukung",
        "Analis dapat memulai dari antrean prioritas per kanal, memeriksa bukti statistik dan riwayat akun, lalu mengonfirmasi proses bisnis pada pemilik data. Pemeriksaan tanggal CANCEL yang tidak lengkap dan pola pencatatan berulang merupakan agenda kualitas data tersendiri. Tindak lanjut kasus harus mencatat hasil tinjauan manusia sebelum menjadi label evaluasi yang sah.",
    ]
    (output / "reports/model_comparison_report.md").write_text("\n\n".join(sections) + "\n", encoding="utf-8")
