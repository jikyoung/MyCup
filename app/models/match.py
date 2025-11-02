# app/models/match.py
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

class Match(Base):
    """매치 모델 (1:1 대결)"""
    __tablename__ = "matches"
    
    # 기본 필드
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    worldcup_id = Column(String, ForeignKey("worldcups.id", ondelete="CASCADE"), nullable=False)
    
    # 라운드 정보
    round_number = Column(Integer, nullable=False)  # 1(준결승), 2(결승)
    match_order = Column(Integer, nullable=False)   # 같은 라운드 내 순서
    
    # 대결 사진
    photo_a_id = Column(String, ForeignKey("photos.id", ondelete="CASCADE"), nullable=False)
    photo_b_id = Column(String, ForeignKey("photos.id", ondelete="CASCADE"), nullable=False)
    
    # 결과
    winner_photo_id = Column(String, ForeignKey("photos.id", ondelete="SET NULL"), nullable=True)
    
    # 관계
    worldcup = relationship("Worldcup", back_populates="matches")
    photo_a = relationship("Photo", foreign_keys=[photo_a_id])
    photo_b = relationship("Photo", foreign_keys=[photo_b_id])
    winner = relationship("Photo", foreign_keys=[winner_photo_id])
    
    def __repr__(self):
        return f"<Match Round {self.round_number} - {self.match_order}>"
