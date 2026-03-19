import logging
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List

from core.database import get_db
from core.security import verify_password, get_password_hash, create_access_token
from models.database_models import User, ChatSession, ChatMessage, UserFavoriteMajor
from models.auth_schemas import (
    UserCreate, UserResponse, Token, ChatHistoryResponse, ChatMessageBase,
    ForgotPasswordRequest, ResetPasswordRequest, ProfileUpdateRequest,
    FavoriteMajorAdd, FavoriteMajorResponse
)
from core.email_utils import send_reset_email, is_email_sending_configured
import secrets
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _resolve_frontend_base(request: Request) -> str:
    """URL gốc của frontend (link trong email). Ưu tiên FRONTEND_URL, sau đó Origin/Referer (ổn cho HF Space)."""
    import os
    explicit = (os.environ.get("FRONTEND_URL") or "").strip().rstrip("/")
    if explicit:
        return explicit
    origin = (request.headers.get("origin") or "").strip().rstrip("/")
    if origin:
        return origin
    referer = request.headers.get("referer") or ""
    if referer:
        parsed = urlparse(referer)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    return "http://localhost:5173"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    import jwt
    from core.security import SECRET_KEY, ALGORITHM
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid auth credentials")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid auth credentials")
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    email_norm = (user.email or "").strip().lower() or None
    if email_norm:
        db_email = db.query(User).filter(func.lower(User.email) == email_norm).first()
        if db_email:
            raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, email=email_norm, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/profile", response_model=UserResponse)
def update_profile(profile_data: ProfileUpdateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if profile_data.khoi_thi is not None:
        current_user.khoi_thi = profile_data.khoi_thi.upper()
    if profile_data.diem_du_kien is not None:
        current_user.diem_du_kien = profile_data.diem_du_kien
    
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/history", response_model=List[ChatHistoryResponse])
def get_user_chat_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.created_at.desc()).all()
    history = []
    for session in sessions:
        history.append({
            "session_id": session.id,
            "messages": session.messages
        })
    return history

@router.post("/forgot-password")
def forgot_password(
    body: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    if not is_smtp_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                "Hệ thống chưa cấu hình gửi email. "
                "Quản trị viên cần đặt biến môi trường MAIL_USERNAME và MAIL_PASSWORD (SMTP)."
            ),
        )

    email_norm = (body.email or "").strip().lower()
    if not email_norm:
        return {
            "message": "Nếu email tồn tại trong hệ thống, bạn sẽ nhận được một đường link đặt lại mật khẩu."
        }

    user = db.query(User).filter(func.lower(User.email) == email_norm).first()
    if not user:
        return {
            "message": "Nếu email tồn tại trong hệ thống, bạn sẽ nhận được một đường link đặt lại mật khẩu."
        }

    if not user.email:
        return {
            "message": "Nếu email tồn tại trong hệ thống, bạn sẽ nhận được một đường link đặt lại mật khẩu."
        }

    reset_token = secrets.token_urlsafe(32)
    user.reset_token = reset_token
    user.reset_token_expire = datetime.utcnow() + timedelta(hours=1)
    db.commit()

    base = _resolve_frontend_base(request)
    reset_link = f"{base}/?reset_token={reset_token}"

    try:
        send_reset_email(user.email, reset_link)
    except Exception:
        user.reset_token = None
        user.reset_token_expire = None
        db.commit()
        logger.exception("Gửi email đặt lại mật khẩu thất bại; đã hủy token.")
        raise HTTPException(
            status_code=500,
            detail=(
                "Lỗi khi gửi email. Trên Hugging Face hãy dùng Resend (RESEND_API_KEY); "
                "SMTP Gmail thường không hoạt động trong Space."
            ),
        )

    return {
        "message": "Nếu email tồn tại trong hệ thống, bạn sẽ nhận được một đường link đặt lại mật khẩu."
    }

@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token == request.token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Token không hợp lệ hoặc đã hết hạn.")
        
    if user.reset_token_expire is None or user.reset_token_expire < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token không hợp lệ hoặc đã hết hạn.")
        
    user.hashed_password = get_password_hash(request.new_password)
    user.reset_token = None
    user.reset_token_expire = None
    db.commit()
    
    return {"message": "Đặt lại mật khẩu thành công. Vui lòng đăng nhập bằng mật khẩu mới."}


# === Ngành quan tâm (Favorites) ===
@router.get("/favorites", response_model=List[FavoriteMajorResponse])
def get_favorites(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Lấy danh sách ngành đã lưu của user."""
    rows = db.query(UserFavoriteMajor).filter(UserFavoriteMajor.user_id == current_user.id).order_by(UserFavoriteMajor.created_at.desc()).all()
    return rows


@router.post("/favorites", response_model=FavoriteMajorResponse)
def add_favorite(body: FavoriteMajorAdd, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Thêm ngành vào danh sách quan tâm."""
    existing = db.query(UserFavoriteMajor).filter(
        UserFavoriteMajor.user_id == current_user.id,
        UserFavoriteMajor.ma_nganh == body.ma_nganh.strip()
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ngành này đã có trong danh sách quan tâm.")
    fav = UserFavoriteMajor(user_id=current_user.id, ma_nganh=body.ma_nganh.strip(), ten_nganh=body.ten_nganh.strip() or None)
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return fav


@router.delete("/favorites/{ma_nganh}")
def remove_favorite(ma_nganh: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Xóa ngành khỏi danh sách quan tâm."""
    row = db.query(UserFavoriteMajor).filter(
        UserFavoriteMajor.user_id == current_user.id,
        UserFavoriteMajor.ma_nganh == ma_nganh
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Không tìm thấy ngành trong danh sách quan tâm.")
    db.delete(row)
    db.commit()
    return {"message": "Đã xóa khỏi danh sách quan tâm."}
