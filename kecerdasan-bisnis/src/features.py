import json
import sqlite3
from contextlib import closing
from pathlib import Path

import numpy as np
import pandas as pd

from src.audit import load_sources, missing_mask, parse_timestamp


CORE_FEATURES = [
    "log1p_amount", "log1p_prior_account_count_24h", "log1p_prior_account_count_7d",
    "log1p_prior_reference_count", "hour_sin", "hour_cos", "weekday_sin", "weekday_cos",
]


def _surrogates(series, channel, kind, config):
    values = series.mask(missing_mask(series, config))
    codes, _ = pd.factorize(values, sort=False)
    return pd.Series([f"{channel}:{kind}:{code + 1:06d}" if code >= 0 else pd.NA
                      for code in codes], index=series.index, dtype="string")


def _history(logs, key, prefix, windows=False):
    logs[f"prior_{prefix}_count"] = np.nan
    if windows:
        logs["prior_account_count_24h"] = np.nan
        logs["prior_account_count_7d"] = np.nan
        logs["seconds_since_previous_log"] = np.nan
    known = logs.loc[logs[key].notna() & logs.created_at.notna()]
    for _, group in known.groupby(["channel", key], sort=False):
        ordered = group.sort_values("created_at", kind="stable")
        times = ordered.created_at.to_numpy(dtype="datetime64[ns]").astype(np.int64)
        prior = np.searchsorted(times, times, side="left")
        logs.loc[ordered.index, f"prior_{prefix}_count"] = prior
        if windows:
            for label, seconds in [("24h", 86400), ("7d", 604800)]:
                first = np.searchsorted(times, times - seconds * 10**9, side="left")
                logs.loc[ordered.index, f"prior_account_count_{label}"] = prior - first
            gaps = np.full(len(times), np.nan)
            has_prior = prior > 0
            gaps[has_prior] = (times[has_prior] - times[prior[has_prior] - 1]) / 10**9
            logs.loc[ordered.index, "seconds_since_previous_log"] = gaps


def _account_snapshots(logs):
    snapshots = []
    for channel, source in logs.groupby("channel", sort=False):
        valid = source.loc[source.created_at.notna()]
        if valid.empty:
            continue
        source_start, source_end = valid.created_at.min(), valid.created_at.max()
        cutoff = source_end + pd.Timedelta(seconds=1)
        known = valid.loc[valid.account_key.notna() & valid.created_at.lt(cutoff)]
        for account_key, group in known.groupby("account_key", sort=False):
            unique_times = group.created_at.drop_duplicates().sort_values()
            median_interval = (unique_times.diff().dt.total_seconds().median()
                               if len(unique_times) >= 3 else np.nan)
            snapshots.append({
                "channel": channel, "account_key": account_key, "cutoff_utc": cutoff,
                "observed_log_count": len(group), "observed_reference_count": group.reference_key.nunique(),
                "amount_observation_count": int(group.amount.notna().sum()),
                "amount_mean": group.amount.mean(), "amount_std": group.amount.std(ddof=1),
                "unique_timestamp_count": len(unique_times), "median_interval_seconds": median_interval,
                "first_created_at": unique_times.iloc[0], "last_created_at": unique_times.iloc[-1],
                "account_observation_days": (unique_times.iloc[-1] - unique_times.iloc[0]).total_seconds() / 86400,
                "source_coverage_start": source_start, "source_coverage_end": source_end,
                "source_observation_days": (source_end - source_start).total_seconds() / 86400,
            })
    columns = ["channel", "account_key", "cutoff_utc", "observed_log_count", "observed_reference_count",
               "amount_observation_count", "amount_mean", "amount_std", "unique_timestamp_count",
               "median_interval_seconds", "first_created_at", "last_created_at", "account_observation_days",
               "source_coverage_start", "source_coverage_end", "source_observation_days"]
    return pd.DataFrame(snapshots, columns=columns)


