# main.py
from fastapi import FastAPI
from app.config import settings
from app.api.routes import auth

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
)

# 라우터 등록
app.include_router(auth.router)

@app.get("/health")
def health_check():
    """헬스체크"""
    return {
        "status": "healthy",
        "service": settings.app_name
    }
