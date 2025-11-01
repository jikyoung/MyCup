# app/models/user.py
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base
import uuid

class User(Base):
    """유저 모델"""
    __tablename__ = "users"
    
    # 기본 필드
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # 계정 상태
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    
    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<User {self.email}>"
