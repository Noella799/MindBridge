from typing import Literal

from pydantic import BaseModel, Field


class SignupRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=150)
    password: str = Field(min_length=4, max_length=128)
    role: Literal["child", "parent", "teacher", "counsellor"]


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=150)
    password: str


class CheckInRequest(BaseModel):
    feeling: str = Field(min_length=2, max_length=50)
    reason: str = Field(min_length=2, max_length=1000)
    support_requested: bool = False


class StatusUpdateRequest(BaseModel):
    is_active: bool


class AdviceRequest(BaseModel):
    child_id: int
    message: str = Field(min_length=2, max_length=1500)
