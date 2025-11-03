# app/services/ai_service.py
from openai import OpenAI
from app.config import settings
import base64
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import APIError, APITimeoutError, RateLimitError

# OpenAI 클라이언트 초기화 (타임아웃 설정)
client = OpenAI(
    api_key=settings.openai_api_key,
    timeout=30.0  # 30초 타임아웃
)

def encode_image_to_base64(image_path: str) -> str:
    """이미지 파일을 base64로 인코딩"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

@retry(
    stop=stop_after_attempt(3),  # 3번 재시도
    wait=wait_exponential(multiplier=1, min=2, max=10),  # 2초, 4초, 8초 대기
    retry=retry_if_exception_type((APIError, APITimeoutError, RateLimitError)),
    reraise=True
)
def analyze_photo_from_path(image_path: str) -> dict:
    """파일 경로로 사진 분석 (재시도 포함)"""
    
    try:
        # 이미지를 base64로 인코딩
        base64_image = encode_image_to_base64(image_path)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "이 사진을 분석해서 다음 정보를 JSON 형식으로 알려줘:\n1. keywords: 이 사진의 주요 키워드 3개 (한글)\n2. emotion: 사진의 감정 (happy/peaceful/excited/nostalgic 중 하나)\n3. description: 사진에 대한 한 줄 설명 (한글, 20자 이내)\n\n응답은 반드시 JSON만 출력해줘."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        
        # 응답 가져오기
        content = response.choices[0].message.content.strip()
        
        # 마크다운 코드 블록 제거
        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()
        
        # JSON 파싱
        import json
        result = json.loads(content)
        
        return {
            "keywords": result.get("keywords", []),
            "emotion": result.get("emotion", "peaceful"),
            "description": result.get("description", "")
        }
        
    except (APIError, APITimeoutError, RateLimitError) as e:
        # 재시도 가능한 에러 - tenacity가 자동 재시도
        print(f"OpenAI API 에러 (재시도 중): {e}")
        raise
        
    except Exception as e:
        # 재시도 불가능한 에러 - 기본값 반환
        print(f"AI 분석 실패 (복구 불가): {e}")
        return {
            "keywords": ["추억", "순간", "감성"],
            "emotion": "peaceful",
            "description": "특별한 순간"
        }

def analyze_multiple_photos(photo_paths: list[str]) -> dict:
    """여러 사진 배치 분석 (에러 핸들링 강화)"""
    
    results = []
    all_keywords = []
    emotions = []
    failed_count = 0
    
    # 각 사진 개별 분석
    for path in photo_paths:
        try:
            analysis = analyze_photo_from_path(path)
            results.append({
                "path": path,
                "keywords": analysis["keywords"],
                "emotion": analysis["emotion"],
                "description": analysis["description"]
            })
            
            # 전체 키워드 모으기
            all_keywords.extend(analysis["keywords"])
            emotions.append(analysis["emotion"])
            
        except Exception as e:
            print(f"사진 분석 실패 ({path}): {e}")
            failed_count += 1
            # 실패해도 계속 진행
            continue
    
    # 최소 1장이라도 성공해야 함
    if not results:
        raise Exception("모든 사진 분석 실패")
    
    # 키워드 빈도 계산
    from collections import Counter
    keyword_counts = Counter(all_keywords)
    top_keywords = [k for k, v in keyword_counts.most_common(5)]
    
    # 주요 감정
    emotion_counts = Counter(emotions)
    primary_emotion = emotion_counts.most_common(1)[0][0] if emotions else "peaceful"
    
    return {
        "total_photos": len(photo_paths),
        "analyzed_photos": len(results),
        "failed_photos": failed_count,
        "individual_results": results,
        "overall_keywords": top_keywords,
        "primary_emotion": primary_emotion,
        "emotion_distribution": dict(emotion_counts)
    }

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((APIError, APITimeoutError, RateLimitError)),
    reraise=True
)
def generate_insight_story(analysis_result: dict, winner_photo_analysis: dict) -> str:
    """AI 인사이트 스토리 생성 (재시도 포함)"""
    
    try:
        prompt = f"""
사용자의 사진 분석 결과를 바탕으로 감성적인 인사이트를 한글로 작성해줘:

전체 키워드: {', '.join(analysis_result['overall_keywords'])}
주요 감정: {analysis_result['primary_emotion']}
1위 사진 키워드: {', '.join(winner_photo_analysis['keywords'])}
1위 사진 감정: {winner_photo_analysis['emotion']}

다음 형식으로 작성:
1. 한 줄 요약 (20자 이내)
2. 상세 설명 (50자 이내)

JSON 형식으로만 답변:
{{
  "summary": "한 줄 요약",
  "detail": "상세 설명"
}}"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        
        content = response.choices[0].message.content.strip()
        
        # 마크다운 제거
        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()
        
        import json
        result = json.loads(content)
        
        return result
        
    except (APIError, APITimeoutError, RateLimitError) as e:
        # 재시도 가능한 에러
        print(f"OpenAI API 에러 (재시도 중): {e}")
        raise
        
    except Exception as e:
        # 재시도 불가능한 에러 - 기본값 반환
        print(f"인사이트 생성 실패: {e}")
        return {
            "summary": "당신의 특별한 순간들",
            "detail": "소중한 추억이 담긴 사진들입니다."
        }

def test_openai_connection() -> bool:
    """OpenAI 연결 테스트"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        return True
    except Exception as e:
        print(f"OpenAI 연결 실패: {e}")
        return False
