import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from src.features import CORE_FEATURES, build_features, save_artifacts


CONFIG = {"missing_tokens": ["", "NULL", "null", "\\N"], "timestamp_artifact": ".-1f",
          "timestamp_format": "%d/%m/%Y %H:%M:%S%z"}


def frame(rows):
    return pd.DataFrame(rows, columns=["customer_id", "transaction_id", "created_at", "price", "status_activated"], dtype="string")


def fixture():
    return frame([
        ["synthetic-account-alpha", "synthetic-reference-one", "1/1/2026 00:00:00.-1f+00", "10", "ACTIVE"],
        ["synthetic-account-alpha", "synthetic-reference-two", "1/1/2026 00:00:00.-1f+00", "30", "CANCEL"],
        ["synthetic-account-alpha", "synthetic-reference-one", "1/1/2026 01:00:00.-1f+00", "20", "ACTIVE"],
        ["synthetic-account-alpha", "synthetic-reference-one", "1/1/2026 01:00:00.-1f+00", "40", "CANCEL"],
        ["synthetic-account-alpha", "synthetic-reference-one", "2/1/2026 01:00:00.-1f+00", "50", "ACTIVE"],
    ])


def build(sources):
    with patch("src.features.load_sources", return_value=(CONFIG, sources, [])):
        return build_features("synthetic-config.json")


