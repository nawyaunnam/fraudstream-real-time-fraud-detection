import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import case, desc, func, select
from sqlalchemy.orm import Session
from starlette.responses import Response

from .auth import create_token, current_user
from .config import settings
from .db import DecisionRecord, MetricSnapshot, get_db, init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="FraudStream API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "fraudstream-api"}


@app.post("/api/auth/demo")
def demo_login():
    return {"access_token": create_token("demo-analyst", "analyst"), "token_type": "bearer"}


@app.get("/api/decisions")
def decisions(outcome: str | None = None, query: str | None = None, limit: int = Query(50, le=200), db: Session = Depends(get_db), _: dict = Depends(current_user)):
    stmt = select(DecisionRecord)
    if outcome:
        stmt = stmt.where(DecisionRecord.outcome == outcome)
    if query:
        stmt = stmt.where(DecisionRecord.transaction_id.contains(query) | DecisionRecord.user_id.contains(query) | DecisionRecord.merchant_id.contains(query))
    rows = db.scalars(stmt.order_by(desc(DecisionRecord.decided_at)).limit(limit)).all()
    return [{"transaction_id": r.transaction_id, "user_id": r.user_id, "merchant_id": r.merchant_id, "amount": r.amount, "country": r.country, "outcome": r.outcome, "rule_score": r.rule_score, "model_score": r.model_score, "combined_score": r.combined_score, "reasons": r.reasons, "latency_ms": r.latency_ms, "event_time": r.event_time} for r in rows]


@app.get("/api/overview")
def overview(db: Session = Depends(get_db), _: dict = Depends(current_user)):
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    total, flagged, avg_latency = db.execute(select(func.count(), func.sum(case((DecisionRecord.outcome == "flag", 1), else_=0)), func.avg(DecisionRecord.latency_ms)).where(DecisionRecord.decided_at >= since)).one()
    recent = db.scalar(select(MetricSnapshot).order_by(desc(MetricSnapshot.recorded_at)).limit(1))
    countries = db.execute(select(DecisionRecord.country, func.count()).where(DecisionRecord.decided_at >= since).group_by(DecisionRecord.country).order_by(desc(func.count())).limit(8)).all()
    return {"total": total or 0, "flagged": flagged or 0, "approval_rate": round(100 * ((total or 0) - (flagged or 0)) / max(total or 0, 1), 2), "avg_latency_ms": round(avg_latency or 0, 2), "precision": recent.precision if recent else 0, "recall": recent.recall if recent else 0, "f1": recent.f1 if recent else 0, "false_positive_rate": recent.false_positive_rate if recent else 0, "drift_score": recent.drift_score if recent else 0, "countries": [{"country": c, "count": n} for c, n in countries]}


@app.get("/metrics")
def prometheus_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.websocket("/ws/decisions")
async def live_decisions(websocket: WebSocket, token: str):
    try:
        current_user(f"Bearer {token}")
    except Exception:
        await websocket.close(code=4401)
        return
    await websocket.accept()
    import redis.asyncio as aioredis
    client = aioredis.from_url(settings.redis_url)
    pubsub = client.pubsub()
    await pubsub.subscribe("fraudstream:decisions")
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1)
            if message:
                data = message["data"].decode() if isinstance(message["data"], bytes) else message["data"]
                await websocket.send_text(data)
            await asyncio.sleep(0.05)
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.close()
        await client.aclose()
