from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    database_url: str = "postgresql://username:password@localhost:5432/strumind"
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    redis_url: str = "redis://localhost:6379"
    
    # Analysis compute settings
    max_analysis_time: int = 3600  # 1 hour max
    max_elements: int = 100000
    max_nodes: int = 100000
    
    # File upload settings
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: list = [".ifc", ".dxf", ".dwg", ".stp", ".step"]
    
    class Config:
        env_file = ".env"


settings = Settings()
