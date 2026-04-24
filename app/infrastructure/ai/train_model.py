from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

DATA_PATH = Path("data/issues.csv")
MODEL_PATH = Path("app/infrastructure/ai/models/triage_model.pkl")


def train_model():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Training data not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    required_columns = {"title", "body", "label"}
    missing = required_columns.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in dataset: {sorted(missing)}")

    df = df.dropna(subset=["label"]).copy()
    if df.empty:
        raise ValueError("Dataset contains no labeled rows.")

    texts = (df["title"].fillna("") + " " + df["body"].fillna("")).tolist()
    labels = df["label"].astype(str).tolist()

    model = Pipeline(
        [
            ("tfidf", TfidfVectorizer()),
            ("clf", MultinomialNB()),
        ]
    )

    model.fit(texts, labels)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    return MODEL_PATH


if __name__ == "__main__":
    path = train_model()
    print(f"Model trained and saved to: {path}")
