from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, Field
from typing import List, Optional


class Settings(BaseSettings):
    app_name: str = Field("SafeHorizon API", env="APP_NAME")
    app_env: str = Field("development", env="APP_ENV")
    app_debug: bool = Field(True, env="APP_DEBUG")
    api_prefix: str = Field("/api", env="API_PREFIX")

    database_url: str = Field(..., env="DATABASE_URL")
    sync_database_url: str = Field(..., env="SYNC_DATABASE_URL")

    supabase_url: Optional[AnyHttpUrl] = Field(None, env="SUPABASE_URL")
    supabase_anon_key: Optional[str] = Field(None, env="SUPABASE_ANON_KEY")
    supabase_service_role_key: Optional[str] = Field(None, env="SUPABASE_SERVICE_ROLE_KEY")
    supabase_jwt_secret: Optional[str] = Field(None, env="SUPABASE_JWT_SECRET")

    redis_url: str = Field("redis://redis:6379/0", env="REDIS_URL")

    firebase_credentials_json_path: Optional[str] = Field(None, env="FIREBASE_CREDENTIALS_JSON_PATH")

    twilio_account_sid: Optional[str] = Field(None, env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: Optional[str] = Field(None, env="TWILIO_AUTH_TOKEN")
    twilio_from_number: Optional[str] = Field(None, env="TWILIO_FROM_NUMBER")

    models_dir: str = Field("./models_store", env="MODELS_DIR")

    allowed_origins: List[str] = Field(default_factory=lambda: ["*"], env="ALLOWED_ORIGINS")

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property 
    def get_allowed_origins(self) -> List[str]:
        """Get CORS allowed origins, handling both single string and list"""
        if isinstance(self.allowed_origins, str):
            # If it's a single string, split by comma or return as single item
            if "," in self.allowed_origins:
                return [origin.strip() for origin in self.allowed_origins.split(",")]
            else:
                return [self.allowed_origins]
        return self.allowed_origins


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore
