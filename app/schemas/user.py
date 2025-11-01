# app/schemas/user.py
from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserCreate(BaseModel):
    """회원가입 요청"""
    email: EmailStr
    username: str
    password: str

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
