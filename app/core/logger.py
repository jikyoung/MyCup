# app/core/logger.py
from loguru import logger
import sys
import os

# 로그 디렉토리 생성
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 기본 로거 제거
logger.remove()

# 콘솔 출력 (개발용)
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)

# 파일 출력 (모든 로그)
logger.add(
    f"{LOG_DIR}/mycup.log",
    rotation="10 MB",  # 10MB마다 새 파일
    retention="30 days",  # 30일 보관
    compression="zip",  # 압축
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG"
)

# 에러 전용 파일
logger.add(
    f"{LOG_DIR}/error.log",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="ERROR"
)
