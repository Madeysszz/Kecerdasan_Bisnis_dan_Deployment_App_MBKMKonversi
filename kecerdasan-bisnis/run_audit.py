import argparse
from pathlib import Path

from src.audit import run_audit


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit agregat dataset Norton.")
    parser.add_argument("--config", type=Path, default=Path(__file__).parent / "configs/audit.json")
    args = parser.parse_args()
    result = run_audit(args.config)
    print(f"Audit selesai: {result['total_log_rows']:,} baris log; keluaran: {result['output_dir']}")
