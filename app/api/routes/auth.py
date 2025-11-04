# app/api/routes/auth.py
from fastapi.responses import RedirectResponse
from app.services.oauth_service import oauth, get_kakao_user_info
from starlette.requests import Request as StarletteRequest
import logging


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.core.security import hash_password, verify_password, create_access_token
from app.config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["인증"])
logger = logging.getLogger(__name__)

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """회원가입"""
    # 이메일 중복 체크
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용 중인 이메일입니다"
        )
    
    # 새 유저 생성
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password)
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """로그인"""
    # 유저 조회
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 비밀번호 검증
    if not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # JWT 토큰 생성
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60
    }

@router.get("/google")
async def google_login(request: StarletteRequest):
    """Google 로그인 시작"""
    redirect_uri = settings.google_redirect_uri
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def google_callback(
    request: StarletteRequest,
    db: Session = Depends(get_db)
):
    """Google OAuth 콜백"""
    try:
        # Google에서 토큰 받기
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        
        if not user_info:
            raise HTTPException(status_code=400, detail="사용자 정보를 가져올 수 없습니다")
        
        # 이메일로 기존 유저 찾기
        email = user_info.get('email')
        provider_id = user_info.get('sub')
        
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            # 기존 유저 - OAuth 정보 업데이트
            user.provider = "google"
            user.provider_id = provider_id
            user.profile_image = user_info.get('picture')
            db.commit()
        else:
            # 새 유저 생성
            user = User(
                email=email,
                username=user_info.get('name', email.split('@')[0]),
                hashed_password="",  # OAuth 유저는 비밀번호 없음
                provider="google",
                provider_id=provider_id,
                profile_image=user_info.get('picture')
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # JWT 토큰 생성
        access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
        
        # 프론트엔드로 리다이렉트 (토큰 포함)
        return RedirectResponse(
            url=f"http://localhost:3000/auth/callback?token={access_token}"
        )
        
    except Exception as e:
        logger.error(f"Google OAuth 에러: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# ===== Kakao OAuth =====

@router.get("/kakao")
async def kakao_login():
    """Kakao 로그인 시작"""
    kakao_auth_url = (
        f"https://kauth.kakao.com/oauth/authorize"
        f"?client_id={settings.kakao_client_id}"
        f"&redirect_uri={settings.kakao_redirect_uri}"
        f"&response_type=code"
    )
    return RedirectResponse(url=kakao_auth_url)

@router.get("/kakao/callback")
async def kakao_callback(
    code: str,
    db: Session = Depends(get_db)
):
    """Kakao OAuth 콜백"""
    try:
        # Kakao에서 사용자 정보 가져오기
        user_info = await get_kakao_user_info(code)
        
        email = user_info.get('email')
        provider_id = user_info.get('provider_id')
        
        if not email:
            raise HTTPException(status_code=400, detail="이메일 정보를 가져올 수 없습니다")
        
        # 이메일로 기존 유저 찾기
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            # 기존 유저 - OAuth 정보 업데이트
            user.provider = "kakao"
            user.provider_id = provider_id
            user.profile_image = user_info.get('profile_image')
            db.commit()
        else:
            # 새 유저 생성
            user = User(
                email=email,
                username=user_info.get('username', email.split('@')[0]),
                hashed_password="",  # OAuth 유저는 비밀번호 없음
                provider="kakao",
                provider_id=provider_id,
                profile_image=user_info.get('profile_image')
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # JWT 토큰 생성
        access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
        
        # 프론트엔드로 리다이렉트 (토큰 포함)
        return RedirectResponse(
            url=f"http://localhost:3000/auth/callback?token={access_token}"
        )
        
    except Exception as e:
        logger.error(f"Kakao OAuth 에러: {e}")
        raise HTTPException(status_code=400, detail=str(e))
