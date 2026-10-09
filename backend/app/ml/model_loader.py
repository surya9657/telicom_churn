"""
model_loader.py

Loads the trained Random Forest pipeline (preprocessing + classifier) that
was produced offline by ml/train.py. The model is loaded ONCE at process
startup and cached, so the API never retrains or reloads the model on every
request.
"""

import json
import os
import threading

import joblib

from app.core.config import get_settings

settings = get_settings()

_model = None
_model_lock = threading.Lock()
_metrics_cache = None


class ModelNotFoundError(RuntimeError):
    """Raised when the trained model file is missing from disk."""


def get_model():
    """
    Returns the cached, trained scikit-learn Pipeline (preprocessor +
    RandomForestClassifier). Loads it from disk on first call only.
    """
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:  # double-checked locking
                path = settings.model_path_resolved
                if not os.path.exists(path):
                    raise ModelNotFoundError(
                        f"Trained model not found at '{path}'. Run 'python ml/train.py' first."
                    )
                _model = joblib.load(path)
    return _model


def get_model_metrics() -> dict:
    """Returns the evaluation metrics saved alongside the model."""
    global _metrics_cache
    if _metrics_cache is None:
        path = settings.metrics_path_resolved
        if not os.path.exists(path):
            raise ModelNotFoundError(
                f"Model metrics not found at '{path}'. Run 'python ml/train.py' first."
            )
        with open(path) as f:
            _metrics_cache = json.load(f)
    return _metrics_cache


def reload_model():
    """Utility for tests / admin tooling to force a fresh load from disk."""
    global _model, _metrics_cache
    with _model_lock:
        _model = None
        _metrics_cache = None
    return get_model()