def build_features(config_path):
    config, sources, manifest = load_sources(config_path)
    parts = []
    for channel, frame in sources.items():
        if channel == "package":
            continue
        row_numbers = np.arange(1, len(frame) + 1)
        parts.append(pd.DataFrame({
            "log_key": [f"{channel}:{number:06d}" for number in row_numbers],
            "source": channel, "source_row_number": row_numbers, "channel": channel,
            "account_key": _surrogates(frame.customer_id, channel, "account", config),
            "reference_key": _surrogates(frame.transaction_id, channel, "reference", config),
            "created_at": parse_timestamp(frame.created_at, config),
            "status_snapshot": frame.status_activated.mask(missing_mask(frame.status_activated, config)),
            "amount": pd.to_numeric(frame.price.mask(missing_mask(frame.price, config)), errors="coerce"),
        }))
    logs = pd.concat(parts, ignore_index=True)
    logs["amount"] = logs.amount.astype(float).where(np.isfinite(logs.amount.astype(float)))
    _history(logs, "account_key", "history", windows=True)
    _history(logs, "reference_key", "reference")
    logs["prior_channel_median_amount"] = np.nan
    logs["window_24h_complete"] = pd.Series(pd.NA, index=logs.index, dtype="boolean")
    logs["window_7d_complete"] = pd.Series(pd.NA, index=logs.index, dtype="boolean")
    cold_start, cutoffs = {}, {}
    for channel, source in logs.groupby("channel", sort=False):
        valid = source.loc[source.created_at.notna()].sort_values("created_at", kind="stable")
        if not valid.empty:
            times = valid.created_at.to_numpy(dtype="datetime64[ns]").astype(np.int64)
            prior = np.searchsorted(times, times, side="left")
            medians = valid.amount.expanding(min_periods=1).median().shift(1).to_numpy()
            logs.loc[valid.index, "prior_channel_median_amount"] = medians[prior]
            for label, seconds in [("24h", 86400), ("7d", 604800)]:
                complete = valid.created_at.sub(valid.created_at.min()).ge(pd.Timedelta(seconds=seconds))
                logs.loc[valid.index, f"window_{label}_complete"] = complete.to_numpy()
            cutoffs[channel] = (valid.created_at.max() + pd.Timedelta(seconds=1)).isoformat()
        cold_start[channel] = {
            "no_prior_account_history": int(logs.loc[source.index, "prior_history_count"].eq(0).sum()),
            "missing_previous_log_seconds": int(logs.loc[source.index, "seconds_since_previous_log"].isna().sum()),
            "missing_prior_channel_median": int(logs.loc[source.index, "prior_channel_median_amount"].isna().sum()),
            "incomplete_window_24h": int(logs.loc[source.index, "window_24h_complete"].eq(False).sum()),
            "incomplete_window_7d": int(logs.loc[source.index, "window_7d_complete"].eq(False).sum()),
        }
    logs["amount_minus_prior_channel_median"] = logs.amount - logs.prior_channel_median_amount
    features = logs[["log_key", "channel"]].copy()
    features["log1p_amount"] = np.log1p(logs.amount.where(logs.amount.ge(0)))
    for count in ["prior_account_count_24h", "prior_account_count_7d", "prior_reference_count"]:
        features[f"log1p_{count}"] = np.log1p(logs[count])
    hour = logs.created_at.dt.hour + logs.created_at.dt.minute / 60 + logs.created_at.dt.second / 3600
    weekday = logs.created_at.dt.day_of_week
    for name, values, period in [("hour", hour, 24), ("weekday", weekday, 7)]:
        features[f"{name}_sin"] = np.sin(2 * np.pi * values / period)
        features[f"{name}_cos"] = np.cos(2 * np.pi * values / period)
    logs["core_features_eligible"] = np.isfinite(features[CORE_FEATURES].to_numpy(dtype=float)).all(axis=1)
    accounts = _account_snapshots(logs)
    metadata = {
        "feature_version": "2_time_of_day_seconds",
        "core_features": CORE_FEATURES,
        "history_policy": "created_at < current timestamp; windows [t-window, t); equal timestamps share history",
        "identity_policy": "source-scoped first-occurrence surrogates; no persisted original identifier mapping",
        "window_completeness_policy": "elapsed time from source minimum created_at; observed boundary only, not ingestion assurance",
        "snapshot_cutoff_utc": cutoffs, "source_manifest": manifest,
        "eligibility": {"total_logs": len(logs), "finite_core_logs": int(logs.core_features_eligible.sum()),
                        "excluded_core_logs": int((~logs.core_features_eligible).sum()),
                        "missing_timestamp": int(logs.created_at.isna().sum()),
                        "invalid_or_missing_amount": int((logs.amount.isna() | logs.amount.lt(0)).sum()),
                        "missing_account_key": int(logs.account_key.isna().sum()),
                        "missing_reference_key": int(logs.reference_key.isna().sum())},
        "cold_start": cold_start,
        "exclusions": ["status_snapshot", "subscription cancellation/expiry fields", "original identifiers",
                       "PII and credentials", "package attributes without validated mapping", "future or same-time history"],
        "evidence_only": ["prior_history_count", "window_24h_complete", "window_7d_complete",
                          "seconds_since_previous_log", "prior_channel_median_amount", "amount_minus_prior_channel_median"],
        "missing_policy": "no imputation; unknown evidence remains missing; observed empty history count is zero",
        "account_model_ready": False,
        "account_model_limitation": "snapshot is descriptive; sparse per-account history and no validated fraud labels",
    }
    return logs, features, accounts, metadata


def _sql_frame(frame):
    output = frame.copy()
    for column in output:
        if isinstance(output[column].dtype, pd.DatetimeTZDtype):
            output[column] = output[column].map(lambda value: value.isoformat() if pd.notna(value) else None)
    return output


