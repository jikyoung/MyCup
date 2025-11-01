# main.py
from fastapi import FastAPI
from app.config import settings
from app.api.routes import auth

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
)

app.include_router(auth.router)

@app.get("/")
def health_check():
    """서버 작동 확인"""
    return {
        "status": "ok",
        "message": f"{settings.app_name} is running"
    }

@app.get("/health")
def health():
    """헬스체크"""
    return {"status": "healthy"}
