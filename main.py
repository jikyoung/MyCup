# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.api.routes import auth, photos, worldcup

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
)

# 라우터 등록
app.include_router(auth.router)
app.include_router(photos.router)
app.include_router(worldcup.router)

# 정적 파일 서빙 (업로드된 이미지)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/health")
def health_check():
    """헬스체크"""
    return {
        "status": "healthy",
        "service": settings.app_name
    }
