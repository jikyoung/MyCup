# app/schemas/share.py
from pydantic import BaseModel
from datetime import datetime
from app.schemas.worldcup import RankingPhoto

class ShareCreate(BaseModel):
    """공유 링크 생성 요청"""
    is_public: bool = True
    expires_days: int | None = None  # None이면 만료 없음, 숫자면 N일 후 만료

class ShareResponse(BaseModel):
    """공유 링크 응답"""
    share_id: str
    share_url: str
    worldcup_id: str
    is_public: bool
    expires_at: datetime | None
    created_at: datetime
    
    class Config:
        from_attributes = True

class SharedWorldcupResponse(BaseModel):
    """공유된 월드컵 조회 응답"""
    worldcup_id: str
    username: str
    round_type: int
    rankings: list[RankingPhoto]
    overall_keywords: list[str]
    primary_emotion: str
    insight_story: dict
    card_images: list[str] | None
    created_at: datetime
