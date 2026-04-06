"""Random Forest for Magic Formula stock selection."""

from sklearn.ensemble import RandomForestClassifier
from src.models.common import _add_predictions, _prepare_data

# columns that are metadata or targets, not features
_SKIP = {"ticker", "quarter", "sector", "industry",
         "quarter_date", "forward_return", "forward_return_rank", "label"}


def detect_features(df):
    """Auto-detect numeric feature columns (everything that isn't metadata/target)."""
    return [c for c in df.select_dtypes(include="number").columns if c not in _SKIP]


def rf_model_fn(train_df, test_df, feature_cols=None, label_col="label"):
    """Train RF, return (result_df, fitted model). Pass None for feature_cols to auto-detect."""
    feature_cols = feature_cols if feature_cols is not None else detect_features(train_df)
    X_train, y_train, X_test = _prepare_data(train_df, test_df, feature_cols, label_col)

    model = RandomForestClassifier(
        n_estimators=300, max_depth=6, min_samples_leaf=30,
        max_features="sqrt", class_weight="balanced",
        oob_score=True, n_jobs=-1, random_state=42)
    model.fit(X_train, y_train)

    y_prob = model.predict_proba(X_test)[:, 1]
    return _add_predictions(test_df, y_prob), model
