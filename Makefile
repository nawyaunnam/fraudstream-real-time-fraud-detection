.PHONY: up down test lint train evaluate
up:
	cp .env.example .env 2>/dev/null || true
	docker compose up --build
down:
	docker compose down -v
test:
	pytest -q
lint:
	ruff check backend
train:
	python -m app.train --output models/fraud_model.joblib
evaluate:
	python -m app.evaluate

