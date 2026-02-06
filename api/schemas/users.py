from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional
from enum import Enum
from datetime import datetime

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    STAFF = "STAFF"
    AUDITOR = "AUDITOR"

class User(BaseModel):
    email: EmailStr = Field(..., description="The email address of the user")
    name: str = Field(..., min_length=1, max_length=120, description="The full name of the user")
    role: UserRole = Field(default=UserRole.STAFF, description="The role of the user within the system")
    active: bool = Field(default=True, description="Indicates if the user is active")

class UserCreate(User):
    email: EmailStr = Field(..., description="The email address for the user account")
    password: str = Field(..., min_length=8, description="The password for the user account")

    @field_validator('email')
    def validate_email(cls, v):
        if not v.strip():
            raise ValueError('email must not be empty or whitespace')
        return v.strip()
    
class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="The email address for login")
    password: str = Field(..., min_length=8, description="The password for login")

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)

class UserResponse(User):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int
    page: int
    page_size: int

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = Field(default="bearer")
    expires_in: int
