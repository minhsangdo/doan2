from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    email: str 
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime
    khoi_thi: Optional[str] = None
    diem_du_kien: Optional[float] = None
    
    class Config:
        from_attributes = True

class ProfileUpdateRequest(BaseModel):
    khoi_thi: Optional[str] = None
    diem_du_kien: Optional[float] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class ChatMessageBase(BaseModel):
    role: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True

class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: List[ChatMessageBase]


# === Ngành quan tâm (Favorites) ===
class FavoriteMajorAdd(BaseModel):
    ma_nganh: str
    ten_nganh: Optional[str] = None


class FavoriteMajorResponse(BaseModel):
    id: int
    ma_nganh: str
    ten_nganh: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# === Phản hồi câu trả lời (Feedback) ===
class FeedbackSubmit(BaseModel):
    message_id: int
    rating: str  # 'up' | 'down'
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    message: str
