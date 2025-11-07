# app/services/cardnews_service.py
from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime

# 설정
CARD_WIDTH = 1080
CARD_HEIGHT = 1920
BACKGROUND_COLOR = (255, 255, 255)
PRIMARY_COLOR = (59, 130, 246)  # 파란색
TEXT_COLOR = (17, 24, 39)  # 검은색
SECONDARY_COLOR = (156, 163, 175)  # 회색

FONT_PATH = "app/assets/fonts/AppleSDGothicNeo.ttc"
OUTPUT_DIR = "uploads/cardnews"

# 출력 폴더 생성
os.makedirs(OUTPUT_DIR, exist_ok=True)

def wrap_text(text: str, max_length: int = 40) -> list[str]:
    """텍스트를 지정된 길이로 줄바꿈"""
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        if len(current_line + word) <= max_length:
            current_line += word + " "
        else:
            if current_line:
                lines.append(current_line.strip())
            current_line = word + " "
    
    if current_line:
        lines.append(current_line.strip())
    
    return lines


def create_cover_card(insight_story: dict, overall_keywords: list[str], is_premium: bool = False) -> str:
    """표지 카드 생성"""
    
    # 이미지 생성
    img = Image.new('RGB', (CARD_WIDTH, CARD_HEIGHT), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)
    
    # 폰트
    title_font = ImageFont.truetype(FONT_PATH, 100)
    subtitle_font = ImageFont.truetype(FONT_PATH, 60)
    keyword_font = ImageFont.truetype(FONT_PATH, 50)
    
    # 제목
    draw.text((540, 400), "나의 2024", font=title_font, fill=PRIMARY_COLOR, anchor="mm")
    draw.text((540, 550), "TOP 4", font=title_font, fill=PRIMARY_COLOR, anchor="mm")
    
    # ===== AI 인사이트 (줄바꿈 적용) =====
    summary = insight_story.get("summary", "")
    summary_lines = wrap_text(summary, max_length=20)  # 짧게
    
    y_position = 800
    for line in summary_lines[:2]:  # 최대 2줄
        draw.text((540, y_position), line, font=subtitle_font, fill=TEXT_COLOR, anchor="mm")
        y_position += 80
    
    # detail (작은 글씨)
    detail = insight_story.get("detail", "")
    detail_lines = wrap_text(detail, max_length=25)
    
    y_position = 950
    for line in detail_lines[:2]:  # 최대 2줄
        draw.text((540, y_position), line, font=keyword_font, fill=SECONDARY_COLOR, anchor="mm")
        y_position += 70
    # =====================================
    
    # 키워드
    keywords_text = " · ".join(overall_keywords[:3])
    draw.text((540, 1150), f"#{keywords_text}", font=keyword_font, fill=PRIMARY_COLOR, anchor="mm")
    
    # 날짜
    date_text = datetime.now().strftime("%Y.%m.%d")
    date_font = ImageFont.truetype(FONT_PATH, 40)
    draw.text((540, 1700), date_text, font=date_font, fill=SECONDARY_COLOR, anchor="mm")
    
    # 워터마크
    if not is_premium:
        watermark_font = ImageFont.truetype(FONT_PATH, 35)
        draw.text(
            (540, 1850), 
            "Made with MyCup", 
            font=watermark_font, 
            fill=(180, 180, 180),
            anchor="mm"
        )
    
    # 저장
    filename = f"cover_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    filepath = os.path.join(OUTPUT_DIR, filename)
    img.save(filepath, quality=90)
    
    return filepath


def create_ranking_card(rank: int, photo_path: str, keywords: list[str], is_premium: bool = False) -> str:
    """순위 카드 생성"""
    
    # 이미지 생성
    img = Image.new('RGB', (CARD_WIDTH, CARD_HEIGHT), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)
    
    # 메달 이모지
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    medal = medals.get(rank, "🏅")
    
    # 폰트
    medal_font = ImageFont.truetype(FONT_PATH, 120)
    rank_font = ImageFont.truetype(FONT_PATH, 80)
    keyword_font = ImageFont.truetype(FONT_PATH, 50)
    
    # 메달 & 순위
    draw.text((540, 200), medal, font=medal_font, anchor="mm")
    draw.text((540, 350), f"{rank}위", font=rank_font, fill=TEXT_COLOR, anchor="mm")
    
    # 사진 삽입
    try:
        photo = Image.open(photo_path)
        # 정사각형으로 크롭
        min_side = min(photo.width, photo.height)
        left = (photo.width - min_side) // 2
        top = (photo.height - min_side) // 2
        photo = photo.crop((left, top, left + min_side, top + min_side))
        # 리사이즈
        photo = photo.resize((800, 800), Image.Resampling.LANCZOS)
        # 붙이기
        img.paste(photo, (140, 500))
    except Exception as e:
        print(f"사진 삽입 실패: {e}")
    
    # 키워드
    if keywords:
        keywords_text = " · ".join(keywords[:3])
        draw.text((540, 1400), keywords_text, font=keyword_font, fill=PRIMARY_COLOR, anchor="mm")
    
    # ===== 워터마크 추가 (무료 유저만) =====
    if not is_premium:
        watermark_font = ImageFont.truetype(FONT_PATH, 30)
        draw.text(
            (540, 1850), 
            "Made with MyCup", 
            font=watermark_font, 
            fill=(180, 180, 180), 
            anchor="mm"
        )
    # =====================================
    
    # 저장
    filename = f"rank{rank}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    filepath = os.path.join(OUTPUT_DIR, filename)
    img.save(filepath, quality=90)
    
    return filepath



def generate_cardnews(
    insight_story: dict,
    overall_keywords: list[str],
    rankings: list[dict],
    is_premium: bool = False
) -> list[str]:
    """카드뉴스 생성 (표지 + 순위 카드들)"""
    
    card_paths = []
    
    # 1. 표지 카드
    cover_path = create_cover_card(insight_story, overall_keywords, is_premium)  # 전달
    card_paths.append(cover_path)
    
    # 2. 순위 카드들 (TOP 3)
    for ranking in rankings[:3]:
        rank = ranking["rank"]
        photo_path = ranking["photo_path"]
        keywords = ranking["keywords"]
        
        card_path = create_ranking_card(rank, photo_path, keywords, is_premium)  # 전달
        card_paths.append(card_path)
    
    return card_paths
