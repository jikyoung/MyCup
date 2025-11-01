# app/models/photo.py
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid

class Photo(Base):
    """사진 모델"""
    __tablename__ = "photos"
    
    # 기본 필드
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 파일 정보
    filename = Column(String, nullable=False)  # 원본 파일명
    file_path = Column(String, nullable=False)  # 저장 경로
    file_size = Column(String)  # 파일 크기 (bytes)
    
    # URL
    url = Column(String, nullable=False)  # 이미지 URL
    thumbnail_url = Column(String)  # 썸네일 URL (나중에)
    
    # 타임스탬프
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계
    user = relationship("User", backref="photos")
    
    def __repr__(self):
        return f"<Photo {self.filename}>"
