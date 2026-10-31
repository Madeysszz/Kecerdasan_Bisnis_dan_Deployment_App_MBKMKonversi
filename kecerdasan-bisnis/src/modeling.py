import itertools
import json
import math
import warnings
from importlib.metadata import version
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from pyod.models.ecod import ECOD
from scipy.stats import spearmanr
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import RobustScaler


MODEL_NAMES = ("if", "ecod", "lof")
EVIDENCE_COLUMNS = (
    "source", "source_row_number", "account_key", "reference_key", "created_at",
    "status_snapshot", "amount", "prior_history_count", "prior_account_count_24h",
    "prior_account_count_7d", "prior_reference_count", "window_24h_complete",
    "window_7d_complete", "seconds_since_previous_log", "prior_channel_median_amount",
    "amount_minus_prior_channel_median",
)
FEATURE_LABELS = {
    "log1p_amount": ("Nilai tercatat", "amount"),
    "log1p_prior_account_count_24h": ("Jumlah log akun dalam 24 jam sebelumnya", "prior_account_count_24h"),
    "log1p_prior_account_count_7d": ("Jumlah log akun dalam tujuh hari sebelumnya", "prior_account_count_7d"),
    "log1p_prior_reference_count": ("Pengulangan referensi transaksi sebelum log ini", "prior_reference_count"),
    "hour_sin": ("Pola jam pencatatan UTC", None),
    "hour_cos": ("Pola jam pencatatan UTC", None),
    "weekday_sin": ("Pola hari pencatatan UTC", None),
    "weekday_cos": ("Pola hari pencatatan UTC", None),
}


def _ordinal_ranks(values, keys):
    order = np.lexsort((np.asarray(keys, dtype=str), -np.asarray(values)))
    ranks = np.empty(len(order), dtype=int)
    ranks[order] = np.arange(1, len(order) + 1)
    return ranks


def _correlation(left, right):
    if np.ptp(left) == 0 or np.ptp(right) == 0:
        return None
    value = float(spearmanr(left, right).statistic)
    return value if np.isfinite(value) else None


def _comparison(left, right, keys, requested_k):
    k = min(int(requested_k), len(left))
    a = set(np.flatnonzero(_ordinal_ranks(left, keys) <= k))
    b = set(np.flatnonzero(_ordinal_ranks(right, keys) <= k))
    return {
        "k_requested": int(requested_k), "k_effective": k,
        "intersection_count": len(a & b), "top_k_overlap": len(a & b) / k,
        "jaccard": len(a & b) / len(a | b), "spearman": _correlation(left, right),
    }


def _plain(value):
    if pd.isna(value):
        return None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    return str(value)


def _explanations(rows, feature_values, priorities):
    percentiles = feature_values.rank(method="average", pct=True)
    reasons, evidence = [], []
    raw_columns = [c for c in EVIDENCE_COLUMNS if c in rows and c not in {
        "source", "source_row_number", "account_key", "reference_key", "created_at", "status_snapshot",
    }]
    for position in range(len(rows)):
        row = rows.iloc[position]
        support = {column: _plain(row[column]) for column in raw_columns}
        if "created_at" in row:
            support["created_at_utc"] = _plain(row["created_at"])
        text = []
        amount = support.get("amount")
        median = support.get("prior_channel_median_amount")
        if amount is not None and median is not None and median > 0 and amount >= 3 * median:
            text.append(f"Nilai tercatat {amount / median:.2f} kali median kanal dari log sebelumnya.")
        if support.get("prior_history_count") == 0:
            text.append("Belum ada riwayat akun sebelum timestamp log ini.")
        extreme = []
        for name, percentile in percentiles.iloc[position].items():
            if percentile >= .99 or percentile <= .01:
                extreme.append((min(percentile, 1 - percentile), name, percentile))
        extreme.sort()
        support["marginal_feature_evidence"] = [
            {"feature": name, "value": float(feature_values.iloc[position][name]),
             "within_channel_percentile": float(percentile)}
            for _, name, percentile in extreme[:3]
        ]
        described = set()
        for _, name, percentile in extreme:
            label, raw_name = FEATURE_LABELS.get(name, ("Karakteristik pencatatan", None))
            if label in described:
                continue
            described.add(label)
            if raw_name is None:
                text.append(f"{label}: komponen pola waktu berada pada ekor persentil {100 * percentile:.2f} snapshot kanal; frekuensi jam atau hari tertentu belum diuji.")
            else:
                raw = support.get(raw_name)
                value_text = f" sebesar {raw:g}" if isinstance(raw, (int, float)) else ""
                text.append(f"{label}{value_text} berada pada persentil {100 * percentile:.2f} dalam snapshot kanal.")
            if len(described) == 2:
                break
        if not extreme and priorities.iloc[position] == "tinggi":
            text.append("Prioritas tinggi berasal dari gabungan peringkat model; kombinasi karakteristik perlu ditinjau bersama konteks bisnis, tanpa bukti deviasi marginal ekstrem pada aturan ini.")
        if support.get("window_24h_complete") is False or support.get("window_7d_complete") is False:
            text.append("Jendela riwayat belum seluruhnya tercakup oleh ekspor.")
        if not text:
            text.append("Tidak ada deviasi marginal ekstrem pada aturan penjelasan deskriptif yang digunakan.")
        support["reference"] = "Statistik marginal snapshot kanal; bukan kontribusi fitur model."
        reasons.append(" ".join(text))
        evidence.append(json.dumps(support, ensure_ascii=False, allow_nan=False))
    return reasons, evidence


