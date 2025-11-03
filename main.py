# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import auth, photos, worldcup, share

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
)

origins = [
    "http://localhost:3000",  # React 개발 서버
    "http://localhost:8081",  # React Native Expo
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8081",
    "https://mycup.app",      # 프로덕션 도메인 (나중에)
    "https://www.mycup.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 허용할 origin 리스트
    allow_credentials=True,
    allow_methods=["*"],    # 모든 HTTP 메소드 허용
    allow_headers=["*"],    # 모든 헤더 허용
)

# 라우터 등록
app.include_router(auth.router)
app.include_router(photos.router)
app.include_router(worldcup.router)
app.include_router(share.router)

# 정적 파일 서빙 (업로드된 이미지)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/health")
def health_check():
    """헬스체크"""
    return {
        "status": "healthy",
        "service": settings.app_name
    }
