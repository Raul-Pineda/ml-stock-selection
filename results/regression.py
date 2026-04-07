import os
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score
)
from scipy.stats import spearmanr

# Load data
script_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(script_dir, "..", "src", "data", "processed", "ml_ready_simfin.csv")
df = pd.read_csv(data_path)

# Temp label
df["label"] = (df["forward_return"] > 0).astype(int)


exclude_cols = [
    "ticker", "quarter", "quarter_date",
    "forward_return", "forward_return_rank", "label"
]

feature_cols = [col for col in df.columns if col not in exclude_cols]

X = df[feature_cols]
y = df["label"]

numeric_features = X.select_dtypes(include=["int64", "float64"]).columns.tolist()
categorical_features = X.select_dtypes(include=["object"]).columns.tolist()


# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

test_forward_returns = df.loc[X_test.index, "forward_return"]


# Preprocessing
numeric_transformer = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler())
])

categorical_transformer = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("onehot", OneHotEncoder(handle_unknown="ignore"))
])

preprocessor = ColumnTransformer([
    ("num", numeric_transformer, numeric_features),
    ("cat", categorical_transformer, categorical_features)
])


# Models
log_model = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", LogisticRegression(penalty="l2", C=1e4, max_iter=2000))
])

ridge_model = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", LogisticRegression(penalty="l2", C=0.1, max_iter=2000))
])


# Evaluation function
def evaluate_model(name, model, X_test, y_test, forward_returns, top_n=30):
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    # Basic classification metrics
    auc = roc_auc_score(y_test, y_prob)
    f1 = f1_score(y_test, y_pred)
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)

    # Create results table
    results = pd.DataFrame({
        "actual_label": y_test.values,
        "pred_prob": y_prob,
        "pred_label": y_pred,
        "forward_return": forward_returns.values
    })

    # Top-N ranking
    top_results = results.sort_values("pred_prob", ascending=False).head(top_n)

    p_at_n = top_results["actual_label"].mean()
    avg_top_return = top_results["forward_return"].mean()

    # Spearman Information Coefficient
    ic, _ = spearmanr(results["pred_prob"], results["forward_return"])

    print(f"\n{name}")
    print("-" * len(name))
    print(f"AUC:       {auc:.4f}")
    print(f"F1:        {f1:.4f}")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"P@{top_n}:    {p_at_n:.4f}")
    print(f"Avg Return Top {top_n}: {avg_top_return:.4f}")
    print(f"IC (Spearman): {ic:.4f}")

    return {
        "Model": name,
        "AUC": auc,
        "IC": ic,
        f"P@{top_n}": p_at_n,
        "F1": f1,
        "Acc": acc,
        "Prec": prec,
        "Rec": rec,
        f"AvgReturnTop{top_n}": avg_top_return
    }


# Train models
log_model.fit(X_train, y_train)
ridge_model.fit(X_train, y_train)

# Evaluate both
log_results = evaluate_model(
    "LogisticRegression",
    log_model,
    X_test,
    y_test,
    test_forward_returns,
    top_n=30
)

ridge_results = evaluate_model(
    "RidgeLogisticRegression",
    ridge_model,
    X_test,
    y_test,
    test_forward_returns,
    top_n=30
)

# Comparison
comparison_df = pd.DataFrame([log_results, ridge_results])

print("\nModel Comparison")
print(comparison_df)
