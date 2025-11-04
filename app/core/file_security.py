# app/core/file_security.py
import os
import mimetypes
from fastapi import UploadFile, HTTPException, status

# 설정
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB (수정)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp"
}

def validate_file_extension(filename: str) -> None:
    """파일 확장자 검증"""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"허용되지 않은 파일 형식입니다. 허용: {', '.join(ALLOWED_EXTENSIONS)}"
        )

def validate_file_size(file: UploadFile) -> None:
    """파일 크기 검증"""
    # 파일 크기 확인
    file.file.seek(0, 2)  # 파일 끝으로 이동
    size = file.file.tell()  # 현재 위치 = 파일 크기
    file.file.seek(0)  # 다시 처음으로
    
    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"파일 크기가 너무 큽니다. 최대: {MAX_FILE_SIZE // 1024 // 1024}MB"
        )

def validate_mime_type(file: UploadFile) -> None:
    """MIME 타입 검증 (간단 버전)"""
    # content_type 체크 (python-magic 없이도 작동)
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"허용되지 않은 파일 형식입니다. 업로드한 타입: {file.content_type}"
        )

def sanitize_filename(filename: str) -> str:
    """파일명 안전하게 변환"""
    # 위험한 문자 제거
    filename = os.path.basename(filename)  # 경로 제거
    filename = filename.replace(" ", "_")  # 공백 → 언더스코어
    
    # 확장자 추출
    name, ext = os.path.splitext(filename)
    
    # 알파벳, 숫자, 언더스코어, 하이픈만 허용
    safe_name = "".join(c for c in name if c.isalnum() or c in "_-")
    
    # 너무 길면 자르기
    if len(safe_name) > 50:
        safe_name = safe_name[:50]
    
    return f"{safe_name}{ext.lower()}"

def validate_uploaded_file(file: UploadFile) -> None:
    """전체 파일 검증"""
    validate_file_extension(file.filename)
    validate_file_size(file)
    validate_mime_type(file)
