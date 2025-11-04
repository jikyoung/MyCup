# app/core/logging_middleware.py
from fastapi import Request
from app.core.logger import logger
import time

async def log_requests(request: Request, call_next):
    """모든 요청/응답 로깅"""
    
    # 요청 시작 시간
    start_time = time.time()
    
    # 요청 정보 로깅
    logger.info(f"➡️  {request.method} {request.url.path}")
    
    # 요청 처리
    try:
        response = await call_next(request)
        
        # 응답 시간 계산
        process_time = (time.time() - start_time) * 1000  # ms
        
        # 응답 로깅
        logger.info(
            f"⬅️  {request.method} {request.url.path} "
            f"- Status: {response.status_code} "
            f"- Time: {process_time:.2f}ms"
        )
        
        return response
        
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        
        # 에러 로깅
        logger.error(
            f"❌ {request.method} {request.url.path} "
            f"- Error: {str(e)} "
            f"- Time: {process_time:.2f}ms"
        )
        logger.exception("Exception details:")
        
        raise