def run_models(logs, features, feature_columns, config, output_dir):
    output_dir = Path(output_dir)
    if not logs.log_key.is_unique or not features.log_key.is_unique:
        raise ValueError("log_key harus unik pada log dan fitur.")
    if set(logs.log_key) != set(features.log_key):
        raise ValueError("Himpunan log_key pada log dan fitur harus sama.")
    columns = ["log_key", "channel", *[c for c in EVIDENCE_COLUMNS if c in logs]]
    data = logs[columns].merge(
        features[["log_key", "channel", *feature_columns]], on=["log_key", "channel"],
        how="left", validate="one_to_one", indicator=True,
    )
    if not data["_merge"].eq("both").all():
        raise ValueError("Kanal fitur harus sesuai dengan kanal log.")
    data = data.drop(columns="_merge")
    matrix = data[feature_columns].to_numpy(dtype=float)
    if not np.isfinite(matrix).all():
        raise ValueError("Fitur model harus numerik finite; imputasi tidak dilakukan.")

    if_config = config.get("isolation_forest", {})
    tree_counts = if_config.get("n_estimators", [100, 300])
    max_samples = if_config.get("max_samples", [256, 1024])
    seeds = if_config.get("seeds", [11, 42, 73])
    neighbor_counts = config.get("lof", {}).get("n_neighbors", [10, 20, 50])
    eval_config = config.get("evaluation", {})
    top_ks = eval_config.get("top_k", [10, 25, 50])
    threshold_percentages = eval_config.get("threshold_percentages", [1, 2, 5, 10])
    sample_fraction = eval_config.get("sample_fraction", .8)
    if not top_ks or any(int(k) < 1 for k in top_ks):
        raise ValueError("top_k harus memuat bilangan positif.")
    if any(not 0 < float(p) <= 100 for p in threshold_percentages):
        raise ValueError("Persentase threshold harus berada pada (0, 100].")

    agreement, stability, thresholds, parameters, scored = [], [], [], [], []
    evaluation = {
        "analysis_mode": "retrospective_in_sample",
        "versions": {package: version(package) for package in ["scikit-learn", "pyod", "scipy", "joblib", "numpy", "pandas"]},
        "configuration": config,
        "channels": {},
        "priority_policy": "Kapasitas awal: ceil(1% n) tinggi, berikutnya sampai ceil(5% n) sedang, sisanya rendah; bukan prevalensi.",
        "tie_policy": "Persentil dan korelasi memakai average ranks; top-K/prioritas memakai log_key sebagai pemecah tie deterministik.",
        "ecod_protocol": "decision_scores_ dari fit pada snapshot kanal; tidak ada batch holdout atau klaim generalisasi temporal.",
        "temporal_evaluation": "not_performed; no ranking correlation across different time-period observation sets",
        "iteration_note": "Pola waktu memakai fitur resolusi sumber; vektor identik dipertahankan, didiagnosis, dan ukuran tetangga LOF dijaga tanpa jitter atau deduplikasi.",
        "limitation": "Tidak ada ground truth; agreement dan stabilitas tidak membuktikan kebenaran deteksi atau fraud.",
    }
    for channel, group in data.groupby("channel", sort=True):
        group = group.sort_values("log_key", kind="stable").reset_index(drop=True)
        if len(group) < 3:
            raise ValueError(f"Kanal {channel} memerlukan sedikitnya tiga log untuk eksperimen.")
        active = [c for c in feature_columns if group[c].nunique() > 1]
        constant = [c for c in feature_columns if c not in active]
        if not active:
            raise ValueError(f"Seluruh fitur konstan pada kanal {channel}; skor tidak dibuat.")
        scaler = RobustScaler()
        x = scaler.fit_transform(group[active].to_numpy(dtype=float))
        keys = group.log_key.to_numpy()
        if not np.isfinite(x).all():
            raise ValueError(f"Transformasi menghasilkan fitur nonfinite pada kanal {channel}.")
        vector_counts = group.groupby(active, dropna=False).size()
        max_identical = int(vector_counts.max())
        duplicate_diagnostics = {
            "distinct_vectors": len(vector_counts), "max_identical_vectors": max_identical,
            "duplicate_groups": int(vector_counts.gt(1).sum()),
            "rows_in_duplicate_groups": int(vector_counts[vector_counts.gt(1)].sum()),
            "feature_columns": active, "handling": "retain_all_rows; no_jitter; no_deduplication",
        }

        if_variants = list(dict.fromkeys(
            (int(trees), min(int(samples), len(group)), int(seed))
            for trees, samples, seed in itertools.product(tree_counts, max_samples, seeds)
        ))
        lof_requests = list(dict.fromkeys(int(k) for k in neighbor_counts))
        if not if_variants or not lof_requests or min(lof_requests) < 1:
            raise ValueError("Daftar parameter model tidak boleh kosong atau tidak valid.")
        if_models, lof_models = [], []
        channel_parameters = []
        for trees, samples, seed in if_variants:
            model = IsolationForest(n_estimators=trees, max_samples=samples, random_state=seed, contamination="auto")
            model.fit(x)
            score = -model.score_samples(x)
            label = f"trees={trees};max_samples={samples};seed={seed}"
            if_models.append((model, score, label))
            channel_parameters.append({"channel": channel, "model": "if", "variant": label,
                                       "n_estimators": trees, "max_samples": samples, "seed": seed,
                                       "baseline": len(if_models) == 1})
        ecod = ECOD(n_jobs=1)
        ecod.fit(x)
        ecod_score = ecod.decision_scores_.copy()
        channel_parameters.append({"channel": channel, "model": "ecod", "variant": "empirical_snapshot",
                                   "baseline": True, "threshold_used_for_priority": False})
        lof_diagnostics = []
        for requested_neighbors in lof_requests:
            clipped = min(requested_neighbors, len(group) - 1)
            neighbors = min(len(group) - 1, max(clipped, max_identical + 1)) if max_identical >= clipped else clipped
            model = LocalOutlierFactor(n_neighbors=neighbors, novelty=False, contamination="auto")
            with warnings.catch_warnings(record=True) as captured:
                warnings.simplefilter("always")
                model.fit(x)
            fit_warnings = [str(warning.message) for warning in captured]
            diagnostic = {
                "requested_n_neighbors": requested_neighbors, "effective_n_neighbors": neighbors,
                "adjustment_reason": "identical_vector_guard" if neighbors > clipped else
                    "bounded_by_channel_size" if clipped < requested_neighbors else "none",
                "warnings": fit_warnings,
            }
            lof_diagnostics.append(diagnostic)
            if any("incorrect results" in message.lower() for message in fit_warnings):
                raise ValueError(f"LOF tidak layak pada kanal {channel}, requested k={requested_neighbors}, effective k={neighbors}: {'; '.join(fit_warnings)}")
            score = -model.negative_outlier_factor_
            label = f"requested_k={requested_neighbors};n_neighbors={neighbors};novelty=False"
            if not any(previous.n_neighbors == neighbors for previous, _, _ in lof_models):
                lof_models.append((model, score, label))
            channel_parameters.append({"channel": channel, "model": "lof", "variant": label,
                                       "n_neighbors": neighbors, "requested_n_neighbors": requested_neighbors,
                                       "adjustment_reason": diagnostic["adjustment_reason"],
                                       "fit_warnings": json.dumps(fit_warnings, ensure_ascii=False),
                                       "baseline": requested_neighbors == lof_requests[0]})
        parameters.extend(channel_parameters)
        raw_scores = {"if": if_models[0][1], "ecod": ecod_score, "lof": lof_models[0][1]}
        for name, values in raw_scores.items():
            if not np.isfinite(values).all():
                raise ValueError(f"Skor {name} tidak finite pada kanal {channel}.")

        result = group[["log_key", "channel"]].copy()
        for name, values in raw_scores.items():
            result[f"{name}_score"] = values
            result[f"{name}_percentile"] = pd.Series(values).rank(method="average", pct=True)
            result[f"{name}_rank"] = pd.Series(values).rank(method="average", ascending=False)
        result["consensus_score"] = result[[f"{name}_percentile" for name in MODEL_NAMES]].mean(axis=1)
        result["anomaly_rank"] = _ordinal_ranks(result.consensus_score.to_numpy(), keys)
        high_count, medium_count = math.ceil(len(group) * .01), math.ceil(len(group) * .05)
        result["investigation_priority"] = np.select(
            [result.anomaly_rank <= high_count, result.anomaly_rank <= medium_count],
            ["tinggi", "sedang"], default="rendah",
        )
        result["explanation_kind"] = "descriptive_statistical"
        result["reasons"], result["supporting_evidence"] = _explanations(
            group, group[active], result.investigation_priority,
        )
        scored.append(result)

        for left, right in itertools.combinations(MODEL_NAMES, 2):
            for k in top_ks:
                agreement.append({"channel": channel, "model_left": left, "model_right": right,
                                  **_comparison(raw_scores[left], raw_scores[right], keys, k)})
        for name, variants in [("if", if_models), ("lof", lof_models)]:
            baseline = variants[0][1]
            for _, values, label in variants[1:]:
                for k in top_ks:
                    stability.append({"channel": channel, "model": name, "comparison": "parameter_or_seed",
                                      "baseline_variant": variants[0][2], "variant": label,
                                      "reference_rows": len(group),
                                      **_comparison(baseline, values, keys, k)})
        sample_performed = 0 < sample_fraction < 1 and math.floor(sample_fraction * len(group)) >= 3
        if sample_performed:
            rng = np.random.default_rng(int(seeds[0]))
            sample_indices = rng.choice(len(group), size=math.floor(sample_fraction * len(group)), replace=False)
            sample_scaler = RobustScaler()
            sample_scaler.fit(group.iloc[sample_indices][active].to_numpy(dtype=float))
            sample_x = sample_scaler.transform(group[active].to_numpy(dtype=float))
            trees, samples, seed = if_variants[0]
            sample_model = IsolationForest(n_estimators=trees, max_samples=min(samples, len(sample_indices)),
                                           random_state=seed, contamination="auto")
            sample_model.fit(sample_x[sample_indices])
            sample_score = -sample_model.score_samples(sample_x)
            for k in top_ks:
                stability.append({"channel": channel, "model": "if", "comparison": "subsample_training",
                                  "baseline_variant": if_models[0][2], "variant": f"fraction={sample_fraction}",
                                  "reference_rows": len(group), "sample_train_rows": len(sample_indices),
                                  **_comparison(raw_scores["if"], sample_score, keys, k)})

        for name, values in {**raw_scores, "consensus": result.consensus_score.to_numpy()}.items():
            ranks = _ordinal_ranks(values, keys)
            for percentage in threshold_percentages:
                capacity = max(1, math.ceil(len(group) * float(percentage) / 100))
                boundary = float(values[ranks == capacity][0])
                thresholds.append({"channel": channel, "model": name, "capacity_percentage": percentage,
                                   "selected_count": capacity, "score_at_boundary": boundary,
                                   "rows_tied_at_boundary": int(np.count_nonzero(values == boundary)),
                                   "rows_above_boundary": int(np.count_nonzero(values > boundary)),
                                   "selection_rule": "ordinal_capacity_with_log_key_tiebreak"})
        model_dir = output_dir / "models" / str(channel)
        model_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(if_models[0][0], model_dir / "isolation_forest.joblib")
        joblib.dump(ecod, model_dir / "ecod.joblib")
        joblib.dump(lof_models[0][0], model_dir / "lof.joblib")
        joblib.dump({"scaler": scaler, "feature_columns": active, "constant_features": constant,
                     "training_log_keys": keys.tolist(), "analysis_mode": "retrospective_in_sample"},
                    model_dir / "preprocessing.joblib")
        channel_agreement = [r["spearman"] for r in agreement if r["channel"] == channel and r["spearman"] is not None]
        stability_by_model = {}
        for name in ["if", "lof"]:
            values = [r["spearman"] for r in stability
                      if r["channel"] == channel and r["model"] == name
                      and r["comparison"] == "parameter_or_seed" and r["spearman"] is not None]
            stability_by_model[name] = {
                "mean_spearman": float(np.mean(values)) if values else None,
                "min_spearman": min(values) if values else None,
            }
        agreement_range = [min(channel_agreement), max(channel_agreement)] if channel_agreement else None
        summaries = [f"{name.upper()} rata-rata korelasi stabilitas {stats['mean_spearman']:.3f}"
                     for name, stats in stability_by_model.items() if stats["mean_spearman"] is not None]
        rationale = "; ".join(summaries) + "." if summaries else "Variasi konfigurasi belum cukup untuk menilai stabilitas."
        if agreement_range:
            rationale += f" Korelasi antar model berada pada {agreement_range[0]:.3f}–{agreement_range[1]:.3f}."
        rationale += f" Terdapat {len(vector_counts)} vektor fitur berbeda dari {len(group)} log; blok identik terbesar {max_identical} baris."
        if any(d["adjustment_reason"] == "identical_vector_guard" for d in lof_diagnostics):
            rationale += " Ukuran tetangga LOF dinaikkan secara tercatat untuk menghindari lingkungan yang seluruhnya identik."
        means = {name: stats["mean_spearman"] for name, stats in stability_by_model.items()
                 if stats["mean_spearman"] is not None}
        if len(means) == 2:
            if abs(means["if"] - means["lof"]) < .01:
                rationale += " Stabilitas rata-rata IF dan LOF pada konfigurasi yang diuji berdekatan."
            else:
                more_stable = max(means, key=means.get).upper()
                rationale += f" {more_stable} lebih konsisten secara rata-rata pada variasi yang diuji; cakupan variasi kedua algoritma berbeda sehingga ini bukan bukti model terbaik."
        rationale += " Tinjau kasus yang disepakati maupun yang berbeda antar model; hasil ini belum mengukur ketepatan investigasi."
        evaluation["channels"][str(channel)] = {
            "rows": len(group), "active_features": active, "constant_features": constant,
            "baseline_parameters": [p for p in channel_parameters if p["baseline"]],
            "experiment_count": len(channel_parameters), "high_priority_count": high_count,
            "medium_priority_count": medium_count - high_count,
            "sample_stability": "common_full_snapshot_reference; overlaps_training; not holdout performance"
                if sample_performed else "not_performed; disabled_or_insufficient_sample",
            "agreement_spearman_range": agreement_range,
            "parameter_stability": stability_by_model,
            "duplicate_vector_diagnostics": duplicate_diagnostics,
            "lof_suitability": {"status": "fit_without_incorrect_results_warning", "variants": lof_diagnostics},
            "recommendation_rationale": rationale,
            "scaler": "RobustScaler fitted on the same retrospective channel snapshot",
        }

    scores = pd.concat(scored, ignore_index=True)
    table_dir, report_dir = output_dir / "tables", output_dir / "reports"
    table_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    for name, records in [
        ("model_agreement", agreement), ("model_stability", stability),
        ("threshold_sensitivity", thresholds), ("experiment_parameters", parameters),
    ]:
        pd.DataFrame(records).to_csv(table_dir / f"{name}.csv", index=False)
    correlations = [r["spearman"] for r in agreement if r["spearman"] is not None]
    evaluation["agreement_spearman_range"] = [min(correlations), max(correlations)] if correlations else None
    stability_values = [r["spearman"] for r in stability if r["spearman"] is not None]
    evaluation["stability_spearman_range"] = [min(stability_values), max(stability_values)] if stability_values else None
    evaluation["recommendation"] = (
        "Gunakan konsensus sebagai antrean tinjauan awal dan periksa perbedaan antar model. "
        "Rentang agreement/stabilitas terlampir hanya mengukur konsistensi snapshot; "
        "tidak cukup untuk memilih model terbaik atau menyimpulkan fraud. "
        "Retail dengan sedikit log dan konsentrasi akun tinggi memerlukan penafsiran eksploratif."
    )
    (report_dir / "model_evaluation.json").write_text(
        json.dumps(evaluation, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8",
    )
    return scores, evaluation
