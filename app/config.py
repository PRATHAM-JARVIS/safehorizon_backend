from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional


class Settings(BaseSettings):
    app_name: str = Field("SafeHorizon API", env="APP_NAME")
    app_env: str = Field("development", env="APP_ENV")
    app_debug: bool = Field(True, env="APP_DEBUG")
    api_prefix: str = Field("/api", env="API_PREFIX")

    database_url: str = Field(..., env="DATABASE_URL")
    sync_database_url: str = Field(..., env="SYNC_DATABASE_URL")

    redis_url: str = Field("redis://redis:6379/0", env="REDIS_URL")

    firebase_credentials_json_path: Optional[str] = Field(None, env="FIREBASE_CREDENTIALS_JSON_PATH")

    twilio_account_sid: Optional[str] = Field(None, env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: Optional[str] = Field(None, env="TWILIO_AUTH_TOKEN")
    twilio_from_number: Optional[str] = Field(None, env="TWILIO_FROM_NUMBER")

    models_dir: str = Field("./models_store", env="MODELS_DIR")

    allowed_origins: Optional[str] = Field(None, env="ALLOWED_ORIGINS")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env file

    @property 
    def get_allowed_origins(self) -> List[str]:
        """Get CORS allowed origins, handling both single string and list"""
        if not self.allowed_origins:
            return ["*"]
        
        if isinstance(self.allowed_origins, str):
            # Handle JSON-like string from .env: '["*"]' or '*'
            origins_str = self.allowed_origins.strip()
            
            # Remove brackets and quotes if present
            if origins_str.startswith('[') and origins_str.endswith(']'):
                origins_str = origins_str[1:-1]
            
            # Split by comma and clean up
            origins = []
            for origin in origins_str.split(','):
                clean_origin = origin.strip().strip('"').strip("'")
                if clean_origin:
                    origins.append(clean_origin)
            return origins if origins else ["*"]
        
        if isinstance(self.allowed_origins, list):
            return self.allowed_origins
            
        return ["*"]


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore
