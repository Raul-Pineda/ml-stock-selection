"""Shared constants and helpers used by all model files."""

MF_FEATURES = ["earnings_yield", "return_on_capital"]

ALL_FEATURES = [
    "earnings_yield", "return_on_capital", "market_cap", "pe_ratio",
    "pb_ratio", "debt_to_equity", "current_ratio",
    "net_margin", "revenue_growth", "fcf_yield", "enterprise_value",
    "return_3m", "return_6m", "volatility_60d",
]


def _prepare_data(train_df, test_df, feature_cols, label_col="label"):
    """Extract feature arrays and labels. Missing values become 0."""
    X_train = train_df[feature_cols].fillna(0).values
    y_train = train_df[label_col].values
    X_test = test_df[feature_cols].fillna(0).values
    return X_train, y_train, X_test


def _add_predictions(test_df, y_prob, threshold=0.5):
    """Attach predicted score, label, and rank to test set."""
    result = test_df.copy()
    result["predicted_score"] = y_prob
    result["predicted_label"] = (y_prob >= threshold).astype(int)
    group = result.groupby("quarter")["predicted_score"] if "quarter" in result.columns else result["predicted_score"]
    result["predicted_rank"] = (group.rank(ascending=False, method="first").astype(int)
                                if "quarter" in result.columns
                                else result["predicted_score"].rank(ascending=False, method="first").astype(int))
    return result
