from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Rental Property Scraper"
    api_prefix: str = "/api/v1"
    debug: bool = False

    database_url: str = Field(
        default="sqlite:///./test.db",
        description="Database URL - use env var in production"
    )
    redis_url: str = Field(
        default="redis://redis:6379/0",
        description="Redis URL - use env var in production"
    )

    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    scrape_url: str = "https://raw.githubusercontent.com/appbrewery/Zillow-Clone/master/index.html"
    request_timeout: int = 20
    max_retries: int = 3
    retry_backoff_seconds: float = 2.0
    retry_delay_seconds: int = 60

    user_agents: list[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    ]
    proxies: list[str] = []

    sentence_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # CORS configuration
    allowed_origins: list[str] = ["*"]
    allow_credentials: bool = True
    allow_methods: list[str] = ["*"]
    allow_headers: list[str] = ["*"]
    
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    
    # Request timeouts (in seconds)
    db_pool_size: int = 20
    db_max_overflow: int = 40
    db_pool_recycle: int = 3600
    
    # Health check settings
    health_check_timeout: int = 5
    
    # API Authentication
    api_key_enabled: bool = False
    api_key: str = ""
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json" if not debug else "plain"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def broker(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def backend(self) -> str:
        return self.celery_result_backend or self.redis_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
