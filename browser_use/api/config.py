from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """API configuration settings."""
    
    # JWT Settings
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    
    # CORS Settings
    cors_origins: List[str] = ["*"]
    
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