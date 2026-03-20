"""
Admin endpoints for managing the Knowledge Graph.
"""
from fastapi import APIRouter, HTTPException
import logging
import os

from models.schemas import AdminResponse, KGStats, RebuildKGRequest, MajorUpdateRequest
from core.neo4j_client import get_neo4j_client
from sqlalchemy.orm import Session
from fastapi import Depends
from core.database import get_db
from models.database_models import User, ChatSession, ChatMessage
from api.routes.auth import get_current_user
from core.kg_bootstrap import resolved_kg_data_dir

logger = logging.getLogger(__name__)

def check_admin(current_user: User = Depends(get_current_user)):
    # For demo purposes, we consider any user with username matching 'admin' as admin
    if current_user.username.lower() != 'admin':
        raise HTTPException(status_code=403, detail="Không có quyền truy cập (yêu cầu Admin)")
    return current_user

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/stats", response_model=KGStats)
async def get_stats(_: User = Depends(check_admin)):
    """Lấy thống kê của Neo4j Knowledge Graph."""
    try:
        db = get_neo4j_client()
        stats = db.get_kg_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail="Không thể kết nối đến Neo4j")

@router.post("/rebuild", response_model=AdminResponse)
async def rebuild_graph(req: RebuildKGRequest, _: User = Depends(check_admin)):
    """Rebuild KG: bắt buộc confirm=True; mặc định full_ingest từ JSON (GraphBuilder)."""
    if not req.confirm:
        return {
            "success": False,
            "message": "Chưa xác nhận thao tác. Gửi confirm=true (theo use case xác nhận rebuild).",
        }

    try:
        if req.full_ingest:
            data_dir = resolved_kg_data_dir()
            if not os.path.isdir(data_dir):
                raise HTTPException(
                    status_code=400,
                    detail=f"Không tìm thấy thư mục dữ liệu JSON: {data_dir}",
                )
            from knowledge.graph_builder import GraphBuilder

            builder = GraphBuilder(data_dir)
            builder.rebuild_all()
            return {
                "success": True,
                "message": f"Đã rebuild Knowledge Graph đầy đủ từ {data_dir}.",
            }

        db = get_neo4j_client()
        db.clear_all()
        db.create_constraints()
        return {
            "success": True,
            "message": "Đã xóa graph và tạo lại constraints (không nạp JSON). Chọn full_ingest=true để import lại.",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rebuilding graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/popular-majors")
async def get_popular_majors(_: User = Depends(check_admin)):
    """Lấy danh sách các ngành được hỏi nhiều nhất."""
    try:
        db = get_neo4j_client()
        return db.get_popular_majors()
    except Exception as e:
        logger.error(f"Error fetching popular majors: {e}")
        raise HTTPException(status_code=500, detail="Lỗi thống kê")

@router.get("/chat-history")
def get_all_chat_history(
    db: Session = Depends(get_db),
    _: User = Depends(check_admin),
):
    """Lấy toàn bộ lịch sử chat của mọi người dùng."""
    try:
        users = db.query(User).all()
        res = []
        for u in users:
            sessions = db.query(ChatSession).filter(ChatSession.user_id == u.id).all()
            session_data = []
            for s in sessions:
                msgs = db.query(ChatMessage).filter(ChatMessage.session_id == s.id).order_by(ChatMessage.timestamp).all()
                if not msgs: continue
                session_data.append({
                    "session_id": s.id,
                    "created_at": str(s.created_at),
                    "messages": [{"role": m.role, "content": m.content, "time": str(m.timestamp)} for m in msgs]
                })
            # Only append users who have chat sessions
            if session_data:
                res.append({"user_id": u.id, "username": u.username, "sessions": session_data})
        return res
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/majors")
def get_all_majors(_: User = Depends(check_admin)):
    """Lấy danh sách tất cả các ngành và thông tin điểm chuẩn."""
    try:
        db = get_neo4j_client()
        return db.get_all_nganh()
    except Exception as e:
        logger.error(f"Error fetching all majors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/majors/{ma_nganh}")
def update_major(
    ma_nganh: str,
    req: MajorUpdateRequest,
    _: User = Depends(check_admin),
):
    """Cập nhật thông tin ngành và điểm chuẩn trực tiếp."""
    try:
        db = get_neo4j_client()
        data = req.dict()
        data["ma_nganh"] = ma_nganh
        db.update_nganh_and_score(data)
        return {"success": True, "message": "Cập nhật ngành thành công!"}
    except Exception as e:
        logger.error(f"Error updating major {ma_nganh}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
