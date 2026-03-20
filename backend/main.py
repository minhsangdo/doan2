"""
FastAPI application entry point for DNC Chatbot Backend.
"""
import asyncio
import logging
import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Import routers
from api.routes import chat, admin, auth
from api.middleware import setup_middlewares
from core.neo4j_client import get_neo4j_client
from core.kg_bootstrap import background_seed_neo4j_if_empty
from core.database import engine, Base, SessionLocal
import models.database_models
from models.database_models import User
from core.security import get_password_hash

# Create SQLite tables
Base.metadata.create_all(bind=engine)


def _ensure_default_admin_if_missing() -> None:
    """
    Trên Hugging Face / Docker, SQLite thường mới tinh → chưa có admin.
    Chạy tay: python create_admin.py. Ở đây tự tạo một lần nếu chưa có user 'admin'.
    Tắt: DISABLE_DEFAULT_ADMIN=1 | Đổi mật khẩu lần đầu: ADMIN_INITIAL_PASSWORD
    """
    if os.environ.get("DISABLE_DEFAULT_ADMIN", "").strip().lower() in ("1", "true", "yes"):
        return
    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == "admin").first():
            return
        pwd = os.environ.get("ADMIN_INITIAL_PASSWORD", "admin123").strip() or "admin123"
        admin_user = User(
            username="admin",
            email="admin@dnc.edu.vn",
            hashed_password=get_password_hash(pwd),
        )
        db.add(admin_user)
        db.commit()
        logger.info("Đã tạo user admin mặc định (DB trống). Đăng nhập: admin / (xem ADMIN_INITIAL_PASSWORD hoặc admin123)")
    except Exception:
        logger.exception("Không thể tạo admin mặc định")
        db.rollback()
    finally:
        db.close()


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("app")
_backend_dir = os.path.dirname(os.path.abspath(__file__))
# Ưu tiên .env cạnh backend, rồi thư mục cha (repo gốc); trên Docker/HF dùng biến môi trường
load_dotenv(os.path.join(_backend_dir, ".env"))
load_dotenv(os.path.join(os.path.dirname(_backend_dir), ".env"))

app = FastAPI(
    title="DNC Admission Chatbot API",
    description="API cho hệ thống Chatbot Tư vấn Tuyển sinh Đại học Nam Cần Thơ ứng dụng Graph RAG",
    version="1.0.0"
)

# Thêm Middleware CORS
setup_middlewares(app)

# Đăng ký routes
app.include_router(chat.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(auth.router, prefix="/api")

# --- Phục vụ React build (Docker / Hugging Face Space): thư mục static do Dockerfile copy ---
_STATIC_DIR = os.path.join(_backend_dir, "static")
if os.path.isdir(_STATIC_DIR) and os.path.isfile(os.path.join(_STATIC_DIR, "index.html")):
    _assets = os.path.join(_STATIC_DIR, "assets")
    if os.path.isdir(_assets):
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")

    @app.get("/", tags=["Health"])
    async def root():
        return FileResponse(os.path.join(_STATIC_DIR, "index.html"))
else:

    @app.get("/", tags=["Health"])
    async def root():
        return {"message": "DNC Chatbot Backend is running!"}

@app.on_event("startup")
async def startup_event():
    """Kiểm tra kết nối lúc khởi động"""
    _ensure_default_admin_if_missing()
    logger.info("Khởi động hệ thống DNC Chatbot Backend...")
    db = get_neo4j_client()
    if db.verify_connectivity():
        logger.info("✅ Kết nối Neo4j thành công!")
        # Nạp KG từ data/processed nếu DB trống (HF Space — không cần bấm Rebuild).
        # Tắt: KG_AUTO_SEED=false. Chạy nền để container vẫn "healthy" trong lúc embedding.
        try:
            loop = asyncio.get_running_loop()
            loop.run_in_executor(None, background_seed_neo4j_if_empty)
        except Exception:
            logger.exception("Không thể khởi chạy nền nạp KG")
    else:
        logger.warning("❌ Không thể kết nối Neo4j. Kiểm tra lại thông tin môi trường!")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Đang tắt hệ thống...")
    db = get_neo4j_client()
    db.close()

@app.get("/api/health", tags=["Health"])
async def check_health():
    """Kiểm tra sức khỏe HT"""
    db = get_neo4j_client()
    ok = db.verify_connectivity()
    status = "OK" if ok else "ERROR"
    out = {"status": status, "neo4j": status}
    if ok:
        try:
            r = db.run_query("MATCH (n:Nganh) RETURN count(n) AS c")
            out["nganh_count"] = int(r[0]["c"]) if r else 0
        except Exception:
            out["nganh_count"] = None
    return out

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True)
