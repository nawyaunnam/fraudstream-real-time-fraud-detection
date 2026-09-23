from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class Transaction(BaseModel):
    transaction_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    merchant_id: str
    amount: float = Field(gt=0)
    currency: str = "USD"
    country: str = "US"
    latitude: float
    longitude: float
    device_id: str
    card_present: bool = False
    event_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_fraud: bool | None = None


class Features(BaseModel):
    amount: float
    velocity_1m: int
    velocity_1h: int
    amount_zscore: float
    distance_from_last_km: float
    seconds_since_last: float
    new_device: int
    country_changed: int
    card_present: int


class Decision(BaseModel):
    transaction_id: str
    outcome: Literal["approve", "flag"]
    rule_score: float
    model_score: float
    combined_score: float
    reasons: list[str]
    latency_ms: float
    decided_at: datetime

