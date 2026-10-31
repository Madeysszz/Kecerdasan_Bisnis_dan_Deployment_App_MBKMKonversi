import json
import sqlite3
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


class IntegrationTests(unittest.TestCase):
    @unittest.skipUnless(
        (ROOT / "data/processed/sanitized_logs.csv").exists()
        and (ROOT / "outputs/tables/anomaly_scores.csv").exists(),
        "CSV privat log dan skor belum tersedia; jalankan pipeline dengan CSV sumber privat.",
    )
    def test_exported_scores_cover_every_log_once(self):
        logs = pd.read_csv(ROOT / "data/processed/sanitized_logs.csv")
        scores = pd.read_csv(ROOT / "outputs/tables/anomaly_scores.csv")
        self.assertTrue(scores.log_key.is_unique)
        self.assertEqual(set(logs.log_key), set(scores.log_key))
        self.assertEqual(len(logs), 14261)
        for model in ["if", "ecod", "lof"]:
            self.assertTrue(np.isfinite(scores[f"{model}_score"]).all())
            self.assertTrue(scores[f"{model}_percentile"].between(0, 1).all())
        self.assertTrue(scores.reasons.notna().all())
        for evidence in scores.supporting_evidence:
            self.assertIsInstance(json.loads(evidence), dict)

    @unittest.skipUnless(
        (ROOT / "data/processed/norton_bi.db").exists(),
        "Database hasil pipeline belum tersedia; jalankan pipeline dengan CSV sumber privat.",
    )
    def test_dimensional_joins_preserve_source_controls(self):
        with sqlite3.connect(ROOT / "data/processed/norton_bi.db") as connection:
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
            rows = connection.execute("""
                SELECT c.channel, COUNT(*), SUM(f.amount)
                FROM fact_log f
                JOIN dim_channel c ON c.channel = f.channel
                JOIN dim_date d ON d.date_utc = f.date_utc
                GROUP BY c.channel
            """).fetchall()
            self.assertEqual(rows, [("cobrandgen", 14083, 210997000), ("retail", 178, 4293900)])
            score_count = connection.execute("SELECT COUNT(*) FROM fact_anomaly_scores").fetchone()[0]
            self.assertEqual(score_count, 14261 * 3)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM fact_account_snapshot").fetchone()[0], 9326)
            invalid_configs = connection.execute("SELECT COUNT(*) FROM dim_run WHERE NOT json_valid(parameters_json)").fetchone()[0]
            self.assertEqual(invalid_configs, 0)

    @unittest.skipUnless(
        (ROOT / "data/processed/feature_metadata.json").exists(),
        "Metadata fitur hasil pipeline belum tersedia; jalankan pipeline dengan CSV sumber privat.",
    )
    def test_core_features_and_models_exclude_restricted_columns(self):
        metadata = json.loads((ROOT / "data/processed/feature_metadata.json").read_text(encoding="utf-8"))
        forbidden = {"customer_id", "transaction_id", "status_snapshot", "pin", "psn", "redeem_code", "ip", "email"}
        self.assertFalse(forbidden.intersection(metadata["core_features"]))
        self.assertEqual(metadata["eligibility"]["excluded_core_logs"], 0)
        evaluation = json.loads((ROOT / "outputs/reports/model_evaluation.json").read_text(encoding="utf-8"))
        self.assertEqual(evaluation["analysis_mode"], "retrospective_in_sample")
        self.assertEqual(set(evaluation["channels"]), {"cobrandgen", "retail"})


if __name__ == "__main__":
    unittest.main()