class FeatureTests(unittest.TestCase):
    def test_strict_history_and_equal_timestamp_shared_state(self):
        logs, features, _, metadata = build({"retail": fixture()})
        np.testing.assert_array_equal(logs.prior_history_count, [0, 0, 2, 2, 4])
        np.testing.assert_array_equal(logs.prior_account_count_24h, [0, 0, 2, 2, 2])
        np.testing.assert_array_equal(logs.prior_account_count_7d, [0, 0, 2, 2, 4])
        np.testing.assert_array_equal(logs.prior_reference_count, [0, 0, 1, 1, 3])
        self.assertTrue(logs.seconds_since_previous_log.iloc[:2].isna().all())
        np.testing.assert_array_equal(logs.seconds_since_previous_log.iloc[2:], [3600, 3600, 86400])
        self.assertTrue(logs.prior_channel_median_amount.iloc[:2].isna().all())
        np.testing.assert_array_equal(logs.prior_channel_median_amount.iloc[2:], [20, 20, 25])
        self.assertEqual(logs.window_24h_complete.tolist(), [False, False, False, False, True])
        self.assertFalse(logs.window_7d_complete.any())
        self.assertTrue(np.isfinite(features[CORE_FEATURES]).all().all())
        self.assertEqual(metadata["eligibility"]["finite_core_logs"], 5)

    def test_future_append_cannot_change_earlier_features(self):
        original = fixture()
        future = frame([["synthetic-account-alpha", "synthetic-reference-one", "3/1/2026 01:00:00+00", "1000000", "FAILED"]])
        logs, features, _, _ = build({"retail": original})
        extended_logs, extended_features, _, _ = build({"retail": pd.concat([original, future], ignore_index=True)})
        pd.testing.assert_frame_equal(features, extended_features.iloc[:len(features)].reset_index(drop=True))
        for column in ["prior_history_count", "seconds_since_previous_log", "prior_channel_median_amount"]:
            pd.testing.assert_series_equal(logs[column], extended_logs[column].iloc[:len(logs)].reset_index(drop=True))

    def test_time_of_day_preserves_observed_minutes_and_seconds(self):
        source = frame([
            ["synthetic-account-alpha", "synthetic-reference-one", "1/1/2026 01:00:00+00", "10", "ACTIVE"],
            ["synthetic-account-alpha", "synthetic-reference-one", "1/1/2026 01:30:15+00", "10", "ACTIVE"],
        ])
        _, features, _, metadata = build({"retail": source})
        expected_hours = np.array([1, 1 + 30 / 60 + 15 / 3600])
        np.testing.assert_allclose(features.hour_sin, np.sin(2 * np.pi * expected_hours / 24))
        np.testing.assert_allclose(features.hour_cos, np.cos(2 * np.pi * expected_hours / 24))
        self.assertNotEqual(features.loc[0, "hour_sin"], features.loc[1, "hour_sin"])
        self.assertNotEqual(features.loc[0, "hour_cos"], features.loc[1, "hour_cos"])
        self.assertEqual(metadata["feature_version"], "2_time_of_day_seconds")

    def test_first_occurrence_surrogates_and_channel_namespaces(self):
        source = fixture().iloc[[4, 0]].reset_index(drop=True)
        source.loc[0, "customer_id"] = "synthetic-account-beta"
        logs, _, _, _ = build({"retail": source, "cobrandgen": source})
        self.assertEqual(logs.account_key.tolist(), ["retail:account:000001", "retail:account:000002",
                                                   "cobrandgen:account:000001", "cobrandgen:account:000002"])
        self.assertEqual(logs.log_key.tolist(), ["retail:000001", "retail:000002", "cobrandgen:000001", "cobrandgen:000002"])
        self.assertEqual(logs.source_row_number.tolist(), [1, 2, 1, 2])

    def test_unknown_values_are_not_imputed(self):
        source = fixture().iloc[:3].copy()
        source.loc[0, "price"] = "NULL"
        source.loc[1, "customer_id"] = "NULL"
        source.loc[1, "transaction_id"] = "NULL"
        source.loc[2, "created_at"] = "invalid-time"
        logs, features, _, metadata = build({"retail": source})
        self.assertTrue(pd.isna(features.loc[0, "log1p_amount"]))
        self.assertTrue(pd.isna(features.loc[1, "log1p_prior_account_count_24h"]))
        self.assertTrue(pd.isna(features.loc[1, "log1p_prior_reference_count"]))
        self.assertTrue(pd.isna(features.loc[2, "hour_sin"]))
        self.assertTrue(logs.amount_minus_prior_channel_median.isna().all())
        self.assertEqual(metadata["eligibility"]["excluded_core_logs"], 3)

    def test_account_snapshot_uses_unique_timestamps_and_sample_std(self):
        singleton = frame([["synthetic-account-beta", "synthetic-reference-three", "2/1/2026 02:00:00+00", "70", "ACTIVE"]])
        _, _, accounts, metadata = build({"retail": pd.concat([fixture(), singleton], ignore_index=True)})
        active = accounts.iloc[0]
        self.assertEqual(active.observed_log_count, 5)
        self.assertEqual(active.unique_timestamp_count, 3)
        self.assertEqual(active.median_interval_seconds, 45000)
        self.assertAlmostEqual(active.amount_std, np.std([10, 30, 20, 40, 50], ddof=1))
        self.assertTrue(pd.isna(accounts.iloc[1].amount_std))
        self.assertTrue(pd.isna(accounts.iloc[1].median_interval_seconds))
        self.assertEqual(str(active.cutoff_utc), "2026-01-02 02:00:01+00:00")
        self.assertFalse(metadata["account_model_ready"])

    def test_sqlite_foreign_keys_grain_and_sanitized_exports(self):
        logs, features, accounts, metadata = build({"retail": fixture()})
        with tempfile.TemporaryDirectory() as directory:
            database = save_artifacts(logs, features, accounts, metadata, directory)
            self.assertEqual(database, Path(directory) / "data" / "processed" / "norton_bi.db")
            with closing(sqlite3.connect(database)) as connection:
                self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
                self.assertEqual(connection.execute("SELECT COUNT(*), COUNT(DISTINCT log_key) FROM fact_log").fetchone(), (5, 5))
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM fact_account_snapshot").fetchone()[0], 1)
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM fact_log WHERE seconds_since_previous_log IS NULL").fetchone()[0], 2)
                self.assertEqual(connection.execute("SELECT SUM(amount) FROM fact_log").fetchone()[0], 150)
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute("INSERT INTO fact_log SELECT * FROM fact_log LIMIT 1")
            for path in database.parent.glob("*.csv"):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("synthetic-account-alpha", text)
                self.assertNotIn("synthetic-reference-one", text)
            stored = json.loads((database.parent / "feature_metadata.json").read_text(encoding="utf-8"))
            self.assertEqual(stored["core_features"], CORE_FEATURES)

    def test_rebuild_invalidates_stale_scores_and_updates_source_provenance(self):
        logs, features, accounts, metadata = build({"retail": fixture()})
        metadata["source_manifest"] = [{"source": "retail", "path": "../synthetic-source.csv", "sha256": "a" * 64}]
        with tempfile.TemporaryDirectory() as directory:
            database = save_artifacts(logs, features, accounts, metadata, directory)
            with closing(sqlite3.connect(database)) as connection:
                connection.execute("PRAGMA foreign_keys = ON")
                connection.executescript("""
                    CREATE TABLE dim_model (model_key TEXT PRIMARY KEY);
                    CREATE TABLE dim_run (run_key TEXT PRIMARY KEY, model_key TEXT REFERENCES dim_model(model_key));
                    CREATE TABLE fact_anomaly_scores (
                        log_key TEXT REFERENCES fact_log(log_key), run_key TEXT REFERENCES dim_run(run_key),
                        model_key TEXT REFERENCES dim_model(model_key), score REAL
                    );
                    INSERT INTO dim_model VALUES ('synthetic-model');
                    INSERT INTO dim_run VALUES ('synthetic-run', 'synthetic-model');
                    INSERT INTO fact_anomaly_scores VALUES ('retail:000001', 'synthetic-run', 'synthetic-model', 0.5);
                """)
                self.assertEqual(connection.execute("SELECT source_sha256, relative_path FROM dim_source").fetchone(),
                                 ("a" * 64, "../synthetic-source.csv"))
            metadata["source_manifest"][0]["sha256"] = "b" * 64
            save_artifacts(logs, features, accounts, metadata, directory)
            with closing(sqlite3.connect(database)) as connection:
                self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM fact_log").fetchone()[0], 5)
                stale = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name IN (?, ?, ?)",
                                           ("fact_anomaly_scores", "dim_run", "dim_model")).fetchall()
                self.assertEqual(stale, [])
                self.assertEqual(connection.execute("SELECT source_sha256 FROM dim_source").fetchone()[0], "b" * 64)


if __name__ == "__main__":
    unittest.main()
