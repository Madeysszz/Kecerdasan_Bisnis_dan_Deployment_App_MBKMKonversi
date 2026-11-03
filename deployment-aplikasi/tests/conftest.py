import json
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest


APP = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture
def dashboard_root(tmp_path, monkeypatch):
    monkeypatch.setenv("NORTON_DATA_ROOT", str(tmp_path))
    logs_dir = tmp_path / "data/processed"
    tables_dir = tmp_path / "outputs/tables"
    reports_dir = tmp_path / "outputs/reports"
    for folder in [logs_dir, tables_dir, reports_dir]:
        folder.mkdir(parents=True)
    logs = pd.DataFrame({
        "log_key": [f"synthetic-{i}" for i in range(8)],
        "channel": ["cobrandgen"] * 4 + ["retail"] * 4,
        "account_key": ["synthetic-c-a", "synthetic-c-a", "synthetic-c-b", "synthetic-c-c",
                        "synthetic-r-a", "synthetic-r-a", "synthetic-r-b", "synthetic-r-c"],
        "created_at": [f"2030-01-{day:02d}T08:00:00+00:00" for day in [1, 2, 3, 4, 1, 2, 3, 4]],
        "status_snapshot": ["ACTIVE", "CANCEL", "ACTIVE", "PENDING", "ACTIVE", "CANCEL", "ACTIVE", "CANCEL"],
        "amount": [100, 200, 300, 400, 50, 60, 70, 80],
        "prior_history_count": [0, 1, 0, 0, 0, 1, 0, 0],
        "seconds_since_previous_log": [None, 86400, None, None, None, 86400, None, None],
        "prior_channel_median_amount": [None, 100, 150, 200, None, 50, 55, 60],
    })
    scores = pd.DataFrame({
        "log_key": logs.log_key,
        "channel": logs.channel,
        "if_percentile": [.1, .2, .6, .995, .3, .7, .9, 1.0],
        "ecod_percentile": [.2, .3, .999, .9, .4, .6, .8, .8],
        "lof_percentile": [.995, .999, .8, .991, .5, .7, .9, 1.0],
        "reasons": ["Skenario sintetis untuk pengujian UI."] * 8,
        "supporting_evidence": [json.dumps({"synthetic": True})] * 8,
    })
    scores["consensus_score"] = scores[["if_percentile", "ecod_percentile", "lof_percentile"]].mean(axis=1)
    scores["anomaly_rank"] = scores.groupby("channel").consensus_score.rank(method="first", ascending=False).astype(int)
    scores["investigation_priority"] = scores.anomaly_rank.map(lambda rank: "tinggi" if rank == 1 else "rendah")
    logs.to_csv(logs_dir / "sanitized_logs.csv", index=False)
    scores.to_csv(tables_dir / "anomaly_scores.csv", index=False)
    for name in ["model_agreement", "model_stability", "threshold_sensitivity", "experiment_parameters"]:
        pd.DataFrame({"channel": ["cobrandgen", "retail"], "fixture_type": ["synthetic", "synthetic"]}).to_csv(
            tables_dir / f"{name}.csv", index=False,
        )
    (reports_dir / "model_evaluation.json").write_text(
        json.dumps({"recommendation": "Rekomendasi sintetis untuk pengujian UI."}), encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def dashboard(dashboard_root):
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    return app
