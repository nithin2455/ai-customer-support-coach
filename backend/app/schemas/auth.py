from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)
    confirm_password: Optional[str] = None


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    customer_id: Optional[int] = None
    agent_id: Optional[int] = None
    tier: Optional[str] = None
    department_name: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
