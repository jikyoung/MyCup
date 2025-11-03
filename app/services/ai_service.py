# app/services/ai_service.py
from openai import OpenAI
from app.config import settings
import base64

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=settings.openai_api_key)

def encode_image_to_base64(image_path: str) -> str:
    """이미지 파일을 base64로 인코딩"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_photo_from_path(image_path: str) -> dict:
    """파일 경로로 사진 분석"""
    
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
            # ```json 과 ``` 제거
            content = content.replace("```json", "").replace("```", "").strip()
        
        # JSON 파싱
        import json
        result = json.loads(content)
        
        return {
            "keywords": result.get("keywords", []),
            "emotion": result.get("emotion", "peaceful"),
            "description": result.get("description", "")
        }
        
    except Exception as e:
        print(f"AI 분석 오류: {e}")
        return {
            "keywords": [],
            "emotion": "peaceful",
            "description": f"분석 실패: {str(e)}"
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
