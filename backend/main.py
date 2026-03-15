"""
FastAPI application entry point for DNC Chatbot Backend.
"""
import logging
import os
from fastapi import FastAPI
from dotenv import load_dotenv

# Import routers
from api.routes import chat, admin, auth
from api.middleware import setup_middlewares
from core.neo4j_client import get_neo4j_client
from core.database import engine, Base
import models.database_models

# Create SQLite tables
Base.metadata.create_all(bind=engine)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("app")
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

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

@app.on_event("startup")
async def startup_event():
    """Kiểm tra kết nối lúc khởi động"""
    logger.info("Khởi động hệ thống DNC Chatbot Backend...")
    db = get_neo4j_client()
    if db.verify_connectivity():
        logger.info("✅ Kết nối Neo4j thành công!")
    else:
        logger.warning("❌ Không thể kết nối Neo4j. Kiểm tra lại thông tin môi trường!")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Đang tắt hệ thống...")
    db = get_neo4j_client()
    db.close()

@app.get("/", tags=["Health"])
async def root():
    return {"message": "DNC Chatbot Backend is running!"}

@app.get("/api/health", tags=["Health"])
async def check_health():
    """Kiểm tra sức khỏe HT"""
    db = get_neo4j_client()
    status = "OK" if db.verify_connectivity() else "ERROR"
    return {"status": status, "neo4j": status}

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True)
