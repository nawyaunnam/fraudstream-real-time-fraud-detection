import json
import signal
import time
from datetime import datetime, timezone

from confluent_kafka import Consumer, KafkaError, Producer
from redis import Redis

from .config import settings
from .db import DecisionRecord, SessionLocal, init_db
from .features import FeaturePipeline
from .schemas import Transaction
from .scoring import FraudModel, combine, rule_score

running = True


def process(tx: Transaction, features: FeaturePipeline, model: FraudModel) -> dict:
    started = time.perf_counter()
    vector = features.calculate(tx)
    rules, reasons = rule_score(vector)
    ml = model.predict(vector)
    score = combine(rules, ml)
    outcome = "flag" if score >= settings.decision_threshold or rules >= 0.70 else "approve"
    decided_at = datetime.now(timezone.utc)
    latency = (time.perf_counter() - started) * 1000
    result = {"transaction_id": tx.transaction_id, "user_id": tx.user_id, "merchant_id": tx.merchant_id, "amount": tx.amount, "country": tx.country, "outcome": outcome, "rule_score": rules, "model_score": round(ml, 5), "combined_score": score, "reasons": reasons, "latency_ms": round(latency, 3), "event_time": tx.event_time.isoformat(), "decided_at": decided_at.isoformat()}
    with SessionLocal() as db:
        db.add(DecisionRecord(**{**result, "features": vector.model_dump(), "is_fraud": tx.is_fraud, "event_time": tx.event_time, "decided_at": decided_at}))
        db.commit()
    return result


def main() -> None:
    global running
    init_db()
    redis = Redis.from_url(settings.redis_url)
    features = FeaturePipeline(redis)
    model = FraudModel(settings.model_path)
    consumer = Consumer({"bootstrap.servers": settings.kafka_bootstrap_servers, "group.id": "fraud-decision-v1", "enable.auto.commit": False, "auto.offset.reset": "earliest"})
    producer = Producer({"bootstrap.servers": settings.kafka_bootstrap_servers, "enable.idempotence": True})
    consumer.subscribe(["transactions"])
    signal.signal(signal.SIGTERM, lambda *_: globals().__setitem__("running", False))
    while running:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() != KafkaError._PARTITION_EOF:
                print(msg.error(), flush=True)
            continue
        try:
            tx = Transaction.model_validate_json(msg.value())
            result = process(tx, features, model)
            payload = json.dumps(result).encode()
            producer.produce("fraud-decisions", key=tx.user_id, value=payload)
            producer.flush(5)
            redis.publish("fraudstream:decisions", payload)
            consumer.commit(message=msg, asynchronous=False)
        except Exception as exc:
            producer.produce("fraud-dead-letter", key=msg.key(), value=msg.value(), headers={"error": str(exc)[:500]})
            producer.flush(5)
            consumer.commit(message=msg, asynchronous=False)
    consumer.close()


if __name__ == "__main__":
    main()

