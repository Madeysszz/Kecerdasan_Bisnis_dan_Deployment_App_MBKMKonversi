import hashlib
import json
import platform
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def load_sources(config_path):
    config_path = Path(config_path).resolve()
    root = config_path.parent.parent
    config = json.loads(config_path.read_text(encoding="utf-8"))
    frames, manifest = {}, []
    for name, relative_path in config["sources"].items():
        path = (root / relative_path).resolve()
        frame = pd.read_csv(path, dtype="string", keep_default_na=False)
        frames[name] = frame
        manifest.append({
            "source": name, "path": relative_path, "rows": len(frame),
            "columns": len(frame.columns), "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    return config, frames, manifest


def missing_mask(series, config):
    return series.str.strip().isin(config["missing_tokens"])


def parse_timestamp(series, config):
    normalized = series.str.replace(config["timestamp_artifact"], "", regex=False)
    normalized = normalized.str.replace(r"\+00$", "+0000", regex=True)
    return pd.to_datetime(normalized, format=config["timestamp_format"], errors="coerce", utc=True)


def markdown_table(frame):
    clean = frame.fillna("").astype(str)
    lines = ["| " + " | ".join(clean.columns) + " |", "| " + " | ".join(["---"] * len(clean.columns)) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in clean.itertuples(index=False, name=None))
    return "\n".join(lines)


def inspect_sources(frames, config):
    profiles, dates, summaries, repetitions, temporal, history = [], [], [], [], [], []
    logs = []
    for source, frame in frames.items():
        parsed = {}
        for column in frame:
            series = frame[column]
            missing = missing_mask(series, config)
            values = series[~missing]
            numeric = pd.to_numeric(values, errors="coerce")
            date_column = column.endswith("_at") or column.startswith("subscription_")
            kind = "timestamp_text" if date_column else "numeric_text" if len(values) and numeric.notna().all() else "text"
            profiles.append({
                "source": source, "column": column, "storage_dtype": str(series.dtype),
                "inferred_type": kind, "rows": len(frame), "missing_count": int(missing.sum()),
                "missing_pct": round(100 * missing.mean(), 4), "unique_nonmissing": int(values.nunique()),
            })
            if date_column:
                parsed[column] = parse_timestamp(series, config)
                valid = parsed[column].dropna()
                dates.append({
                    "source": source, "column": column, "missing": int(missing.sum()),
                    "artifact_replacements": int(series.str.contains(config["timestamp_artifact"], regex=False).sum()),
                    "parse_failures_nonmissing": int((~missing & parsed[column].isna()).sum()),
                    "min_utc": valid.min().isoformat() if len(valid) else None,
                    "max_utc": valid.max().isoformat() if len(valid) else None,
                })
        summary = {"source": source, "rows": len(frame), "columns": len(frame.columns),
                   "exact_duplicate_excess": int(frame.duplicated().sum())}
        payload = frame.drop(columns=[c for c in ["id", "Unnamed: 0", "sort"] if c in frame])
        summary["duplicate_excess_without_row_keys"] = int(payload.duplicated().sum())
        summaries.append(summary)
        if source == "package":
            continue
        log = pd.DataFrame({"channel": source, "status": frame["status_activated"],
                            "amount": pd.to_numeric(frame["price"], errors="coerce"),
                            "created_at": parsed["created_at"],
                            "customer_id": frame["customer_id"], "transaction_id": frame["transaction_id"]})
        logs.append(log)
        for key in ["transaction_id", "customer_id"]:
            counts = frame.loc[~missing_mask(frame[key], config)].groupby(key).size()
            repetitions.append({"source": source, "key": key, "unique": len(counts),
                                "repeated_groups": int((counts > 1).sum()),
                                "rows_in_repeated_groups": int(counts[counts > 1].sum()),
                                "max_rows_per_key": int(counts.max())})
        groups = frame.groupby("transaction_id")
        repeated_keys = groups.size().loc[lambda x: x > 1].index
        for column in ["status_activated", "customer_id", "price", "pricing_id", "subscription_start_date", "subscription_expired_at"]:
            values = parsed[column] if column in parsed else frame[column]
            varying = values.groupby(frame["transaction_id"]).nunique().reindex(repeated_keys)
            temporal.append({"source": source, "check": f"repeated_transaction_varies_{column}",
                             "count": int((varying > 1).sum()), "eligible_rows_or_groups": len(repeated_keys)})
        checks = {
            "updated_before_created": ("updated_at", "created_at", "lt"),
            "updated_after_created": ("updated_at", "created_at", "gt"),
            "start_before_created": ("subscription_start_date", "created_at", "lt"),
            "start_after_created": ("subscription_start_date", "created_at", "gt"),
            "expiry_before_start": ("subscription_expired_at", "subscription_start_date", "lt"),
            "cancel_before_start": ("subscription_cancel_date", "subscription_start_date", "lt"),
            "cancel_after_expiry": ("subscription_cancel_date", "subscription_expired_at", "gt"),
        }
        for label, (left, right, operation) in checks.items():
            eligible = parsed[left].notna() & parsed[right].notna()
            count = getattr(parsed[left], operation)(parsed[right]) & eligible
            temporal.append({"source": source, "check": label, "count": int(count.sum()),
                             "eligible_rows_or_groups": int(eligible.sum())})
        cancel_missing = parsed["subscription_cancel_date"].isna()
        temporal.append({"source": source, "check": "cancel_status_without_cancel_date",
                         "count": int((frame.status_activated.eq("CANCEL") & cancel_missing).sum()),
                         "eligible_rows_or_groups": int(frame.status_activated.eq("CANCEL").sum())})
        temporal.append({"source": source, "check": "noncancel_with_cancel_date",
                         "count": int((frame.status_activated.ne("CANCEL") & ~cancel_missing).sum()),
                         "eligible_rows_or_groups": int(frame.status_activated.ne("CANCEL").sum())})
        temporal.append({"source": source, "check": "adjacent_created_decreases_in_file_order",
                         "count": int(parsed["created_at"].diff().dt.total_seconds().lt(0).sum()),
                         "eligible_rows_or_groups": max(len(frame) - 1, 0)})
        ordered = log.sort_values(["customer_id", "created_at"], kind="stable")
        gaps = ordered.groupby("customer_id").created_at.diff().dt.total_seconds()
        counts = frame.groupby("customer_id").size()
        time_groups = log.groupby(["customer_id", "created_at"]).size()
        first_times = log.groupby("customer_id").created_at.transform("min")
        history.append({
            "source": source, "accounts": len(counts), "single_log_accounts": int(counts.eq(1).sum()),
            "accounts_at_least_3_logs": int(counts.ge(3).sum()), "accounts_at_least_5_logs": int(counts.ge(5).sum()),
            "logs_without_strictly_prior_account_timestamp": int(log.created_at.eq(first_times).sum()),
            "same_account_timestamp_groups": int(time_groups.gt(1).sum()),
            "rows_in_same_account_timestamp_groups": int(time_groups[time_groups.gt(1)].sum()),
            "consecutive_intervals": int(gaps.notna().sum()), "zero_intervals": int(gaps.eq(0).sum()),
            "median_gap_seconds": float(gaps.median()), "p95_gap_seconds": float(gaps.quantile(.95)),
            "max_gap_seconds": float(gaps.max()),
        })
    tables = {"column_profile": pd.DataFrame(profiles), "timestamp_quality": pd.DataFrame(dates),
              "source_summary": pd.DataFrame(summaries), "repetition_summary": pd.DataFrame(repetitions),
              "temporal_checks": pd.DataFrame(temporal), "account_history": pd.DataFrame(history)}
    return pd.concat(logs, ignore_index=True), tables


def analytical_tables(logs, frames, config):
    tables = {}
    tables["status_counts"] = logs.groupby(["channel", "status"]).size().rename("log_count").reset_index()
    tables["price_distribution"] = logs.groupby(["channel", "amount"], dropna=False).size().rename("log_count").reset_index()
    prices = []
    for channel, group in logs.groupby("channel"):
        amount = group.amount
        q1, q3 = amount.quantile([.25, .75])
        prices.append({"channel": channel, "count": len(group), "invalid_or_missing": int(amount.isna().sum()),
                       "min": amount.min(), "p25": q1, "median": amount.median(), "p75": q3,
                       "p95": amount.quantile(.95), "p99": amount.quantile(.99), "max": amount.max(),
                       "mean": amount.mean(), "recorded_value_sum": amount.sum(),
                       "zero_count": int(amount.eq(0).sum()), "negative_count": int(amount.lt(0).sum()),
                       "above_upper_iqr_fence": int(amount.gt(q3 + 1.5 * (q3 - q1)).sum())})
    tables["price_summary"] = pd.DataFrame(prices)
    daily = logs.assign(date_utc=logs.created_at.dt.floor("D")).groupby(["channel", "date_utc"]).size().rename("log_count")
    daily_parts = []
    for channel, group in logs.groupby("channel"):
        index = pd.date_range(group.created_at.min().floor("D"), group.created_at.max().floor("D"), freq="D")
        daily_parts.append(daily.loc[channel].reindex(index, fill_value=0).rename_axis("date_utc").reset_index().assign(channel=channel))
    tables["daily_counts"] = pd.concat(daily_parts, ignore_index=True)
    tables["account_activity_distribution"] = logs.groupby(["channel", "customer_id"]).size().rename("logs_per_account").reset_index().groupby(["channel", "logs_per_account"]).size().rename("account_count").reset_index()
    tables["transaction_repetition_distribution"] = logs.groupby(["channel", "transaction_id"]).size().rename("logs_per_transaction_id").reset_index().groupby(["channel", "logs_per_transaction_id"]).size().rename("transaction_id_count").reset_index()
    join_checks = []
    for channel in ["retail", "cobrandgen"]:
        source = frames[channel]
        for left, right in [("pricing_id", "id"), ("package_name", "name"), ("skup", "spku")]:
            if left not in source:
                continue
            values = source.loc[~missing_mask(source[left], config), left]
            target = frames["package"][right]
            join_checks.append({"channel": channel, "log_column": left, "package_column": right,
                                "nonmissing_log_rows": len(values), "distinct_log_values": values.nunique(),
                                "matched_rows_exact": int(values.isin(target).sum()),
                                "target_unique_nonmissing": target[~missing_mask(target, config)].is_unique,
                                "join_validated": False})
    tables["catalog_join_checks"] = pd.DataFrame(join_checks)
    overlap = [{"key": key, "distinct_value_overlap": len(set(frames["retail"][key]) & set(frames["cobrandgen"][key]))}
               for key in ["customer_id", "transaction_id", "pricing_id"]]
    tables["cross_channel_key_overlap"] = pd.DataFrame(overlap)
    return tables


def create_figures(logs, tables, folder):
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False,
                         "axes.spines.right": False, "font.size": 10, "figure.dpi": 120})
    colors = {"retail": "#B3652A", "cobrandgen": "#225F86"}

    def save(fig, name):
        fig.tight_layout()
        fig.savefig(folder / name, dpi=160, bbox_inches="tight", facecolor="white")
        plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for ax, (channel, group) in zip(axes, logs.groupby("channel")):
        ax.hist(np.log1p(group.amount.dropna()), bins=24, color=colors[channel])
        ax.set(title=f"Nilai tercatat: {channel} (n={len(group):,})", xlabel="ln(1 + price), satuan sumber", ylabel="Jumlah log")
    save(fig, "01_value_distribution.png")

    fig, axes = plt.subplots(2, 1, figsize=(11, 6))
    for ax, (channel, daily) in zip(axes, tables["daily_counts"].groupby("channel")):
        ax.plot(daily.date_utc, daily.log_count, color=colors[channel], linewidth=1.4)
        ax.set(title=f"Frekuensi log harian: {channel}", xlabel="Tanggal UTC", ylabel="Jumlah log")
        ax.tick_params(axis="x", labelrotation=20)
    save(fig, "02_daily_activity.png")

    counts = logs.channel.value_counts()
    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(counts.index, counts.values, color=[colors[x] for x in counts.index])
    ax.bar_label(bars, labels=[f"{x:,} ({x / len(logs):.2%})" for x in counts.values], padding=4)
    ax.set(title="Komposisi sumber log", ylabel="Jumlah log", ylim=(0, counts.max() * 1.16))
    save(fig, "03_channel_distribution.png")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for ax, (channel, group) in zip(axes, tables["status_counts"].groupby("channel")):
        bars = ax.bar(group.status, group.log_count, color=colors[channel])
        ax.bar_label(bars, padding=3)
        ax.set(title=f"Status pada ekspor: {channel}", ylabel="Jumlah log", ylim=(0, group.log_count.max() * 1.16))
    save(fig, "04_activation_status.png")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for ax, (channel, group) in zip(axes, tables["account_activity_distribution"].groupby("channel")):
        ax.bar(group.logs_per_account, group.account_count, color=colors[channel])
        ax.set(title=f"Aktivitas per akun: {channel}", xlabel="Jumlah log per customer_id", ylabel="Jumlah akun (skala log)", yscale="log")
    save(fig, "05_account_activity.png")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for ax, (channel, group) in zip(axes, tables["transaction_repetition_distribution"].groupby("channel")):
        ax.bar(group.logs_per_transaction_id, group.transaction_id_count, color=colors[channel])
        ax.set(title=f"Referensi transaksi berulang: {channel}", xlabel="Jumlah log per referensi transaksi", ylabel="Jumlah referensi (skala log)", yscale="log")
    save(fig, "06_repeated_patterns.png")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for ax, (channel, group) in zip(axes, logs.groupby("channel")):
        ordered = group.sort_values(["customer_id", "created_at"], kind="stable")
        intervals = ordered.groupby("customer_id").created_at.diff().dt.total_seconds().dropna()
        ax.hist(np.log1p(intervals / 3600), bins=24, color=colors[channel])
        ax.set(title=f"Interval akun: {channel} (n={len(intervals):,})", xlabel="ln(1 + interval dalam jam)", ylabel="Jumlah interval")
        ax.text(.03, .94, f"Interval nol: {int(intervals.eq(0).sum()):,}", transform=ax.transAxes, ha="left", va="top")
    save(fig, "07_intertransaction_intervals.png")


