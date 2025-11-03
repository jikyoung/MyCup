# app/services/worldcup_service.py
import random
from typing import List
from sqlalchemy.orm import Session
from app.models.worldcup import Worldcup, WorldcupStatus
from app.models.match import Match
from app.models.photo import Photo

def create_tournament_bracket(
    db: Session,
    worldcup: Worldcup,
    photo_ids: List[str]
) -> List[Match]:
    """토너먼트 브라켓 생성"""
    
    # 사진 순서 랜덤 섞기
    shuffled_photos = photo_ids.copy()
    random.shuffle(shuffled_photos)
    
    # 첫 라운드 매치 생성 (준결승 또는 그 이전)
    matches = []
    total_matches = len(photo_ids) // 2
    
    for i in range(total_matches):
        match = Match(
            worldcup_id=worldcup.id,
            round_number=1,
            match_order=i + 1,
            photo_a_id=shuffled_photos[i * 2],
            photo_b_id=shuffled_photos[i * 2 + 1]
        )
        db.add(match)
        matches.append(match)
    
    db.commit()
    
    return matches

def get_next_match(db: Session, worldcup_id: str) -> Match | None:
    """다음 매치 가져오기 (아직 승자가 없는 것)"""
    return db.query(Match)\
        .filter(
            Match.worldcup_id == worldcup_id,
            Match.winner_photo_id == None
        )\
        .order_by(Match.round_number, Match.match_order)\
        .first()

def advance_to_next_round(db: Session, worldcup: Worldcup):
    """다음 라운드로 진행"""
    
    # 현재 라운드의 모든 매치가 끝났는지 확인
    current_round = db.query(Match.round_number)\
        .filter(Match.worldcup_id == worldcup.id)\
        .order_by(Match.round_number.desc())\
        .first()[0]
    
    current_matches = db.query(Match)\
        .filter(
            Match.worldcup_id == worldcup.id,
            Match.round_number == current_round
        )\
        .all()
    
    # 모든 매치에 승자가 있는지 확인
    if not all(m.winner_photo_id for m in current_matches):
        return  # 아직 끝나지 않음
    
    # 승자들 모으기
    winners = [m.winner_photo_id for m in current_matches]
    
    # 승자가 1명이면 월드컵 종료
    if len(winners) == 1:
        worldcup.status = WorldcupStatus.COMPLETED
        worldcup.winner_photo_id = winners[0]
        from datetime import datetime, timezone
        worldcup.completed_at = datetime.now(timezone.utc)
        db.commit()
        return
    
    # 다음 라운드 매치 생성
    next_round = current_round + 1
    for i in range(len(winners) // 2):
        match = Match(
            worldcup_id=worldcup.id,
            round_number=next_round,
            match_order=i + 1,
            photo_a_id=winners[i * 2],
            photo_b_id=winners[i * 2 + 1]
        )
        db.add(match)
    
    db.commit()

def get_worldcup_rankings(db: Session, worldcup_id: str) -> List[dict]:
    """월드컵 순위 계산"""
    
    # 모든 매치 가져오기
    matches = db.query(Match)\
        .filter(Match.worldcup_id == worldcup_id)\
        .order_by(Match.round_number.desc(), Match.match_order)\
        .all()
    
    if not matches:
        return []
    
    # 결승전 (마지막 라운드)
    final_round = matches[0].round_number
    final_match = matches[0]
    
    # 1위: 결승 승자
    winner_id = final_match.winner_photo_id
    
    # 2위: 결승 패자
    runner_up_id = final_match.photo_a_id if final_match.photo_b_id == winner_id else final_match.photo_b_id
    
    # 3-4위: 준결승 패자들
    semifinal_losers = []
    if final_round > 1:  # 4강 이상일 때만 준결승 있음
        semifinal_matches = [m for m in matches if m.round_number == final_round - 1]
        for match in semifinal_matches:
            loser_id = match.photo_a_id if match.photo_b_id == match.winner_photo_id else match.photo_b_id
            semifinal_losers.append(loser_id)
    
    # 순위 매기기
    rankings = []
    
    # 1위
    winner_photo = db.query(Photo).filter(Photo.id == winner_id).first()
    if winner_photo:
        rankings.append({"rank": 1, "photo_id": winner_id, "photo": winner_photo})
    
    # 2위
    runner_up_photo = db.query(Photo).filter(Photo.id == runner_up_id).first()
    if runner_up_photo:
        rankings.append({"rank": 2, "photo_id": runner_up_id, "photo": runner_up_photo})
    
    # 3-4위
    for i, loser_id in enumerate(semifinal_losers):
        loser_photo = db.query(Photo).filter(Photo.id == loser_id).first()
        if loser_photo:
            rankings.append({"rank": 3, "photo_id": loser_id, "photo": loser_photo})
    
    return rankings
