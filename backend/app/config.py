import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "CWA Temperature Broadcast Service"
    DEBUG: bool = True
    
    # CWA OpenData API Key
    CWA_API_KEY: str = ""
    CWA_DATA_URL: str = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001"
    
    # Cache duration in seconds
    CACHE_TTL_SECONDS: int = 600
    
    # CORS
    CORS_ORIGINS: str = "*"

    @property
    def cors_origin_list(self) -> List[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