def write_report(logs, tables, manifest, output):
    sections = [
        "# Audit Data Norton — Tahap 1",
        "Unit observasi adalah satu baris log dalam satu sumber. Audit tidak membentuk label fraud, pembelian unik, pembayaran berhasil, maupun churn. Interpretasi dan keterbatasan tersedia dalam `../../docs/data_audit_interpretation.md`; rancangan tahap berikutnya tersedia dalam `../../docs/architecture_and_experiments.md`.",
        "## Inventaris aktual",
        "Workspace awal hanya berisi tiga CSV. Database `norton_bisnis.db`, kode proyek sebelumnya, repositori Git, `knowledge_dataset_norton.md`, dan `ringkasan_konversi_proyek_basis_data.md` tidak ditemukan. Skema maupun foreign key keenam tabel operasional belum dapat diaudit. Kanal diturunkan dari asal CSV, bukan join tabel channel. Hash input tersimpan di `source_manifest.json`.",
        markdown_table(tables["source_summary"]),
        f"Total log: **{len(logs):,}**. Katalog: **{next(x['rows'] for x in manifest if x['source'] == 'package')} baris**. Tidak ada input yang ditimpa.",
        "## Skema dan missing values",
        "CSV tidak memiliki tipe database; pembacaan memakai teks agar identifier tidak berubah. Tipe inferensi bukan konversi identifier menjadi fitur numerik. Token missing dinyatakan dalam konfigurasi; nol tetap bernilai nol. Kolom pertama cobrandgen tidak bernama dan dibaca sebagai `Unnamed: 0`. Tidak ada imputasi.",
        markdown_table(tables["column_profile"]),
        "Nilai kredensial, atribut pribadi, customer_id, dan transaction_id tidak ditulis ke laporan/tabel keluaran. Profil hanya memuat nama kolom, jumlah missing, dan keunikan. Identifier mentah dipakai sementara untuk grouping di memori, bukan diekspor.",
        "## Harga dan status",
        markdown_table(tables["price_summary"].round(4)),
        "Jumlah price adalah total nilai tercatat pada log. Mata uang, pembayaran terkonfirmasi, refund, pajak, dan kebijakan pendapatan tidak tersedia; jumlah ini bukan pendapatan bersih. Batas IQR hanya deskriptif; seluruh nol dan nilai ekstrem dipertahankan.",
        markdown_table(tables["status_counts"]),
        "Status merupakan nilai pada ekspor. ACTIVE belum membuktikan pembayaran berhasil, sedangkan CANCEL belum membuktikan churn.",
        "## Timestamp dan urutan kejadian",
        "Parser memakai day-first dan UTC eksplisit. Hanya token literal `.-1f` dibuang pada salinan dalam memori; offset +00 dinormalkan ke +0000 sebelum format eksplisit diterapkan. Presisi pecahan detik yang hilang tidak direkonstruksi. Missing dan kegagalan parse nonmissing dicatat terpisah. Baris file tidak diasumsikan kronologis. Waktu grafik tetap UTC.",
        markdown_table(tables["timestamp_quality"]),
        "Pemeriksaan berikut memakai pasangan timestamp yang lengkap atau grup transaction_id berulang sebagai denominator, sesuai nama pemeriksaan:",
        markdown_table(tables["temporal_checks"]),
        "Start sebelum created_at, cancel setelah expiry, atau expiry yang berubah pada ID berulang memerlukan validasi semantik proses. Hasil tersebut tidak otomatis menunjukkan kesalahan atau fraud. Status, updated_at, dan tanggal langganan belum dianggap tersedia saat kejadian.",
        "## Pengulangan dan riwayat akun",
        markdown_table(tables["repetition_summary"]),
        "Exact duplicate memakai seluruh kolom. Pemeriksaan payload kedua mengabaikan hanya id, indeks ekspor, dan sort; tidak ada deduplikasi. Pengulangan ID tidak dianggap pembelian unik atau data rusak.",
        markdown_table(tables["account_history"].round(4)),
        "Unit akun adalah (kanal, customer_id). Interval EDA adalah selisih timestamp berurutan setelah sort. Interval nol tidak menentukan urutan dalam satu detik. Untuk fitur historis, seluruh baris dengan waktu sama harus berbagi riwayat strictly earlier, bukan urutan arbitrer. Awal/akhir observasi merupakan batas ekspor, bukan tanggal akuisisi/churn akun.",
        "## Validasi relasi katalog",
        markdown_table(tables["catalog_join_checks"]),
        markdown_table(tables["cross_channel_key_overlap"]),
        "Tidak ada join katalog yang disahkan. pricing_id tidak dianggap package.id. Dibutuhkan mapping pricing–package yang valid beserta kardinalitas dan masa berlaku; pencocokan nama atau SKU tanpa validasi tidak digunakan.",
        "## EDA",
        "Tujuh gambar pada `../figures/` mencakup distribusi nilai, frekuensi harian, kanal, status, aktivitas akun, pengulangan ID, dan interval akun. Histogram memakai ln(1+x); statistik asli tersimpan pada tabel agregat. Nol log pada hari di dalam cakupan berarti tidak ada baris teramati pada ekspor, bukan bukti tidak ada aktivitas operasional. Hari di luar cakupan setiap sumber tidak diisi nol.",
        "## Keputusan dan kelanjutan",
        "Fungsi audit hanya melakukan analisis deskriptif dan EDA, tanpa imputasi, penghapusan outlier, deduplikasi, join katalog, pemodelan, atau penulisan database. Implementasi fase lanjutan dijalankan terpisah melalui run_pipeline.py; hasil eksperimen aktual tersedia pada model_comparison_report.md. Audit ini tidak menghasilkan label ground truth atau metrik performa berlabel.",
        "Konfirmasi berikutnya meliputi grain log/renewal, makna price/status, kelengkapan ekspor, ketersediaan atribut saat scoring, mapping katalog, dan format timestamp. Perbedaan kanal serta sparsitas riwayat perlu menjadi dasar eksperimen, bukan dihilangkan lewat penggabungan otomatis.",
        "## Reproduksibilitas",
        "Jalankan `python run_audit.py` di folder BI. Konfigurasi memakai path relatif terhadap folder BI; script dapat dipanggil dari direktori lain. Manifest input, versi runtime, salinan konfigurasi, dan hasil rekonsiliasi disimpan. Hash semua CSV diperiksa kembali sesudah audit. Notebook memakai fungsi audit yang sama.",
    ]
    (output / "reports/data_audit_report.md").write_text("\n\n".join(sections) + "\n", encoding="utf-8")


