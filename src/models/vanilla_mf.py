"""
Magic Formula baseline — a fixed stock-picking rule (no ML).

Scores each stock by: earnings_yield + return_on_capital.
Higher score = cheap AND efficient company = better pick.
This is the baseline we compare ML models against.
"""

import pandas as pd


def rank_magic_formula(df, ey_col="earnings_yield", roc_col="return_on_capital",
                       quarter_col="quarter"):
    """Score and rank stocks within each quarter. Rank 1 = best."""
    df = df.copy()
    df["mf_score"] = df[ey_col].fillna(0) + df[roc_col].fillna(0)
    df["mf_rank"] = (df.groupby(quarter_col)["mf_score"]
                     .rank(ascending=False, method="first").astype(int))
    return df


def mf_model_fn(train_df, test_df):
    """Score the test set using the Magic Formula (ignores training data)."""
    result = rank_magic_formula(test_df)
    result["predicted_score"] = result["mf_score"]
    result["predicted_rank"] = result["mf_rank"]
    median = result["predicted_score"].median()
    result["predicted_label"] = (result["predicted_score"] >= median).astype(int)
    return result



