"""
Đường dẫn JSON cho Knowledge Graph + tự nạp Neo4j khi DB trống (Hugging Face / Docker).
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

# Thư mục backend (…/backend)
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resolved_kg_data_dir() -> str:
    """
    Docker/HF: /app/data/processed.
    Dev: <repo>/data/processed.
    """
    env = os.environ.get("KG_DATA_DIR", "").strip()
    if env and os.path.isdir(env):
        return os.path.abspath(env)
    in_app = os.path.join(_BACKEND_DIR, "data", "processed")
    if os.path.isdir(in_app):
        return os.path.abspath(in_app)
    project_root = os.path.abspath(os.path.join(_BACKEND_DIR, ".."))
    return os.path.join(project_root, "data", "processed")


def background_seed_neo4j_if_empty() -> None:
    """
    Nếu Neo4j trống hoặc **thiếu ngành** (seed dở, còn vài node) → chạy GraphBuilder.

    Mặc định: coi là đủ dữ liệu khi có >= 40 node Nganh (DNC ~45 ngành).
    Tuỳ chỉnh: KG_MIN_NGANH_COMPLETE=45

    Tắt: KG_AUTO_SEED=0 | false | off
    """
    v = os.getenv("KG_AUTO_SEED", "true").strip().lower()
    if v in ("0", "false", "no", "off"):
        logger.info("KG_AUTO_SEED tắt — bỏ qua tự động nạp graph khi khởi động.")
        return

    try:
        min_complete = int(os.getenv("KG_MIN_NGANH_COMPLETE", "40").strip() or "40")

        from core.neo4j_client import get_neo4j_client

        db = get_neo4j_client()
        if not db.verify_connectivity():
            logger.warning("Neo4j không kết nối được — không tự nạp KG.")
            return
        r = db.run_query("MATCH (n:Nganh) RETURN count(n) AS c")
        cnt = int(r[0]["c"]) if r else 0
        if cnt >= min_complete:
            logger.info(
                "Neo4j đã có %s ngành (ngưỡng đủ: %s) — không tự nạp lại.",
                cnt,
                min_complete,
            )
            return
        if cnt > 0:
            logger.warning(
                "Neo4j chỉ có %s ngành (< %s) — có thể seed dở/lỗi. Sẽ rebuild đầy đủ từ JSON.",
                cnt,
                min_complete,
            )
        data_dir = resolved_kg_data_dir()
        if not os.path.isdir(data_dir):
            logger.warning("Không tìm thấy thư mục JSON: %s — không tự nạp KG.", data_dir)
            return
        logger.info(
            "Bắt đầu GraphBuilder từ %s (nền, có thể vài phút; cần OPENAI_API_KEY).",
            data_dir,
        )
        from knowledge.graph_builder import GraphBuilder

        GraphBuilder(data_dir).rebuild_all()
        logger.info("Tự động nạp Knowledge Graph xong.")
    except Exception:
        logger.exception(
            "Lỗi khi tự động nạp KG — kiểm tra Secrets/logs hoặc dùng Admin > Rebuild sau."
        )
