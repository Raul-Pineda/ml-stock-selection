"""Shared constants and helpers used by all model files."""

MF_FEATURES = ["earnings_yield", "return_on_capital"]

ALL_FEATURES = [
    "earnings_yield", "return_on_capital", "market_cap",
    "pb_ratio", "debt_to_equity", "net_margin", "revenue_growth",
    "fcf_yield", "ev_to_ebitda", "ev_to_ebit", "roe", "gross_profit",
    "total_assets", "return_1m", "return_3m", "return_6m", "return_1yr",
    "beta", "volatility_60d", "short_interest_ratio", "volume",
    "shares_outstanding", "total_return_index",
]


def _prepare_data(train_df, test_df, feature_cols, label_col="label"):
    """Extract feature arrays and labels. Missing values filled with training median."""
    train_features = train_df[feature_cols]
    medians = train_features.median()
    X_train = train_features.fillna(medians).values
    y_train = train_df[label_col].values
    X_test = test_df[feature_cols].fillna(medians).values
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
