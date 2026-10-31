import json
import unittest
from pathlib import Path

import pandas as pd

from src.audit import load_sources, missing_mask, parse_timestamp


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/audit.json"
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = CONFIG

    def test_day_first_artifact_and_invalid_values(self):
        values = pd.Series(["7/8/2026 06:00:00.-1f+00", "11/5/2026 00:00:00+00",
                            "31/2/2026 00:00:00+00", "", "unparseable"], dtype="string")
        original = values.copy()
        parsed = parse_timestamp(values, self.config)
        self.assertEqual(parsed.iloc[0], pd.Timestamp("2026-08-07T06:00:00Z"))
        self.assertEqual(parsed.iloc[1], pd.Timestamp("2026-05-11T00:00:00Z"))
        self.assertEqual(parsed.isna().tolist(), [False, False, True, True, True])
        pd.testing.assert_series_equal(values, original)

    def test_missing_values_preserve_zero(self):
        values = pd.Series(["", " NULL ", "null", "\\N", "0", "1000"], dtype="string")
        self.assertEqual(missing_mask(values, self.config).tolist(), [True, True, True, True, False, False])


@unittest.skipUnless(
    all((ROOT / path).exists() for path in CONFIG["sources"].values()),
    "CSV sumber privat belum tersedia; sediakan berkas sesuai configs/audit.json.",
)
class SourceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config, cls.frames, cls.manifest = load_sources(CONFIG_PATH)

    def test_aggregate_outputs_against_independent_source_counts(self):
        tables = ROOT / "outputs/tables"
        statuses = pd.read_csv(tables / "status_counts.csv")
        prices = pd.read_csv(tables / "price_summary.csv")
        daily = pd.read_csv(tables / "daily_counts.csv")
        for channel in ["retail", "cobrandgen"]:
            raw = self.frames[channel]
            for status, count in raw.status_activated.value_counts().items():
                actual = statuses.loc[statuses.channel.eq(channel) & statuses.status.eq(status), "log_count"].item()
                self.assertEqual(actual, count)
            expected = sum(int(value) for value in raw.price)
            self.assertEqual(prices.loc[prices.channel.eq(channel), "recorded_value_sum"].item(), expected)
            self.assertEqual(daily.loc[daily.channel.eq(channel), "log_count"].sum(), len(raw))

    def test_identifiers_and_credentials_absent_from_outputs(self):
        output_text = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "outputs").rglob("*") if path.suffix in [".csv", ".md", ".json"])
        for channel in ["retail", "cobrandgen"]:
            raw = self.frames[channel]
            for column in ["customer_id", "transaction_id", "redeem_code", "psn"]:
                values = raw[column][~missing_mask(raw[column], self.config)].unique()
                for value in values:
                    if len(value) >= 16:
                        self.assertFalse(value in output_text, f"Nilai terbatas terdeteksi pada kolom {column}.")

    def test_snapshot_checks(self):
        validation = json.loads((ROOT / "outputs/reports/audit_validation.json").read_text(encoding="utf-8"))
        self.assertTrue(validation["raw_inputs_unchanged"])
        self.assertEqual(validation["timestamp_parse_failures_nonmissing"], 0)
        self.assertEqual(validation["total_log_rows"], 14261)
        self.assertEqual([entry["rows"] for entry in self.manifest], [178, 14083, 90])


if __name__ == "__main__":
    unittest.main()
