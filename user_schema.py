from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
import uuid
import re


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str

    @field_validator('password')
    @classmethod
    def check_password_complexity(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_+\-=\[\]\\\/]', v):
            raise ValueError('Password must contain at least one special character')
        return v

    @field_validator('email')
    @classmethod
    def check_email_structure(cls, v: str) -> str:
        parts = v.split('@')
        if len(parts) != 2:
            raise ValueError('Email must contain exactly one @ sign')
        domain = parts[1]
        if '.' not in domain:
            raise ValueError('Email domain must contain at least one dot')
        return v



class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    user_id: uuid.UUID
    email: str
    full_name: str
    role: str
    avatar_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
