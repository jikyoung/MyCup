# app/services/rate_limit_service.py
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models.user import User
from fastapi import HTTPException, status

# 제한 설정
FREE_LIMIT = 5  # 무료: 평생 5번
PREMIUM_MONTHLY_LIMIT = 50  # 프리미엄: 월 50번

def check_worldcup_limit(db: Session, user: User) -> None:
    """
    월드컵 생성 제한 체크
    - 무료: 평생 5번
    - 프리미엄: 월 50번
    """
    
    # 프리미엄 유저
    if user.is_premium:
        # 월 리셋 체크
        now = datetime.now(timezone.utc)
        if user.last_reset_at is None or \
           (now.year > user.last_reset_at.year or now.month > user.last_reset_at.month):
            # 새 달 시작 - 카운터 리셋
            user.monthly_worldcup_count = 0
            user.last_reset_at = now
            db.commit()
        
        # 월 제한 체크
        if user.monthly_worldcup_count >= PREMIUM_MONTHLY_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"프리미엄 유저는 월 {PREMIUM_MONTHLY_LIMIT}회까지 생성 가능합니다. 다음 달에 다시 시도해주세요."
            )
    
    # 무료 유저
    else:
        if user.worldcup_count >= FREE_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"무료 유저는 최대 {FREE_LIMIT}번까지 생성 가능합니다. 프리미엄으로 업그레이드하세요!"
            )

def increment_worldcup_count(db: Session, user: User) -> None:
    """월드컵 생성 카운터 증가"""
    
    user.worldcup_count += 1
    
    if user.is_premium:
        user.monthly_worldcup_count += 1
    
    db.commit()

def get_remaining_count(user: User) -> dict:
    """남은 생성 횟수 조회"""
    
    # None 방어 코드 추가
    if user.worldcup_count is None:
        user.worldcup_count = 0
    if user.monthly_worldcup_count is None:
        user.monthly_worldcup_count = 0
    
    if user.is_premium:
        # 월 리셋 체크
        now = datetime.now(timezone.utc)
        if user.last_reset_at is None or \
           (now.year > user.last_reset_at.year or now.month > user.last_reset_at.month):
            remaining = PREMIUM_MONTHLY_LIMIT
        else:
            remaining = PREMIUM_MONTHLY_LIMIT - user.monthly_worldcup_count
        
        return {
            "tier": "premium",
            "limit": PREMIUM_MONTHLY_LIMIT,
            "used": user.monthly_worldcup_count,
            "remaining": remaining,
            "period": "monthly"
        }
    else:
        remaining = FREE_LIMIT - user.worldcup_count
        
        return {
            "tier": "free",
            "limit": FREE_LIMIT,
            "used": user.worldcup_count,
            "remaining": remaining,
            "period": "lifetime"
        }
