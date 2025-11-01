# app/schemas/photo.py
from pydantic import BaseModel
from datetime import datetime

class PhotoResponse(BaseModel):
    """사진 응답"""
    id: str
    filename: str
    url: str
    thumbnail_url: str | None
    file_size: str
    uploaded_at: datetime
    
    class Config:
        from_attributes = True

class PhotoUploadResponse(BaseModel):
    """사진 업로드 응답"""
    photos: list[PhotoResponse]
    total: int
