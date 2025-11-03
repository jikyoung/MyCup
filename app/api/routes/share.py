# app/api/routes/share.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone

from app.database import get_db
from app.models.user import User
from app.models.worldcup import Worldcup
from app.models.share import Share
from app.schemas.share import ShareCreate, ShareResponse, SharedWorldcupResponse
from app.schemas.worldcup import RankingPhoto, PhotoInMatch
from app.api.deps import get_current_user
from app.services import worldcup_service, ai_service

router = APIRouter(prefix="/api/v1/share", tags=["공유"])

@router.post("/worldcup/{worldcup_id}", response_model=ShareResponse, status_code=status.HTTP_201_CREATED)
def create_share_link(
    worldcup_id: str,
    data: ShareCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """공유 링크 생성"""
    
    # 월드컵 조회
    worldcup = db.query(Worldcup).filter(Worldcup.id == worldcup_id).first()
    if not worldcup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="월드컵을 찾을 수 없습니다"
        )
    
    # 권한 체크
    if worldcup.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="권한이 없습니다"
        )
    
    # 완료 여부 확인
    if worldcup.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="완료된 월드컵만 공유할 수 있습니다"
        )
    
    # 만료 날짜 계산
    expires_at = None
    if data.expires_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=data.expires_days)
    
    # 기존 공유 확인 (같은 월드컵)
    existing_share = db.query(Share).filter(
        Share.worldcup_id == worldcup_id,
        Share.user_id == current_user.id
    ).first()
    
    if existing_share:
        # 기존 공유 업데이트
        existing_share.is_public = data.is_public
        existing_share.expires_at = expires_at
        db.commit()
        db.refresh(existing_share)
        share = existing_share
    else:
        # 새 공유 생성
        share = Share(
            worldcup_id=worldcup_id,
            user_id=current_user.id,
            is_public=data.is_public,
            expires_at=expires_at
        )
        db.add(share)
        db.commit()
        db.refresh(share)
    
    # 공유 URL 생성
    share_url = f"https://mycup.app/share/{share.id}"  # 프로덕션 URL
    
    return ShareResponse(
        share_id=share.id,
        share_url=share_url,
        worldcup_id=share.worldcup_id,
        is_public=share.is_public,
        expires_at=share.expires_at,
        created_at=share.created_at
    )

@router.get("/{share_id}", response_model=SharedWorldcupResponse)
@router.get("/{share_id}", response_model=SharedWorldcupResponse)
def get_shared_worldcup(
    share_id: str,
    db: Session = Depends(get_db)
):
    """공유된 월드컵 조회 (인증 불필요)"""
    
    # 공유 링크 조회
    share = db.query(Share).filter(Share.id == share_id).first()
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="공유 링크를 찾을 수 없습니다"
        )
    
    # 만료 확인
    if share.is_expired():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="만료된 공유 링크입니다"
        )
    
    # 공개 여부 확인
    if not share.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비공개 처리된 공유 링크입니다"
        )
    
    # 월드컵 조회
    worldcup = share.worldcup
    user = share.user
    
    # 순위 계산
    rankings_data = worldcup_service.get_worldcup_rankings(db, worldcup.id)
    rankings = [
        RankingPhoto(
            rank=item["rank"],
            photo=PhotoInMatch(
                id=item["photo"].id,
                url=item["photo"].url
            )
        )
        for item in rankings_data
    ]
    
    # 캐시된 분석 결과 확인
    if worldcup.analysis_result:
        # 캐시 사용 (빠름!)
        print("캐시된 분석 결과 사용")
        analysis_data = worldcup.analysis_result
        overall_keywords = analysis_data["overall_keywords"]
        primary_emotion = analysis_data["primary_emotion"]
        insight_story = analysis_data["insight_story"]
    else:
        # 실시간 분석 (느림, 첫 조회만)
        print("실시간 AI 분석 실행")
        photo_paths = [item["photo"].file_path for item in rankings_data]
        batch_analysis = ai_service.analyze_multiple_photos(photo_paths)
        winner_analysis = ai_service.analyze_photo_from_path(rankings_data[0]["photo"].file_path)
        insight_story = ai_service.generate_insight_story(batch_analysis, winner_analysis)
        
        overall_keywords = batch_analysis["overall_keywords"]
        primary_emotion = batch_analysis["primary_emotion"]
        
        # 결과 저장 (다음번엔 빠름)
        worldcup.analysis_result = {
            "overall_keywords": overall_keywords,
            "primary_emotion": primary_emotion,
            "insight_story": insight_story
        }
        db.commit()
    
    return SharedWorldcupResponse(
        worldcup_id=worldcup.id,
        username=user.username,
        round_type=worldcup.round_type,
        rankings=rankings,
        overall_keywords=overall_keywords,
        primary_emotion=primary_emotion,
        insight_story=insight_story,
        card_images=None,
        created_at=worldcup.created_at
    )
