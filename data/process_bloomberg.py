#!/usr/bin/env python3
"""
Process raw Bloomberg terminal data into ml_ready.csv.

Place Bloomberg files (.csv/.xlsx) in data/unprocessed/. Each file or sheet
represents one quarter — include the quarter in the name (e.g. SP500_2024Q3.csv).

Usage:
    python data/process_bloomberg.py
    python data/process_bloomberg.py --normalize none
    python data/process_bloomberg.py --dry-run
"""

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

# ── Paths ────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
UNPROCESSED_DIR = ROOT / "data" / "unprocessed"
OUTPUT_PATH = ROOT / "data" / "processed" / "ml_ready.csv"

# ── Column Mapping ───────────────────────────────────────────────────────────
# Bloomberg field (left) → our name (right). Unmapped columns are dropped.

COLUMN_MAP = {
    "TICKER":                       "ticker",
    "GICS_SECTOR_NAME":             "sector",
    "GICS_INDUSTRY_NAME":           "industry",
    "EARN_YLD":                     "earnings_yield",
    "PX_TO_BOOK_RATIO":             "pb_ratio",
    "FCF_YIELD":                    "fcf_yield",
    "EV_TO_T12M_EBITDA":            "ev_to_ebitda",
    "RETURN_ON_CAP":                "return_on_capital",
    "PROF_MARGIN":                  "profit_margin",
    "GROSS_PROFIT":                 "gross_profit",
    "RETURN_COM_EQY":               "roe",
    "BS_TOT_ASSET":                 "total_assets",
    "TOT_DEBT_TO_TOT_EQY":          "debt_to_equity",
    "SALES_GROWTH":                 "revenue_growth",
    "CHG_PCT_1M":                   "return_1m",
    "CHG_PCT_3M":                   "return_3m",
    "CHG_PCT_6M":                   "return_6m",
    "CHG_PCT_1YR":                  "return_1y",
    "BETA_RAW_OVERRIDABLE":         "beta",
    "VOLATILITY_60D":               "volatility_60d",
    "SHORT_INT_RATIO":              "short_interest_ratio",
    "PX_VOLUME":                    "volume",
    "EQY_SH_OUT":                   "shares_outstanding",
    "HISTORICAL_MARKET_CAP":        "market_cap",
    "TOT_RETURN_INDEX_GROSS_DVDS":  "total_return_index",
    "FORWARD_RETURN":               "forward_return",
}

# ── Features & Output Schema ────────────────────────────────────────────────

MF_FEATURES = ["earnings_yield", "return_on_capital"]

ALL_FEATURES = [
    "earnings_yield", "pb_ratio", "fcf_yield", "ev_to_ebitda",
    "return_on_capital", "profit_margin", "gross_profit", "roe",
    "total_assets", "debt_to_equity", "revenue_growth",
    "return_1m", "return_3m", "return_6m", "return_1y",
    "beta", "volatility_60d",
    "short_interest_ratio", "volume", "shares_outstanding", "market_cap",
    "total_return_index",
]

IDENTIFIER_COLS = ["ticker", "quarter", "sector", "industry", "quarter_date"]
TARGET_COLS = ["forward_return", "forward_return_rank"]
OUTPUT_COLS = IDENTIFIER_COLS + ALL_FEATURES + TARGET_COLS

# ── Quarter Extraction ───────────────────────────────────────────────────────

_QUARTER_RE = re.compile(r"(\d{4})[_\-]?Q([1-4])|Q([1-4])[_\-]?(\d{4})", re.I)
_QUARTER_END = {"1": "03-31", "2": "06-30", "3": "09-30", "4": "12-31"}


def _parse_quarter(name: str) -> tuple[str, str] | None:
    """'SP500_2024Q3' → ('2024-Q3', '2024-09-30'), or None."""
    m = _QUARTER_RE.search(name)
    if not m:
        return None
    year, q = (m.group(1), m.group(2)) if m.group(1) else (m.group(4), m.group(3))
    return f"{year}-Q{q}", f"{year}-{_QUARTER_END[q]}"


# ── Pipeline ─────────────────────────────────────────────────────────────────

