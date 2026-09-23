# Deployment

1. Build immutable API, worker, generator, and frontend images in CI.
2. Train and validate a model, store the artifact in versioned S3, and pin its digest in the worker release.
3. Provision private networking, MSK, RDS PostgreSQL, ElastiCache Redis, S3, KMS keys, and workload identity.
4. Apply database migrations before deploying consumers.
5. Deploy the API and workers with the Kubernetes examples, replacing image names and secrets.
6. Run shadow scoring, compare the challenger with the current decision policy, then increase traffic gradually.

Scale workers on Kafka consumer lag with KEDA in a production cluster. The included HPA uses CPU as a portable baseline. Alert on consumer lag, p95 decision latency, DLQ growth, Redis evictions, database errors, flag-rate shifts, calibration, PSI, and slice-level false-positive rates.

Never commit `.env`. Rotate the demo JWT secret, disable the demo login endpoint, connect an OIDC provider, and use network policies before exposing the service.

