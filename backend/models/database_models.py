from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True) # Added for password reset
    hashed_password = Column(String)
    reset_token = Column(String, unique=True, index=True, nullable=True)
    reset_token_expire = Column(DateTime, nullable=True)
    khoi_thi = Column(String, nullable=True) # e.g. A00, A01
    diem_du_kien = Column(Integer, nullable=True) # e.g. 22
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("ChatSession", back_populates="user")
    favorite_majors = relationship("UserFavoriteMajor", back_populates="user")
    feedbacks = relationship("MessageFeedback", back_populates="user")

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, index=True) # UUID session
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("chat_sessions.id"))
    role = Column(String) # 'user' or 'bot'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")
    feedbacks = relationship("MessageFeedback", back_populates="message")


class UserFavoriteMajor(Base):
    """Ngành học người dùng quan tâm / đã lưu."""
    __tablename__ = "user_favorite_majors"
    __table_args__ = (UniqueConstraint("user_id", "ma_nganh", name="uq_user_ma_nganh"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ma_nganh = Column(String, nullable=False, index=True)
    ten_nganh = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="favorite_majors")


class MessageFeedback(Base):
    """Đánh giá / phản hồi của người dùng cho câu trả lời (thể hiện hữu ích hay báo sai)."""
    __tablename__ = "message_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    rating = Column(String, nullable=False)  # 'up' | 'down' hoặc '1'..'5'
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    message = relationship("ChatMessage", back_populates="feedbacks")
    user = relationship("User", back_populates="feedbacks")
