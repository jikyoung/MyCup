# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# 데이터베이스 엔진 생성
engine = create_engine(
    settings.database_url,
    echo=settings.debug  # SQL 쿼리 로그 출력
)

# 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 (모든 모델의 부모)
Base = declarative_base()

# DB 세션 의존성 (FastAPI에서 사용)
def get_db():
    """DB 세션 생성 및 종료"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
