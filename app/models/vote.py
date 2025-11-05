# app/models/vote.py
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid

class Vote(Base):
    """투표 모델"""
    __tablename__ = "votes"
    
    # 기본 필드
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    worldcup_id = Column(String, ForeignKey("worldcups.id", ondelete="CASCADE"), nullable=False)
    
    # 투표자 정보
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # 로그인 안 해도 가능
    ip_address = Column(String, nullable=False)  # 중복 투표 방지
    
    # 투표 결과
    rankings = Column(JSON, nullable=False)  # [{"photo_id": "...", "rank": 1}, ...]
    
    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계
    worldcup = relationship("Worldcup", backref="votes")
    user = relationship("User", backref="votes")
    
    def __repr__(self):
        return f"<Vote {self.id} for Worldcup {self.worldcup_id}>"
