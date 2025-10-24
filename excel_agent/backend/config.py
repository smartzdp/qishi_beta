"""
Configuration management using pydantic-settings
"""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # OpenAI API Configuration
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    
    # Model Configuration
    llm_model: str = "gpt-4"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    
    # Server Configuration
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    
    # Data Configuration
    data_dir: Path = Path("data")
    knowledge_base_dir: Path = Path("data/knowledge_base")
    samples_dir: Path = Path("data/samples")
    
    # Execution Configuration
    code_execution_timeout: int = 10
    
    # Voice Configuration
    stt_model: str = "whisper-1"
    tts_model: str = "tts-1"
    tts_voice: str = "alloy"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_base_dir.mkdir(parents=True, exist_ok=True)
        self.samples_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

