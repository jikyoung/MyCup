# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """환경변수 설정"""
    
    # API 기본 설정
    app_name: str = "MyCup API"
    debug: bool = True
    
    # Database
    database_url: str
    
    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # OpenAI API (나중에 추가)
    openai_api_key: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# 싱글톤 인스턴스
settings = Settings()
