# Architecture

## Online path

The generator publishes schema-valid JSON to `transactions`, keyed by `user_id`. Each decision worker owns Kafka partitions, calculates point-in-time features from Redis, evaluates rules and the model, writes an immutable PostgreSQL record, publishes the decision, and then commits the input offset. Invalid events go to `fraud-dead-letter` with a bounded error header.

The write and Kafka commit are not a distributed transaction. The unique transaction ID makes database retries safe, but the example does not yet recover a database success followed by a publish failure. A production deployment can use a transactional outbox or Kafka transactions.

## Data contracts

`Transaction` and `Features` are Pydantic contracts. For multi-team deployments, register equivalent Avro or Protobuf schemas in a schema registry, use backward-compatible evolution, and reject unknown major versions.

## Feature correctness

Features are computed from Redis state before the current event is inserted. This avoids self-counting and training/serving leakage. Kafka customer keys preserve order within a partition. Late arrivals require event-time watermarks and recomputation policies beyond this example.

## Evaluation

The simulator emits delayed-label stand-ins as `is_fraud`. `evaluate.py` compares final decisions with those labels, calculating precision, recall, F1, false-positive rate, and amount PSI. In production, join chargebacks or confirmed investigation outcomes only after their label maturity window.

## Threat model

Treat transaction data as sensitive. Terminate TLS at ingress, encrypt brokers and databases, keep secrets in a managed secret store, restrict analyst access by tenant and role, audit case access, redact logs, and set retention policies. Validate event sizes and identities at ingestion to limit abuse.