def save_artifacts(logs, features, accounts, metadata, project_root):
    folder = Path(project_root).resolve() / "data" / "processed"
    folder.mkdir(parents=True, exist_ok=True)
    for name, frame in [("sanitized_logs", logs), ("transaction_features", features), ("account_features", accounts)]:
        frame.to_csv(folder / f"{name}.csv", index=False)
    (folder / "feature_metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    database = folder / "norton_bi.db"
    numeric_columns = ["prior_history_count", "prior_account_count_24h", "prior_account_count_7d", "prior_reference_count",
                       "seconds_since_previous_log", "prior_channel_median_amount", "amount_minus_prior_channel_median"]
    numeric_sql = ",\n".join(f"{column} REAL" for column in numeric_columns + CORE_FEATURES)
    schema = f"""
        DROP TABLE IF EXISTS fact_anomaly_scores;
        DROP TABLE IF EXISTS dim_run;
        DROP TABLE IF EXISTS dim_model;
        DROP TABLE IF EXISTS fact_account_snapshot;
        DROP TABLE IF EXISTS fact_log;
        DROP TABLE IF EXISTS dim_account;
        DROP TABLE IF EXISTS dim_status_snapshot;
        DROP TABLE IF EXISTS dim_date;
        DROP TABLE IF EXISTS dim_source;
        DROP TABLE IF EXISTS dim_channel;
        CREATE TABLE dim_channel (channel TEXT PRIMARY KEY);
        CREATE TABLE dim_source (
            source TEXT PRIMARY KEY, channel TEXT NOT NULL REFERENCES dim_channel(channel),
            source_rows INTEGER NOT NULL, observed_start_utc TEXT, observed_end_utc TEXT,
            source_sha256 TEXT, relative_path TEXT
        );
        CREATE TABLE dim_date (date_utc TEXT PRIMARY KEY, year INTEGER, month INTEGER, day INTEGER, weekday INTEGER);
        CREATE TABLE dim_status_snapshot (status_snapshot TEXT PRIMARY KEY);
        CREATE TABLE dim_account (
            account_key TEXT PRIMARY KEY, channel TEXT NOT NULL REFERENCES dim_channel(channel),
            first_observed_utc TEXT, last_observed_utc TEXT
        );
        CREATE TABLE fact_log (
            log_key TEXT PRIMARY KEY, source TEXT NOT NULL REFERENCES dim_source(source), source_row_number INTEGER NOT NULL,
            channel TEXT NOT NULL REFERENCES dim_channel(channel), date_utc TEXT REFERENCES dim_date(date_utc),
            account_key TEXT REFERENCES dim_account(account_key), reference_key TEXT, created_at TEXT,
            status_snapshot TEXT REFERENCES dim_status_snapshot(status_snapshot), amount REAL,
            window_24h_complete INTEGER, window_7d_complete INTEGER, core_features_eligible INTEGER NOT NULL,
            {numeric_sql}, UNIQUE(source, source_row_number)
        );
        CREATE TABLE fact_account_snapshot (
            channel TEXT NOT NULL REFERENCES dim_channel(channel), account_key TEXT NOT NULL REFERENCES dim_account(account_key),
            cutoff_utc TEXT NOT NULL, observed_log_count INTEGER, observed_reference_count INTEGER,
            amount_observation_count INTEGER, amount_mean REAL, amount_std REAL, unique_timestamp_count INTEGER,
            median_interval_seconds REAL, first_created_at TEXT, last_created_at TEXT, account_observation_days REAL,
            source_coverage_start TEXT, source_coverage_end TEXT, source_observation_days REAL,
            PRIMARY KEY(account_key, cutoff_utc)
        );
    """
    sources = logs.groupby(["source", "channel"], sort=False).agg(
        source_rows=("log_key", "size"), observed_start_utc=("created_at", "min"),
        observed_end_utc=("created_at", "max")).reset_index()
    manifests = {item["source"]: item for item in metadata["source_manifest"]}
    sources["source_sha256"] = sources.source.map({name: item.get("sha256") for name, item in manifests.items()})
    sources["relative_path"] = sources.source.map({name: item.get("path") for name, item in manifests.items()})
    dates = logs.created_at.dropna().dt.floor("D").drop_duplicates().sort_values()
    date_dimension = pd.DataFrame({"date_utc": dates.dt.strftime("%Y-%m-%d"), "year": dates.dt.year,
                                   "month": dates.dt.month, "day": dates.dt.day, "weekday": dates.dt.day_of_week})
    account_dimension = logs.loc[logs.account_key.notna()].groupby(["account_key", "channel"], sort=False).agg(
        first_observed_utc=("created_at", "min"), last_observed_utc=("created_at", "max")).reset_index()
    fact = logs.merge(features.drop(columns="channel"), on="log_key", validate="one_to_one")
    fact["date_utc"] = fact.created_at.dt.strftime("%Y-%m-%d")
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(schema)
        for table, frame in [
            ("dim_channel", logs[["channel"]].drop_duplicates()), ("dim_source", sources),
            ("dim_date", date_dimension), ("dim_status_snapshot", logs[["status_snapshot"]].dropna().drop_duplicates()),
            ("dim_account", account_dimension), ("fact_log", fact), ("fact_account_snapshot", accounts),
        ]:
            _sql_frame(frame).to_sql(table, connection, if_exists="append", index=False)
        if connection.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("SQLite foreign-key integrity check failed")
    return database
