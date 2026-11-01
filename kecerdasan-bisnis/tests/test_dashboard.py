import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT.parent / "DEPLOYMENT_KECERDASAN BISNIS/app.py"


@unittest.skipUnless(
    (ROOT / "data/processed/sanitized_logs.csv").exists()
    and (ROOT / "outputs/tables/anomaly_scores.csv").exists(),
    "Artefak privat dashboard belum tersedia; jalankan pipeline dengan CSV sumber privat.",
)
class DashboardTests(unittest.TestCase):
    def test_four_pages_render_with_actual_outputs(self):
        app = AppTest.from_file(str(APP), default_timeout=30).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[0].value, "14,261")
        for page in ["Anomaly Monitoring", "Model Comparison", "Transaction Investigation"]:
            app.sidebar.radio[0].set_value(page).run()
            self.assertEqual(len(app.exception), 0, page)
            self.assertGreater(len(app.dataframe), 0)

    def test_channel_and_status_filters_reconcile_source_counts(self):
        app = AppTest.from_file(str(APP), default_timeout=30).run()
        app.sidebar.multiselect[0].set_value(["retail"]).run()
        self.assertEqual(app.metric[0].value, "178")
        app.sidebar.multiselect[1].set_value(["ACTIVE"]).run()
        self.assertEqual(app.metric[0].value, "16")
        self.assertEqual(len(app.exception), 0)

    def test_empty_filter_and_model_changes_do_not_crash(self):
        app = AppTest.from_file(str(APP), default_timeout=30).run()
        app.sidebar.radio[0].set_value("Anomaly Monitoring").run()
        for model in ["Isolation Forest", "ECOD", "LOF"]:
            app.sidebar.selectbox[0].set_value(model).run()
            self.assertEqual(len(app.exception), 0)
        app.sidebar.multiselect[0].set_value([]).run()
        self.assertEqual(len(app.exception), 0)
        self.assertIn("Tidak ada log", app.info[0].value)


if __name__ == "__main__":
    unittest.main()
