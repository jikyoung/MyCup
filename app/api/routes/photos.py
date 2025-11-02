# app/api/routes/photos.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
import shutil

from app.database import get_db
from app.models.user import User
from app.models.photo import Photo
from app.schemas.photo import PhotoResponse, PhotoUploadResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/photos", tags=["사진"])

# 업로드 설정
UPLOAD_DIR = "uploads/photos"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

@router.post("/upload", response_model=PhotoUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_photos(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사진 업로드 (최대 16장)"""
    
    # 파일 개수 체크
    if len(files) > 16:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="최대 16장까지 업로드 가능합니다"
        )
    
    uploaded_photos = []
    
    for file in files:
        # 파일 확장자 체크
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"지원하지 않는 파일 형식입니다: {file_ext}"
            )
        
        # 파일 크기 체크
        file.file.seek(0, 2)  # 파일 끝으로 이동
        file_size = file.file.tell()  # 현재 위치 = 파일 크기
        file.file.seek(0)  # 다시 처음으로
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"파일 크기는 10MB 이하여야 합니다"
            )
        
        # 고유한 파일명 생성
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # 파일 저장
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # DB에 저장
        photo = Photo(
            user_id=current_user.id,
            filename=file.filename,
            file_path=file_path,
            file_size=str(file_size),
            url=f"/uploads/photos/{unique_filename}",
            thumbnail_url=None  # 나중에 썸네일 생성
        )
        
        db.add(photo)
        uploaded_photos.append(photo)
    
    db.commit()
    
    # refresh (DB에서 생성된 값 가져오기)
    for photo in uploaded_photos:
        db.refresh(photo)
    
    return {
        "photos": uploaded_photos,
        "total": len(uploaded_photos)
    }

@router.get("/", response_model=List[PhotoResponse])
def get_my_photos(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 개수"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """내 사진 목록 조회 (페이지네이션)"""
    
    # 전체 개수
    total = db.query(Photo).filter(Photo.user_id == current_user.id).count()
    
    # 페이지네이션
    skip = (page - 1) * limit
    photos = db.query(Photo)\
        .filter(Photo.user_id == current_user.id)\
        .order_by(Photo.uploaded_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return photos

@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(
    photo_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사진 삭제"""
    
    # 사진 조회
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사진을 찾을 수 없습니다"
        )
    
    # 권한 체크 (본인 사진만 삭제 가능)
    if photo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="삭제 권한이 없습니다"
        )
    
    # 파일 삭제
    if os.path.exists(photo.file_path):
        os.remove(photo.file_path)
    
    # DB에서 삭제
    db.delete(photo)
    db.commit()
    
    return None
