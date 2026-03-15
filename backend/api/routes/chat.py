"""
API route for handling chat interactions.
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
import uuid
import logging

from models.schemas import ChatRequest, ChatResponse
from models.auth_schemas import FeedbackSubmit, FeedbackResponse
from core.graph_rag import get_graph_rag_engine
from core.database import get_db
from models.database_models import ChatSession, ChatMessage, User, MessageFeedback
from api.routes.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])

# Optional auth dependency
def get_optional_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    import jwt
    from core.security import SECRET_KEY, ALGORITHM
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username: return None
        return db.query(User).filter(User.username == username).first()
    except Exception:
        return None

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """
    Nhận câu hỏi từ thí sinh và trả về câu trả lời được sinh từ Graph RAG.
    """
    session_id = request.session_id or str(uuid.uuid4())
    logger.info(f"Received query: '{request.message}' [Session: {session_id}]")
    
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Câu hỏi không được để trống")

    try:
        engine = get_graph_rag_engine()
        response = engine.process_query(request.message, session_id, user=current_user)
        
        # Save to SQLite
        db_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not db_session:
            db_session = ChatSession(id=session_id)
            if current_user:
                db_session.user_id = current_user.id
            db.add(db_session)
            db.commit()
            
        user_msg = ChatMessage(session_id=session_id, role="user", content=request.message)
        bot_msg = ChatMessage(session_id=session_id, role="bot", content=response.answer)
        db.add_all([user_msg, bot_msg])
        db.commit()
        db.refresh(bot_msg)

        # Trả kèm bot_message_id để frontend gửi phản hồi (thích / báo sai)
        out = response.model_dump()
        out["bot_message_id"] = bot_msg.id
        return out
    except Exception as e:
        logger.error(f"Error processing chat: {e}")
        raise HTTPException(status_code=500, detail="Hệ thống đang bận, vui lòng thử lại sau.")


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(
    body: FeedbackSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Gửi đánh giá (hữu ích / báo sai) cho một câu trả lời của bot."""
    if body.rating not in ("up", "down"):
        raise HTTPException(status_code=400, detail="rating phải là 'up' hoặc 'down'.")
    msg = db.query(ChatMessage).filter(ChatMessage.id == body.message_id).first()
    if not msg or msg.role != "bot":
        raise HTTPException(status_code=404, detail="Không tìm thấy tin nhắn.")
    user_id = current_user.id if current_user else None
    fb = MessageFeedback(message_id=body.message_id, user_id=user_id, rating=body.rating, comment=body.comment)
    db.add(fb)
    db.commit()
    return FeedbackResponse(message="Cảm ơn bạn đã phản hồi!")
