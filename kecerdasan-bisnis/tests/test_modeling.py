import copy
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src.modeling import run_models


FEATURE_COLUMNS = [
    "log1p_amount",
    "log1p_prior_account_count_24h",
    "log1p_prior_account_count_7d",
    "log1p_prior_reference_count",
    "hour_sin",
    "hour_cos",
    "weekday_sin",
    "weekday_cos",
]


def synthetic_data():
    rng = np.random.default_rng(2026)
    logs = []
    features = []
    for channel, count in [("retail", 70), ("cobrandgen", 35)]:
        values = np.column_stack([
            np.log1p(rng.lognormal(8, 0.4, count)),
            np.log1p(rng.integers(0, 6, count)),
            np.log1p(rng.integers(0, 25, count)),
            np.log1p(rng.integers(0, 3, count)),
            np.sin(np.arange(count) * np.pi / 12),
            np.cos(np.arange(count) * np.pi / 12),
            np.sin(np.arange(count) * 2 * np.pi / 7),
            np.cos(np.arange(count) * 2 * np.pi / 7),
        ])
        values[-2:] = values[-3]
        for index, row in enumerate(values):
            key = f"{channel}-{index:03d}"
            logs.append({
                "log_key": key,
                "channel": channel,
                "created_at": pd.Timestamp("2026-01-01", tz="UTC") + pd.Timedelta(hours=index),
                "status_snapshot": "active",
                "amount": float(np.expm1(row[0])),
                "unknown_private": "private-value-must-not-be-exported",
            })
            features.append({"log_key": key, "channel": channel, **dict(zip(FEATURE_COLUMNS, row))})
    return pd.DataFrame(logs), pd.DataFrame(features).sample(frac=1, random_state=11).reset_index(drop=True)


class ModelingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.logs, cls.features = synthetic_data()
        cls.config = {
            "isolation_forest": {"n_estimators": [12, 20], "max_samples": [20], "seeds": [11, 42]},
            "lof": {"n_neighbors": [5, 10]},
            "evaluation": {"top_k": [5, 10], "threshold_percentages": [1, 5], "sample_fraction": 0},
        }
        cls.directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.directory.cleanup)
        cls.output = Path(cls.directory.name)
        cls.original_logs = cls.logs.copy(deep=True)
        cls.original_features = cls.features.copy(deep=True)
        cls.scores, cls.evaluation = run_models(
            cls.logs, cls.features, FEATURE_COLUMNS, copy.deepcopy(cls.config), cls.output
        )

    def test_rows_remain_aligned_and_private_columns_are_excluded(self):
        self.assertEqual(len(self.scores), len(self.logs))
        self.assertTrue(self.scores.log_key.is_unique)
        expected_channels = self.logs.set_index("log_key").channel.sort_index()
        actual_channels = self.scores.set_index("log_key").channel.sort_index()
        pd.testing.assert_series_equal(actual_channels, expected_channels)
        for column in ["unknown_private", "created_at", "status_snapshot", "amount"]:
            self.assertNotIn(column, self.scores.columns)
        self.assertNotIn("private-value-must-not-be-exported", self.scores.to_json())
        for path in self.output.rglob("*"):
            if path.suffix in [".csv", ".json", ".md"]:
                self.assertNotIn("private-value-must-not-be-exported", path.read_text(encoding="utf-8"))
        pd.testing.assert_frame_equal(self.logs, self.original_logs)
        pd.testing.assert_frame_equal(self.features, self.original_features)

    def test_score_direction_and_tied_average_ranks(self):
        for channel, rows in self.scores.groupby("channel"):
            for model in ["if", "ecod", "lof"]:
                with self.subTest(channel=channel, model=model):
                    raw = rows[f"{model}_score"]
                    self.assertTrue(np.isfinite(raw).all())
                    np.testing.assert_allclose(rows[f"{model}_percentile"], raw.rank(method="average", pct=True))
                    np.testing.assert_allclose(rows[f"{model}_rank"], raw.rank(method="average", ascending=False))
                    tied = rows.loc[rows.log_key.isin([f"{channel}-{len(rows) - offset:03d}" for offset in [1, 2, 3]])]
                    self.assertEqual(tied[f"{model}_score"].nunique(), 1)
                    self.assertEqual(tied[f"{model}_rank"].nunique(), 1)

    def test_investigation_priorities_and_consensus_order(self):
        for channel, rows in self.scores.groupby("channel"):
            with self.subTest(channel=channel):
                counts = rows.investigation_priority.value_counts()
                high = int(np.ceil(len(rows) * 0.01))
                reviewed = int(np.ceil(len(rows) * 0.05))
                self.assertEqual(counts.get("tinggi", 0), high)
                self.assertEqual(counts.get("sedang", 0), reviewed - high)
                self.assertEqual(counts.get("rendah", 0), len(rows) - reviewed)
                ordered = rows.sort_values(["consensus_score", "log_key"], ascending=[False, True])
                self.assertEqual(ordered.anomaly_rank.tolist(), list(range(1, len(rows) + 1)))

    def test_metadata_and_saved_models_cover_each_channel(self):
        self.assertEqual(self.evaluation["analysis_mode"], "retrospective_in_sample")
        self.assertEqual(set(self.evaluation["channels"]), {"retail", "cobrandgen"})
        for channel, metadata in self.evaluation["channels"].items():
            with self.subTest(channel=channel):
                self.assertEqual(set(metadata["active_features"]), set(FEATURE_COLUMNS))
                self.assertEqual(metadata["constant_features"], [])
                self.assertEqual({entry["model"] for entry in metadata["baseline_parameters"]}, {"if", "ecod", "lof"})
                for name in ["isolation_forest", "ecod", "lof", "preprocessing"]:
                    artifact = self.output / "models" / channel / f"{name}.joblib"
                    self.assertTrue(artifact.is_file(), str(artifact))
                    self.assertGreater(artifact.stat().st_size, 0)

    def test_repeated_runs_are_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            repeated, _ = run_models(
                self.logs.sample(frac=1, random_state=73), self.features.iloc[::-1].copy(),
                FEATURE_COLUMNS, copy.deepcopy(self.config), Path(directory)
            )
        pd.testing.assert_frame_equal(
            self.scores.sort_values("log_key").reset_index(drop=True),
            repeated.sort_values("log_key").reset_index(drop=True),
        )

    def test_nonfinite_features_are_rejected(self):
        for value in [np.nan, np.inf, -np.inf]:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                features = self.features.copy()
                features.loc[0, FEATURE_COLUMNS[0]] = value
                with self.assertRaises(ValueError):
                    run_models(self.logs, features, FEATURE_COLUMNS, self.config, Path(directory))

    def test_duplicate_keys_and_missing_feature_rows_are_rejected(self):
        invalid_inputs = [
            (pd.concat([self.logs, self.logs.iloc[[0]]], ignore_index=True), self.features),
            (self.logs, pd.concat([self.features, self.features.iloc[[0]]], ignore_index=True)),
            (self.logs, self.features.iloc[1:].copy()),
        ]
        for index, (logs, features) in enumerate(invalid_inputs):
            with self.subTest(case=index), tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(ValueError):
                    run_models(logs, features, FEATURE_COLUMNS, self.config, Path(directory))

    def test_constant_and_insufficient_channels_are_rejected(self):
        logs = self.logs.loc[self.logs.channel.eq("retail")].copy()
        features = self.features.loc[self.features.channel.eq("retail")].copy()
        constant = features.copy()
        constant[FEATURE_COLUMNS] = 0.0
        too_few_logs = logs.iloc[:2].copy()
        too_few_features = features.loc[features.log_key.isin(too_few_logs.log_key)].copy()
        for case, (case_logs, case_features) in enumerate([(logs, constant), (too_few_logs, too_few_features)]):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(ValueError):
                    run_models(case_logs, case_features, FEATURE_COLUMNS, self.config, Path(directory))

    def test_duplicate_vectors_adjust_lof_neighbors_without_changing_rows(self):
        logs = self.logs.loc[self.logs.channel.eq("cobrandgen")].copy()
        features = self.features.loc[self.features.channel.eq("cobrandgen")].sort_values("log_key").copy()
        duplicate_keys = features.log_key.iloc[:20]
        vector = features[FEATURE_COLUMNS].iloc[0].to_numpy()
        features.loc[features.log_key.isin(duplicate_keys), FEATURE_COLUMNS] = vector
        logs.loc[logs.log_key.isin(duplicate_keys), "amount"] = float(np.expm1(vector[0]))
        original = features.copy(deep=True)
        with tempfile.TemporaryDirectory() as directory:
            scores, evaluation = run_models(logs, features, FEATURE_COLUMNS, self.config, Path(directory))
            diagnostics = evaluation["channels"]["cobrandgen"]
            self.assertEqual(diagnostics["duplicate_vector_diagnostics"]["max_identical_vectors"], 20)
            self.assertEqual(len(scores), len(logs))
            self.assertEqual(set(scores.log_key), set(logs.log_key))
            for variant in diagnostics["lof_suitability"]["variants"]:
                self.assertLess(variant["requested_n_neighbors"], 20)
                self.assertEqual(variant["effective_n_neighbors"], 21)
                self.assertEqual(variant["adjustment_reason"], "identical_vector_guard")
                self.assertEqual(variant["warnings"], [])
            stability = pd.read_csv(Path(directory) / "tables" / "model_stability.csv")
            self.assertFalse(stability.model.eq("lof").any())
        pd.testing.assert_frame_equal(features, original)


if __name__ == "__main__":
    unittest.main()
