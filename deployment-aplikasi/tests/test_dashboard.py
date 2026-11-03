from datetime import date

import pytest
from streamlit.testing.v1 import AppTest

from conftest import APP


@pytest.mark.parametrize("page", [
    "Executive Overview", "Anomaly Monitoring", "Model Comparison", "Transaction Investigation",
])
def test_four_pages_render_with_synthetic_outputs(dashboard, page):
    dashboard.sidebar.radio[0].set_value(page).run()
    assert not dashboard.exception
    assert dashboard.header[0].value == page
    if page == "Executive Overview":
        assert [item.value for item in dashboard.metric] == ["8", "1,260", "6"]
    else:
        assert len(dashboard.dataframe) > 0


def test_channel_and_status_filters_reconcile_synthetic_counts(dashboard):
    dashboard.sidebar.multiselect[0].set_value(["retail"]).run()
    assert not dashboard.exception
    assert dashboard.metric[0].value == "4"
    assert dashboard.metric[1].value == "260"
    dashboard.sidebar.multiselect[1].set_value(["ACTIVE"]).run()
    assert not dashboard.exception
    assert dashboard.metric[0].value == "2"
    assert dashboard.metric[1].value == "120"


@pytest.mark.parametrize("model,score_column,flagged", [
    ("Isolation Forest", "if_percentile", 2),
    ("ECOD", "ecod_percentile", 1),
    ("LOF", "lof_percentile", 4),
])
def test_model_choice_changes_flagged_results(dashboard, model, score_column, flagged):
    dashboard.sidebar.radio[0].set_value("Anomaly Monitoring").run()
    dashboard.sidebar.selectbox[0].set_value(model).run()
    assert not dashboard.exception
    assert dashboard.metric[0].value == str(flagged)
    cases = dashboard.dataframe[1].value
    assert score_column in cases.columns
    assert len(cases) == flagged
    assert cases[score_column].ge(.99).all()


def test_empty_channel_filter_shows_message(dashboard):
    dashboard.sidebar.multiselect[0].set_value([]).run()
    assert not dashboard.exception
    assert dashboard.info[0].value == "Tidak ada log pada kombinasi filter ini."
    assert len(dashboard.metric) == 0


def test_date_filter_selects_inclusive_utc_range(dashboard):
    dashboard.sidebar.date_input[0].set_value((date(2030, 1, 2), date(2030, 1, 3))).run()
    assert not dashboard.exception
    assert dashboard.metric[0].value == "4"
    assert dashboard.metric[1].value == "630"


def test_investigation_keeps_full_account_context_outside_date_filter(dashboard):
    dashboard.sidebar.date_input[0].set_value((date(2030, 1, 2), date(2030, 1, 2))).run()
    dashboard.sidebar.radio[0].set_value("Transaction Investigation").run()
    assert not dashboard.exception
    selection = next(item for item in dashboard.selectbox if item.label == "Pilih log untuk melihat bukti")
    selection.set_value("synthetic-1").run()
    assert not dashboard.exception
    ranked = dashboard.dataframe[0].value
    context = dashboard.dataframe[1].value
    assert set(ranked.log_key) == {"synthetic-1", "synthetic-5"}
    assert set(context.log_key) == {"synthetic-0", "synthetic-1"}


def test_missing_artifacts_show_guidance_without_error(tmp_path, monkeypatch):
    monkeypatch.setenv("NORTON_DATA_ROOT", str(tmp_path))
    dashboard = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not dashboard.exception
    assert dashboard.info[0].value == "Data dashboard belum tersedia. Siapkan artefak analitik sesuai panduan deployment."
    assert len(dashboard.metric) == 0
