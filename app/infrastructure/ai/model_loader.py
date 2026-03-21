from pathlib import Path

import joblib

MODEL_PATH = Path("app/infrastructure/ai/models/triage_model.pkl")


def load_model():
    if not MODEL_PATH.exists():
        return None
    return joblib.load(MODEL_PATH)
