import argparse
import hashlib
import json
from pathlib import Path

from src.audit import run_audit
from src.features import build_features, save_artifacts
from src.modeling import run_models
from src.reporting import store_model_scores, write_results


def run_pipeline(root):
    audit_config = root / "configs/audit.json"
    print("Fase 1: audit dan EDA", flush=True)
    audit = run_audit(audit_config)
    print("Fase 2: fitur historis dan data mart terpisah", flush=True)
    logs, features, accounts, metadata = build_features(audit_config)
    mart = save_artifacts(logs, features, accounts, metadata, root)
    config = json.loads((root / "configs/experiments.json").read_text(encoding="utf-8"))
    print("Fase 3–5: model, evaluasi, dan alasan statistik", flush=True)
    scores, evaluation = run_models(logs, features, metadata["core_features"], config, root / "outputs")
    scores.to_csv(root / "outputs/tables/anomaly_scores.csv", index=False)
    store_model_scores(root, scores, config)
    write_results(root, logs, scores, evaluation, metadata)
    for source in metadata["source_manifest"]:
        if hashlib.sha256((root / source["path"]).read_bytes()).hexdigest() != source["sha256"]:
            raise RuntimeError("Sumber berubah selama pipeline; hasil harus ditinjau ulang.")
    result = {"analysis_mode": "retrospective_in_sample", "log_rows": len(logs),
              "scored_rows": len(scores), "account_snapshots": len(accounts),
              "input_files_unchanged": audit["raw_inputs_unchanged"],
              "data_mart": str(Path(mart).relative_to(root)),
              "feature_columns": metadata["core_features"], "feature_version": metadata["feature_version"]}
    (root / "outputs/reports/pipeline_validation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline BI retrospektif Norton.")
    parser.parse_args()
    run_pipeline(Path(__file__).resolve().parent)
