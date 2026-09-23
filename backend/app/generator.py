import os
import random
import time
from datetime import datetime, timezone

from confluent_kafka import Producer

from .config import settings
from .schemas import Transaction

CITIES = [("US", 40.71, -74.01), ("US", 37.77, -122.42), ("GB", 51.51, -0.13), ("DE", 52.52, 13.40), ("SG", 1.35, 103.82)]


def transaction() -> Transaction:
    user = f"usr_{random.randint(1, 500):04d}"
    fraud = random.random() < 0.045
    country, lat, lon = random.choice(CITIES)
    amount = random.lognormvariate(3.8, 0.9)
    if fraud:
        amount *= random.uniform(8, 25)
        country, lat, lon = random.choice(CITIES)
    return Transaction(user_id=user, merchant_id=f"mrc_{random.randint(1, 120):03d}", amount=round(amount, 2), country=country, latitude=lat + random.uniform(-0.1, 0.1), longitude=lon + random.uniform(-0.1, 0.1), device_id=f"dev_{random.randint(1, 800):04d}" if fraud else f"dev_{int(user[-4:]):04d}", card_present=random.random() < 0.35, event_time=datetime.now(timezone.utc), is_fraud=fraud)


def main() -> None:
    rate = int(os.getenv("GENERATOR_RATE", settings.generator_rate))
    producer = Producer({"bootstrap.servers": settings.kafka_bootstrap_servers, "enable.idempotence": True, "linger.ms": 10, "compression.type": "snappy"})
    while True:
        tx = transaction()
        producer.produce("transactions", key=tx.user_id, value=tx.model_dump_json().encode())
        producer.poll(0)
        time.sleep(1 / max(rate, 1))


if __name__ == "__main__":
    main()

