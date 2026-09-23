from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


class DecisionRecord(Base):
    __tablename__ = "decisions"
    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    merchant_id: Mapped[str] = mapped_column(String(64), index=True)
    amount: Mapped[float] = mapped_column(Float)
    country: Mapped[str] = mapped_column(String(8), index=True)
    outcome: Mapped[str] = mapped_column(String(16), index=True)
    rule_score: Mapped[float] = mapped_column(Float)
    model_score: Mapped[float] = mapped_column(Float)
    combined_score: Mapped[float] = mapped_column(Float)
    reasons: Mapped[list] = mapped_column(JSON)
    features: Mapped[dict] = mapped_column(JSON)
    is_fraud: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    latency_ms: Mapped[float] = mapped_column(Float)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )


class MetricSnapshot(Base):
    __tablename__ = "metric_snapshots"
    id: Mapped[int] = mapped_column(primary_key=True)
    window: Mapped[str] = mapped_column(String(32), index=True)
    precision: Mapped[float] = mapped_column(Float)
    recall: Mapped[float] = mapped_column(Float)
    f1: Mapped[float] = mapped_column(Float)
    false_positive_rate: Mapped[float] = mapped_column(Float)
    drift_score: Mapped[float] = mapped_column(Float)
    sample_count: Mapped[int] = mapped_column(Integer)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(engine)


def get_db():
    with SessionLocal() as session:
        yield session

