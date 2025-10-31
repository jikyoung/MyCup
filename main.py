# main.py
from fastapi import FastAPI

app = FastAPI(title="MyCup API")

@app.get("/")
def health_check():
    """서버 작동 확인"""
    return {"status": "ok", "message": "MyCup API is running"}

@app.get("/health")
def health():
    """헬스체크 엔드포인트"""
    return {"status": "healthy"}
