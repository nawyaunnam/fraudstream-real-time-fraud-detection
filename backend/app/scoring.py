from pathlib import Path

import joblib
import numpy as np

from .schemas import Features

FEATURE_ORDER = ["amount", "velocity_1m", "velocity_1h", "amount_zscore", "distance_from_last_km", "seconds_since_last", "new_device", "country_changed", "card_present"]


def rule_score(f: Features) -> tuple[float, list[str]]:
    score, reasons = 0.0, []
    checks = [(f.velocity_1m >= 4, 0.35, "high_velocity"), (f.amount_zscore >= 3, 0.30, "unusual_amount"), (f.distance_from_last_km >= 800 and f.seconds_since_last < 7200, 0.35, "impossible_travel"), (f.new_device and f.amount >= 750, 0.20, "new_device_high_value"), (f.country_changed == 1, 0.15, "country_change")]
    for matched, weight, reason in checks:
        if matched:
            score += weight
            reasons.append(reason)
    return round(min(score, 1.0), 5), reasons


class FraudModel:
    def __init__(self, path: str):
        self.model = joblib.load(path) if Path(path).exists() else None

    def predict(self, features: Features) -> float:
        row = np.array([[getattr(features, name) for name in FEATURE_ORDER]], dtype=float)
        if self.model is not None:
            return float(self.model.predict_proba(row)[0, 1])
        # Deterministic fallback lets the complete pipeline run before training.
        raw = 0.08 + min(features.velocity_1m / 10, 0.35) + min(max(features.amount_zscore, 0) / 10, 0.3) + (0.2 if features.country_changed else 0) + (0.15 if features.new_device else 0)
        return min(raw, 0.99)


def combine(rule: float, model: float) -> float:
    return round(0.40 * rule + 0.60 * model, 5)
