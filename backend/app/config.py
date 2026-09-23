from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./fraudstream.db"
    redis_url: str = "redis://localhost:6379/0"
    kafka_bootstrap_servers: str = "localhost:9092"
    jwt_secret: str = "development-secret-change-me-please"
    model_path: str = "models/fraud_model.joblib"
    decision_threshold: float = 0.70
    generator_rate: int = 25


settings = Settings()

