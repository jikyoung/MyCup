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
    RankingPhoto,
    WorldcupInsightResponse, 
    PhotoAnalysis,
    CardNewsResponse
)
from app.api.deps import get_current_user
from app.services import worldcup_service, ai_service, cardnews_service

from datetime import datetime, timezone
import os

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
    
    # 월드컵 완료되면 AI 분석 자동 실행
    if worldcup.status == "completed":
        try:
            # 순위 계산
            rankings_data = worldcup_service.get_worldcup_rankings(db, worldcup_id)
            
            # AI 분석
            photo_paths = [item["photo"].file_path for item in rankings_data]
            batch_analysis = ai_service.analyze_multiple_photos(photo_paths)
            winner_analysis = ai_service.analyze_photo_from_path(rankings_data[0]["photo"].file_path)
            insight_story = ai_service.generate_insight_story(batch_analysis, winner_analysis)
            
            # 결과 저장
            worldcup.analysis_result = {
                "overall_keywords": batch_analysis["overall_keywords"],
                "primary_emotion": batch_analysis["primary_emotion"],
                "insight_story": insight_story
            }
            db.commit()
            
        except Exception as e:
            print(f"AI 분석 실패 (백그라운드): {e}")
            # 실패해도 월드컵 완료는 계속
    
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

@router.get("/{worldcup_id}/insights", response_model=WorldcupInsightResponse)
def get_worldcup_insights(
    worldcup_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """월드컵 AI 인사이트 조회"""
    
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
    
    # 캐시된 분석 결과 확인
    if worldcup.analysis_result:
        # 캐시 사용 (빠름!)
        print("캐시된 분석 결과 사용")
        analysis_data = worldcup.analysis_result
        overall_keywords = analysis_data["overall_keywords"]
        primary_emotion = analysis_data["primary_emotion"]
        insight_story = analysis_data["insight_story"]
        
        # 1위 사진 분석 (캐시에 없으면 실시간)
        winner_analysis_result = ai_service.analyze_photo_from_path(rankings_data[0]["photo"].file_path)
    else:
        # 실시간 분석 (느림, 첫 조회만)
        print("실시간 AI 분석 실행")
        photo_paths = [item["photo"].file_path for item in rankings_data]
        batch_analysis = ai_service.analyze_multiple_photos(photo_paths)
        winner_analysis_result = ai_service.analyze_photo_from_path(rankings_data[0]["photo"].file_path)
        insight_story = ai_service.generate_insight_story(batch_analysis, winner_analysis_result)
        
        overall_keywords = batch_analysis["overall_keywords"]
        primary_emotion = batch_analysis["primary_emotion"]
        
        # 결과 저장
        worldcup.analysis_result = {
            "overall_keywords": overall_keywords,
            "primary_emotion": primary_emotion,
            "insight_story": insight_story
        }
        db.commit()
    
    return WorldcupInsightResponse(
        worldcup_id=worldcup.id,
        rankings=rankings,
        overall_keywords=overall_keywords,
        primary_emotion=primary_emotion,
        winner_analysis=PhotoAnalysis(
            keywords=winner_analysis_result["keywords"],
            emotion=winner_analysis_result["emotion"],
            description=winner_analysis_result["description"]
        ),
        insight_story=insight_story
    )

@router.get("/test/openai")
def test_openai():
    """OpenAI 연결 테스트"""
    is_connected = ai_service.test_openai_connection()
    return {
        "openai_connected": is_connected,
        "message": "연결 성공!" if is_connected else "연결 실패"
    }

@router.post("/test/analyze-photo")
def test_analyze_photo(file_path: str):
    """사진 분석 테스트 (파일 경로)"""
    result = ai_service.analyze_photo_from_path(file_path)
    return result

@router.post("/test/analyze-multiple")
def test_analyze_multiple(file_paths: list[str]):
    """여러 사진 배치 분석 테스트"""
    result = ai_service.analyze_multiple_photos(file_paths)
    return result

@router.post("/test/generate-insight")
def test_generate_insight():
    """인사이트 스토리 생성 테스트"""
    # 샘플 데이터
    analysis_result = {
        "overall_keywords": ["가족", "아기", "행복"],
        "primary_emotion": "peaceful"
    }
    winner_photo = {
        "keywords": ["아기", "미소"],
        "emotion": "happy"
    }
    
    story = ai_service.generate_insight_story(analysis_result, winner_photo)
    return story

@router.post("/{worldcup_id}/cardnews", response_model=CardNewsResponse)
def generate_cardnews(
    worldcup_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """카드뉴스 생성"""
    
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
    
    # AI 분석
    photo_paths = [item["photo"].file_path for item in rankings_data]
    batch_analysis = ai_service.analyze_multiple_photos(photo_paths)
    winner_analysis = ai_service.analyze_photo_from_path(rankings_data[0]["photo"].file_path)
    insight_story = ai_service.generate_insight_story(batch_analysis, winner_analysis)
    
    # 카드뉴스 데이터 준비
    rankings_for_card = []
    for item in rankings_data[:3]:  # TOP 3만
        # 개별 사진 분석
        photo_analysis = ai_service.analyze_photo_from_path(item["photo"].file_path)
        rankings_for_card.append({
            "rank": item["rank"],
            "photo_path": item["photo"].file_path,
            "keywords": photo_analysis["keywords"]
        })
    
    # 카드뉴스 생성
    card_paths = cardnews_service.generate_cardnews(
        insight_story=insight_story,
        overall_keywords=batch_analysis["overall_keywords"],
        rankings=rankings_for_card
    )
    
    # URL로 변환
    card_urls = [f"/uploads/cardnews/{os.path.basename(path)}" for path in card_paths]
    
    return CardNewsResponse(
        worldcup_id=worldcup_id,
        card_images=card_urls,
        total_cards=len(card_urls),
        created_at=datetime.now(timezone.utc)
    )
