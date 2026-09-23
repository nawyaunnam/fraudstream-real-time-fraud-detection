import math

from redis import Redis

from .schemas import Features, Transaction


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


class FeaturePipeline:
    """Atomic Redis feature calculation; features are computed before state mutation."""

    def __init__(self, redis: Redis):
        self.redis = redis

    def calculate(self, tx: Transaction) -> Features:
        key = f"user:{tx.user_id}"
        now = tx.event_time.timestamp()
        velocity = f"{key}:velocity"
        pipe = self.redis.pipeline(transaction=True)
        pipe.zremrangebyscore(velocity, 0, now - 3600)
        pipe.zcount(velocity, now - 60, now)
        pipe.zcard(velocity)
        pipe.hgetall(f"{key}:profile")
        _, count_1m, count_1h, raw = pipe.execute()
        profile = {k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v for k, v in raw.items()}
        mean = float(profile.get("mean", tx.amount))
        variance = max(float(profile.get("variance", 0)), 1.0)
        last_time = float(profile.get("last_time", now))
        distance = 0.0
        if "lat" in profile:
            distance = haversine_km(float(profile["lat"]), float(profile["lon"]), tx.latitude, tx.longitude)
        device_key = f"{key}:devices"
        new_device = 0 if self.redis.sismember(device_key, tx.device_id) else 1
        country_changed = int(bool(profile.get("country")) and profile["country"] != tx.country)
        n = int(profile.get("n", 0)) + 1
        delta = tx.amount - mean
        new_mean = mean + delta / n
        new_variance = ((n - 1) * variance + delta * (tx.amount - new_mean)) / max(n, 1)
        member = f"{tx.transaction_id}:{now}"
        pipe = self.redis.pipeline(transaction=True)
        pipe.zadd(velocity, {member: now})
        pipe.expire(velocity, 3700)
        pipe.sadd(device_key, tx.device_id)
        pipe.expire(device_key, 86400 * 90)
        pipe.hset(f"{key}:profile", mapping={"mean": new_mean, "variance": max(new_variance, 1), "n": n, "lat": tx.latitude, "lon": tx.longitude, "country": tx.country, "last_time": now})
        pipe.expire(f"{key}:profile", 86400 * 90)
        pipe.execute()
        return Features(amount=tx.amount, velocity_1m=int(count_1m), velocity_1h=int(count_1h), amount_zscore=(tx.amount - mean) / math.sqrt(variance), distance_from_last_km=distance, seconds_since_last=max(now - last_time, 0), new_device=new_device, country_changed=country_changed, card_present=int(tx.card_present))
