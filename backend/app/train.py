import argparse
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier


def dataset(n: int = 25000, seed: int = 42):
    rng = np.random.default_rng(seed)
    amount = rng.lognormal(3.8, 1.0, n)
    v1m = rng.poisson(0.7, n)
    v1h = v1m + rng.poisson(4, n)
    z = rng.normal(0, 1.4, n)
    distance = rng.exponential(45, n)
    seconds = rng.exponential(10000, n)
    new_device = rng.binomial(1, 0.12, n)
    country = rng.binomial(1, 0.05, n)
    card = rng.binomial(1, 0.35, n)
    logits = -5 + 0.008 * amount + 0.7 * v1m + 0.45 * np.maximum(z, 0) + 0.004 * distance * (seconds < 7200) + 1.0 * new_device + 1.1 * country - 0.4 * card
    probability = 1 / (1 + np.exp(-np.clip(logits, -20, 20)))
    y = rng.binomial(1, probability)
    return np.column_stack([amount, v1m, v1h, z, distance, seconds, new_device, country, card]), y


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="models/fraud_model.joblib")
    args = parser.parse_args()
    x, y = dataset()
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=.2, stratify=y, random_state=42)
    model = XGBClassifier(n_estimators=180, max_depth=5, learning_rate=.07, subsample=.85, colsample_bytree=.85, eval_metric="logloss", n_jobs=2)
    model.fit(x_train, y_train)
    print(classification_report(y_test, model.predict(x_test), digits=4))
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.output)


if __name__ == "__main__":
    main()

