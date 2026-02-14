from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    model_config = {"env_prefix": "EPOCH_"}

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://epoch:epoch@localhost:5432/epoch"
    database_url_sync: str = "postgresql+psycopg2://epoch:epoch@localhost:5432/epoch"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Scheduler
    scheduler_loop_interval: float = 1.0  # seconds
    leader_heartbeat_interval: float = 5.0  # seconds
    leader_lock_ttl: float = 15.0  # seconds

    # Worker
    worker_max_slots: int = 4
    worker_heartbeat_interval: float = 5.0  # seconds
    worker_heartbeat_timeout: float = 30.0  # seconds

    # Jobs
    default_job_timeout: int = 3600  # 1 hour
    default_max_retries: int = 3
    retry_base_delay: float = 5.0  # seconds
    retry_max_delay: float = 300.0  # 5 minutes

    # Checkpoint
    checkpoint_dir: str = "/tmp/epoch-checkpoints"
    checkpoint_interval: float = 30.0  # seconds


settings = Settings()
