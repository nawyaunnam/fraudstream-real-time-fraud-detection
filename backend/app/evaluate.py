from datetime import datetime, timezone

import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score
from sqlalchemy import desc, select

from .db import DecisionRecord, MetricSnapshot, SessionLocal


def population_stability_index(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    cuts = np.quantile(expected, np.linspace(0, 1, bins + 1))
    cuts[0], cuts[-1] = -np.inf, np.inf
    e = np.histogram(expected, cuts)[0] / max(len(expected), 1)
    a = np.histogram(actual, cuts)[0] / max(len(actual), 1)
    e, a = np.clip(e, 1e-6, None), np.clip(a, 1e-6, None)
    return float(np.sum((a - e) * np.log(a / e)))


def main():
    with SessionLocal() as db:
        rows = db.scalars(select(DecisionRecord).where(DecisionRecord.is_fraud.is_not(None)).order_by(desc(DecisionRecord.event_time)).limit(10000)).all()
        if len(rows) < 100:
            print("Need at least 100 labeled decisions")
            return
        y = np.array([int(r.is_fraud) for r in rows])
        pred = np.array([int(r.outcome == "flag") for r in rows])
        midpoint = len(rows) // 2
        amounts = np.array([r.amount for r in rows])
        precision, recall, f1 = precision_score(y, pred, zero_division=0), recall_score(y, pred, zero_division=0), f1_score(y, pred, zero_division=0)
        fp = int(((pred == 1) & (y == 0)).sum())
        tn = int(((pred == 0) & (y == 0)).sum())
        snapshot = MetricSnapshot(window="latest-10k", precision=precision, recall=recall, f1=f1, false_positive_rate=fp / max(fp + tn, 1), drift_score=population_stability_index(amounts[midpoint:], amounts[:midpoint]), sample_count=len(rows), recorded_at=datetime.now(timezone.utc))
        db.add(snapshot)
        db.commit()
        print({"precision": precision, "recall": recall, "f1": f1, "false_positive_rate": snapshot.false_positive_rate, "amount_psi": snapshot.drift_score})


if __name__ == "__main__":
    main()
