# app/models/worldcup.py
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum

class WorldcupStatus(str, enum.Enum):
    """월드컵 상태"""
    IN_PROGRESS = "in_progress"  # 진행 중
    COMPLETED = "completed"       # 완료

class Worldcup(Base):
    """월드컵 모델"""
    __tablename__ = "worldcups"
    
    # 기본 필드
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 게임 설정
    round_type = Column(Integer, nullable=False)  # 4, 8, 16
    status = Column(SQLEnum(WorldcupStatus), default=WorldcupStatus.IN_PROGRESS)
    
    # 결과
    winner_photo_id = Column(String, ForeignKey("photos.id", ondelete="SET NULL"), nullable=True)
    
    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    analysis_result = Column(JSON, nullable=True)
        
    # 관계
    user = relationship("User", backref="worldcups")
    winner = relationship("Photo", foreign_keys=[winner_photo_id])
    matches = relationship("Match", back_populates="worldcup", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Worldcup {self.round_type}강 - {self.status}>"