def load(input_dir: Path) -> pd.DataFrame:
    """Read all CSVs/Excel files from input_dir. Quarter from filename/sheet."""
    input_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(
        p for p in input_dir.iterdir()
        if p.suffix.lower() in {".csv", ".xlsx", ".xls"}
    )
    if not files:
        sys.exit(f"No data files found in {input_dir}")

    frames = []
    for f in files:
        sheets = {"": pd.read_csv(f)} if f.suffix == ".csv" else {
            s: pd.read_excel(f, sheet_name=s) for s in pd.ExcelFile(f).sheet_names
        }
        for sheet_name, df in sheets.items():
            if df.empty:
                continue
            label = f"{f.stem}_{sheet_name}" if sheet_name else f.stem
            qinfo = _parse_quarter(sheet_name) or _parse_quarter(f.stem)
            if qinfo:
                df["quarter"], df["quarter_date"] = qinfo
            frames.append(df)
            print(f"  {label}: {len(df):,} rows  quarter={qinfo[0] if qinfo else '???'}")

    if not frames:
        sys.exit("All files were empty")

    combined = pd.concat(frames, ignore_index=True)
    if "quarter" not in combined.columns:
        sys.exit("Could not extract quarter from any filename — use e.g. SP500_2024Q3.csv")

    print(f"Loaded {len(combined):,} total rows from {len(files)} file(s)\n")
    return combined


def rename(df: pd.DataFrame) -> pd.DataFrame:
    """Rename Bloomberg columns, drop the rest."""
    lower_to_orig = {c.lower(): c for c in df.columns}
    mapping = {}
    for bbg, ours in COLUMN_MAP.items():
        orig = lower_to_orig.get(bbg.lower())
        if orig:
            mapping[orig] = ours

    unmapped = set(COLUMN_MAP) - {k for k in COLUMN_MAP if k.lower() in lower_to_orig}
    if unmapped:
        print(f"  Warning — not found in data: {sorted(unmapped)}")

    df = df.rename(columns=mapping)
    keep = set(COLUMN_MAP.values()) | {"quarter", "quarter_date"}
    return df[[c for c in df.columns if c in keep]]


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce types, drop unusable rows, deduplicate."""
    for col in ALL_FEATURES + TARGET_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "ticker" in df.columns:
        df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()

    n = len(df)
    df = df.dropna(subset=["ticker", "forward_return"])
    df = df.drop_duplicates(subset=["ticker", "quarter"], keep="last")
    print(f"Cleaned: {n:,} → {len(df):,} rows\n")
    return df


def normalize(df: pd.DataFrame, method: str) -> pd.DataFrame:
    """Percentile-rank features within each quarter (0 to 1)."""
    if method == "none":
        return df
    cols = [c for c in ALL_FEATURES if c in df.columns]
    df[cols] = df.groupby("quarter")[cols].rank(pct=True, method="average")
    print(f"Normalized {len(cols)} features via percentile rank\n")
    return df


def add_forward_rank(df: pd.DataFrame) -> pd.DataFrame:
    """forward_return_rank = percentile of forward_return per quarter (0-100)."""
    if "forward_return_rank" in df.columns and df["forward_return_rank"].notna().all():
        return df
    df["forward_return_rank"] = (
        df.groupby("quarter")["forward_return"].rank(pct=True, method="average") * 100
    )
    return df


def validate(df: pd.DataFrame) -> None:
    """Quick sanity checks."""
    missing = [c for c in OUTPUT_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    print(
        f"Output: {len(df):,} rows | "
        f"{df['ticker'].nunique()} tickers | "
        f"{df['quarter'].nunique()} quarters "
        f"({df['quarter'].min()} → {df['quarter'].max()})"
    )


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Bloomberg → ml_ready.csv")
    p.add_argument("--input-dir", type=Path, default=UNPROCESSED_DIR)
    p.add_argument("--output", type=Path, default=OUTPUT_PATH)
    p.add_argument("--normalize", choices=["rank", "none"], default="rank")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    df = load(args.input_dir)
    df = rename(df)
    df = clean(df)
    df = normalize(df, args.normalize)
    df = add_forward_rank(df)
    df = df[OUTPUT_COLS]
    validate(df)

    if args.dry_run:
        print(f"\n[DRY RUN] Would write to {args.output}")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(args.output, index=False)
        print(f"\nWrote {len(df):,} rows → {args.output}")


if __name__ == "__main__":
    main()
