"""
evaluate.py

Evaluation utilities for churn models. Because churn datasets are
imbalanced (far more "No churn" than "Churn"), accuracy alone is not
trusted - precision, recall, F1 and ROC-AUC are all reported together.
"""

from typing import Any, Dict

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def evaluate_model(pipeline, X_test, y_test, model_name: str = "model") -> Dict[str, Any]:
    """
    Runs predictions on the held-out test set and returns a dictionary of
    standard classification metrics plus the confusion matrix.
    """
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    metrics = {
        "model_name": model_name,
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_proba)), 4),
        "confusion_matrix": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp),
        },
        "test_set_size": int(len(y_test)),
        "positive_rate_actual": round(float(np.mean(y_test)), 4),
        "positive_rate_predicted": round(float(np.mean(y_pred)), 4),
    }
    return metrics
