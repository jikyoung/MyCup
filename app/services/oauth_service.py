# app/services/oauth_service.py
from authlib.integrations.starlette_client import OAuth
from app.config import settings
import httpx

# OAuth 클라이언트 초기화
oauth = OAuth()

# Google OAuth
oauth.register(
    name='google',
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# Kakao는 수동 구현 (authlib가 지원 안 함)
KAKAO_AUTH_URL = "https://kauth.kakao.com/oauth/authorize"
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_USER_URL = "https://kapi.kakao.com/v2/user/me"

async def get_kakao_user_info(code: str) -> dict:
    """Kakao OAuth 토큰 교환 & 사용자 정보 조회"""
    
    # 1. 인가 코드로 토큰 받기
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            KAKAO_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": settings.kakao_client_id,
                "redirect_uri": settings.kakao_redirect_uri,
                "code": code
            }
        )
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise Exception("Kakao 토큰 받기 실패")
        
        # 2. 액세스 토큰으로 사용자 정보 조회
        user_response = await client.get(
            KAKAO_USER_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_data = user_response.json()
        
        # 3. 필요한 정보만 추출
        kakao_account = user_data.get("kakao_account", {})
        profile = kakao_account.get("profile", {})
        
        return {
            "provider": "kakao",
            "provider_id": str(user_data.get("id")),
            "email": kakao_account.get("email"),
            "username": profile.get("nickname"),
            "profile_image": profile.get("profile_image_url")
        }
