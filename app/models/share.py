# app/models/share.py
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid
from datetime import datetime, timedelta, timezone

class Share(Base):
    """공유 링크 모델"""
    __tablename__ = "shares"
    
    # 기본 필드
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4())[:8])  # 짧은 ID
    worldcup_id = Column(String, ForeignKey("worldcups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 설정
    is_public = Column(Boolean, default=True)
    
    # 만료
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계
    worldcup = relationship("Worldcup")
    user = relationship("User")
    
    def is_expired(self) -> bool:
        """만료 여부 확인"""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def __repr__(self):
        return f"<Share {self.id}>"
