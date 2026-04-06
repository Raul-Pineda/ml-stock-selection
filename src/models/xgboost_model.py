"""XGBoost — gradient-boosted decision trees, each correcting the last."""

import logging
import pandas as pd
from xgboost import XGBClassifier
from src.models.common import ALL_FEATURES, _add_predictions, _prepare_data

logger = logging.getLogger(__name__)


def xgb_model_fn(train_df, test_df, feature_cols=None, label_col="label"):
    """Train an XGBoost classifier and return (result_df, model)."""
    feature_cols = feature_cols or ALL_FEATURES
    X_train, y_train, X_test = _prepare_data(train_df, test_df, feature_cols, label_col)

    n_pos = y_train.sum()
    model = XGBClassifier(
        n_estimators=300, max_depth=4, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        reg_alpha=0.1, reg_lambda=5.0,
        scale_pos_weight=(len(y_train) - n_pos) / max(n_pos, 1),
        eval_metric="logloss", random_state=42, verbosity=0,
    )
    model.fit(X_train, y_train)

    y_prob = model.predict_proba(X_test)[:, 1]
    result_df = _add_predictions(test_df, y_prob)
    logger.info("XGBoost: train=%d, test=%d, features=%d", len(X_train), len(X_test), len(feature_cols))
    return result_df, model
