# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserCreate(BaseModel):
    """회원가입 요청"""
    email: EmailStr
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)

class UserLogin(BaseModel):
    """로그인 요청"""
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """유저 응답"""
    id: str
    email: str
    username: str
    is_premium: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    """JWT 토큰 응답"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
