from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """API configuration settings."""
    
    # API Key Settings
    REST_API_KEY: str
    WS_API_KEY: str
    
    # CORS Settings
    CORS_ORIGINS: str = "*"  # Comma-separated list of origins or "*" for all
    
    @property
    def cors_origins(self) -> List[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # Socket.IO Settings
    socketio_ping_timeout: int = 5
    socketio_ping_interval: int = 25
    socketio_max_http_buffer_size: int = 1000000
    
    # Agent Settings
    agent_max_retries: int = 3
    agent_scratchpad_dir: str = "scratchpads"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8" 