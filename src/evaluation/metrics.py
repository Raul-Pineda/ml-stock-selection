"""Metrics for measuring how well models pick stocks."""

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)


def classification_metrics(y_true, y_pred, y_prob=None):
    """Standard classification scores: accuracy, precision, recall, F1, AUC."""
    results = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }
    if y_prob is not None and len(np.unique(y_true)) > 1:
        results["roc_auc"] = float(roc_auc_score(y_true, y_prob))
    else:
        results["roc_auc"] = None
    return results


def spearman_rank_correlation(predicted_scores, actual_returns):
    """How well does the model's ranking match reality? +1 = perfect."""
    mask = np.isfinite(predicted_scores) & np.isfinite(actual_returns)
    if mask.sum() < 3:
        return 0.0, 1.0
    ic, p = stats.spearmanr(np.asarray(predicted_scores)[mask], np.asarray(actual_returns)[mask])
    return float(ic), float(p)


def ndcg_at_k(predicted_scores, actual_returns, k=30):
    """How good are the top K picks vs the actual top K? 1.0 = perfect."""
    pred = np.asarray(predicted_scores, dtype=float)
    actual = np.asarray(actual_returns, dtype=float)
    mask = np.isfinite(pred) & np.isfinite(actual)
    pred, actual = pred[mask], actual[mask]

    k = min(k, len(pred))
    if k == 0:
        return 0.0

    discount = np.log2(np.arange(2, k + 2))
    dcg = np.sum(actual[np.argsort(-pred)[:k]] / discount)
    ideal = np.sum(actual[np.argsort(-actual)[:k]] / discount)
    return 0.0 if abs(ideal) < 1e-10 else float(dcg / ideal)


def precision_at_k(predicted_scores, actual_returns, k=30, threshold_percentile=80):
    """Of the top K picks, what fraction were actually top performers?"""
    pred = np.asarray(predicted_scores, dtype=float)
    actual = np.asarray(actual_returns, dtype=float)
    mask = np.isfinite(pred) & np.isfinite(actual)
    pred, actual = pred[mask], actual[mask]

    k = min(k, len(pred))
    if k == 0:
        return 0.0

    top_k = np.argsort(-pred)[:k]
    threshold = np.percentile(actual, threshold_percentile)
    return float((actual[top_k] >= threshold).mean())


def evaluate_ranking(test_df, score_col="predicted_score", return_col="forward_return_rank",
                     label_col="label", pred_label_col="predicted_label", k=30):
    """Run all metrics on a test set."""
    scores = test_df[score_col].values
    returns = test_df[return_col].values

    ic, p = spearman_rank_correlation(scores, returns)
    results = {
        "spearman_ic": ic, "spearman_p_value": p,
        "ndcg_at_k": ndcg_at_k(scores, returns, k=k),
        "precision_at_k": precision_at_k(scores, returns, k=k, threshold_percentile=80),
    }

    if label_col in test_df.columns and pred_label_col in test_df.columns:
        results.update(classification_metrics(test_df[label_col].values,
                                              test_df[pred_label_col].values, scores))
    return results