def run_audit(config_path):
    config, frames, manifest = load_sources(config_path)
    root = Path(config_path).resolve().parent.parent
    output = root / config["output_dir"]
    for folder in ["figures", "tables", "reports"]:
        (output / folder).mkdir(parents=True, exist_ok=True)
    logs, tables = inspect_sources(frames, config)
    tables.update(analytical_tables(logs, frames, config))
    for name, table in tables.items():
        table.to_csv(output / "tables" / f"{name}.csv", index=False)
    create_figures(logs, tables, output / "figures")
    write_report(logs, tables, manifest, output)
    versions = {"python": platform.python_version(), "pandas": pd.__version__,
                "numpy": np.__version__, "matplotlib": matplotlib.__version__}
    for entry in manifest:
        actual = hashlib.sha256((root / entry["path"]).read_bytes()).hexdigest()
        if actual != entry["sha256"]:
            raise RuntimeError(f"Input berubah selama audit: {entry['source']}")
    result = {"total_log_rows": len(logs), "raw_inputs_unchanged": True,
              "timestamp_parse_failures_nonmissing": int(tables["timestamp_quality"].parse_failures_nonmissing.sum()),
              "status_count_reconciles": int(tables["status_counts"].log_count.sum()) == len(logs),
              "price_count_reconciles": int(tables["price_distribution"].log_count.sum()) == len(logs),
              "daily_count_reconciles": int(tables["daily_counts"].log_count.sum()) == len(logs),
              "versions": versions}
    (output / "reports/source_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (output / "reports/audit_validation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (output / "reports/audit_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    if not all(result[k] for k in ["status_count_reconciles", "price_count_reconciles", "daily_count_reconciles"]):
        raise RuntimeError("Rekonsiliasi agregat tidak sesuai dengan total log.")
    return {**result, "output_dir": str(output)}
