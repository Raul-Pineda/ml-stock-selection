#!/usr/bin/env python3
"""Run all models through walk-forward validation and save results.

Usage: python -m src.evaluation.model_comparison
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
from backend.pipeline import METRIC_LABELS, build_excel, run_pipeline

DATA_PATH = ROOT / "src" / "data" / "processed" / "ml_ready_simfin.csv"
RESULTS_DIR = ROOT / "src" / "results"


def main():
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df):,} rows | {df['quarter'].nunique()} quarters\n")

    def on_progress(model, fs, fold, total, auc):
        if fold % 10 == 0 or fold == total:
            print(f"  {model} ({fs}): {fold}/{total} folds | AUC={auc:.4f}")

    comp_df, pq_df, fi_dict = run_pipeline(df, on_progress=on_progress)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Excel with embedded charts
    xlsx_path = RESULTS_DIR / "model_comparison.xlsx"
    xlsx_path.write_bytes(build_excel(comp_df, pq_df, fi_dict).read())

    # CSV summary
    csv_path = RESULTS_DIR / "model_comparison.csv"
    comp_df.to_csv(csv_path, index=False)

    print(f"\n{'='*60}\nRESULTS\n{'='*60}")
    print(comp_df.rename(columns=METRIC_LABELS).to_string(index=False))
    print(f"\nSaved: {xlsx_path}")
    print(f"Saved: {csv_path}")


if __name__ == "__main__":
    main()
