# app/api/routes/worldcup.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.worldcup import Worldcup
from app.models.match import Match
from app.models.photo import Photo
from app.schemas.worldcup import (
    WorldcupCreate, 
    WorldcupResponse, 
    MatchSelectRequest,
    MatchResponse,
    PhotoInMatch,
    WorldcupResultResponse,
    RankingPhoto
)
from app.api.deps import get_current_user
from app.services import worldcup_service

router = APIRouter(prefix="/api/v1/worldcup", tags=["월드컵"])

@router.post("", response_model=WorldcupResponse, status_code=status.HTTP_201_CREATED)
def create_worldcup(
    data: WorldcupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """월드컵 생성"""
    
    # round_type 검증
    if data.round_type not in [4, 8, 16]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="round_type은 4, 8, 16 중 하나여야 합니다"
        )
    
    # 사진 개수 검증
    if len(data.photo_ids) != data.round_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{data.round_type}강은 {data.round_type}장의 사진이 필요합니다"
        )
    
    # 사진 소유권 확인
    photos = db.query(Photo).filter(
        Photo.id.in_(data.photo_ids),
        Photo.user_id == current_user.id
    ).all()
    
    if len(photos) != len(data.photo_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="본인의 사진만 사용할 수 있습니다"
        )
    
    # 월드컵 생성
    worldcup = Worldcup(
        user_id=current_user.id,
        round_type=data.round_type
    )
    db.add(worldcup)
    db.commit()
    db.refresh(worldcup)
    
    # 토너먼트 브라켓 생성
    worldcup_service.create_tournament_bracket(db, worldcup, data.photo_ids)
    
    # 첫 번째 매치 가져오기
    first_match = worldcup_service.get_next_match(db, worldcup.id)
    
    return WorldcupResponse(
        id=worldcup.id,
        round_type=worldcup.round_type,
        status=worldcup.status,
        current_match=MatchResponse(
            id=first_match.id,
            round_number=first_match.round_number,
            match_order=first_match.match_order,
            photo_a=PhotoInMatch(id=first_match.photo_a.id, url=first_match.photo_a.url),
            photo_b=PhotoInMatch(id=first_match.photo_b.id, url=first_match.photo_b.url),
            winner_photo_id=None
        ) if first_match else None,
        created_at=worldcup.created_at
    )

@router.post("/{worldcup_id}/matches/{match_id}/select")
def select_winner(
    worldcup_id: str,
    match_id: str,
    data: MatchSelectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """매치 승자 선택"""
    
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
    
    # 매치 조회
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="매치를 찾을 수 없습니다"
        )
    
    # 이미 선택했는지 확인
    if match.winner_photo_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 선택한 매치입니다"
        )
    
    # 승자가 이 매치의 사진 중 하나인지 확인
    if data.winner_photo_id not in [match.photo_a_id, match.photo_b_id]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 사진입니다"
        )
    
    # 승자 저장
    match.winner_photo_id = data.winner_photo_id
    db.commit()
    
    # 다음 라운드 진행
    worldcup_service.advance_to_next_round(db, worldcup)
    
    # 다음 매치 가져오기
    next_match = worldcup_service.get_next_match(db, worldcup_id)
    
    return {
        "is_completed": worldcup.status == "completed",
        "winner_photo_id": worldcup.winner_photo_id,
        "next_match": MatchResponse(
            id=next_match.id,
            round_number=next_match.round_number,
            match_order=next_match.match_order,
            photo_a=PhotoInMatch(id=next_match.photo_a.id, url=next_match.photo_a.url),
            photo_b=PhotoInMatch(id=next_match.photo_b.id, url=next_match.photo_b.url),
            winner_photo_id=None
        ) if next_match else None
    }

@router.get("/{worldcup_id}/result", response_model=WorldcupResultResponse)
def get_worldcup_result(
    worldcup_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """월드컵 결과 조회"""
    
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
            detail="아직 진행 중인 월드컵입니다"
        )
    
    # 순위 계산
    rankings_data = worldcup_service.get_worldcup_rankings(db, worldcup_id)
    
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
    
    return WorldcupResultResponse(
        worldcup_id=worldcup.id,
        round_type=worldcup.round_type,
        status=worldcup.status,
        rankings=rankings,
        completed_at=worldcup.completed_at
    )
