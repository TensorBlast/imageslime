"""
Configuration settings for ImageSlime application.
"""

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # SAM3 model configuration
    SAM3_MODEL_PATH: str = "sam3.pt"
    SAM3_DEVICE: str = "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES", "") else "cpu"
    SAM3_HALF_PRECISION: bool = True  # Use FP16 for faster inference
    
    # Image storage
    UPLOAD_DIR: str = "uploads"
    TEMP_DIR: str = "temp"
    MAX_IMAGE_SIZE: int = 4096  # Maximum image dimension in pixels
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB max upload
    
    # WebSocket configuration
    SOCKETIO_CORS_ALLOW_ALL: bool = True
    SOCKETIO_ASYNC_MODE: str = "asgi"
    
    # Performance settings
    EMBEDDING_CACHE_SIZE: int = 10  # Number of image embeddings to cache
    SEGMENTATION_CONFIDENCE: float = 0.25  # Minimum confidence for segmentation
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings
