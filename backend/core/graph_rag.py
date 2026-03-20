"""
The Core Engine combining: Intent Classification, Vector Search, Graph Traversal, and Generation.
"""
import logging
import time
from typing import Dict, Any, List

from core.neo4j_client import get_neo4j_client
from core.embeddings import get_embedding_service
from core.intent_classifier import get_intent_classifier
from core.llm_client import get_llm_client
from models.schemas import ChatResponse, Source, SuggestedQuestion

logger = logging.getLogger(__name__)

class GraphRAGEngine:
    def __init__(self):
        self.db = get_neo4j_client()
        self.embedder = get_embedding_service()
        self.classifier = get_intent_classifier()
        self.llm = get_llm_client()

    def process_query(self, query: str, session_id: str, user=None) -> ChatResponse:
        """Main pipeline for processing a user's question."""
        start_time = time.time()
        
        # 1. Classify Intent
        intent = self.classifier.classify(query)
        logger.info(f"Classified intent: {intent}")

        # 2. Get Query Embedding
        embedding = None
        if intent in ["nganh_hoc", "diem_chuan", "so_sanh", "tu_van_ca_nhan"]:
            try:
                embedding = self.embedder.get_embedding(query)
            except Exception as e:
                logger.error(f"Failed to get embedding: {e}")

        # 3. Retrieve Context from Knowledge Graph
        context_str, sources = self._retrieve_context(query, intent, embedding, user)
        
        # 4. Generate Response using LLM
        answer, suggestions = self.llm.generate_response(query, context_str)
        
        # 5. Format Output
        process_time = time.time() - start_time
        
        sugg_objs = [SuggestedQuestion(text=s) for s in suggestions]
        
        return ChatResponse(
            answer=answer,
            sources=sources,
            suggested_questions=sugg_objs,
            session_id=session_id,
            processing_time=process_time
        )

    def _retrieve_context(self, query: str, intent: str, embedding: List[float] = None, user=None) -> tuple[str, List[Source]]:
        """Determine what logic to run based on the intent."""
        context_parts = []
        sources = []
        
        # Personal Advice Logic
        if intent == "tu_van_ca_nhan":
            if not user:
                return ("(Hệ thống: Hãy yêu cầu người dùng đăng nhập để sử dụng tính năng tư vấn cá nhân hóa.)", [])
            if not user.diem_du_kien:
                return ("(Hệ thống: Hãy yêu cầu người dùng cập nhật 'Điểm dự kiến' và 'Khối thi' trong phần Hồ sơ để hệ thống tư vấn chính xác.)", [])
            
            advised_majors = self.db.search_nganh_by_profile(user.diem_du_kien, user.khoi_thi)
            if not advised_majors:
                context_parts.append(f"(Hệ thống: Không tìm thấy ngành nào phù hợp với điểm số {user.diem_du_kien} và khối {user.khoi_thi or 'bất kỳ'}. Hãy khuyên người dùng cố gắng thêm hoặc xem xét các phương thức khác như xét học bạ.)")
            else:
                context_parts.append(f"--- GỢI Ý NGÀNH HỌC CHO BẠN ({user.username}) ---\n"
                                     f"Điểm dự kiến: {user.diem_du_kien} | Khối thi: {user.khoi_thi or 'Không rõ'}\n")
                for n in advised_majors:
                    context_parts.append(f"- {n['ten']} (Mã: {n['ma_nganh']}) - Điểm chuẩn: {n['diem_thpt']}\n  Mô tả: {n.get('mo_ta', '')}")
                    sources.append(Source(node_type="Nganh", name=n['ten']))
                
                context_parts.append("(Hệ thống: Dựa vào thông tin GỢI Ý NGÀNH HỌC CHO BẠN ở trên, hãy trả lời thật tự nhiên, động viên người dùng và giới thiệu các ngành học phù hợp với họ. Chỉ lấy thông tin từ danh sách gợi ý.)")
            return "\n".join(context_parts), sources

        # Fallback or general questions logic
        if intent == "khac":
            return (
                "(Hệ thống: Hãy gợi mở về việc DNC là một môi trường tuyệt vời, hoặc yêu cầu hỏi rõ hơn.)", 
                []
            )

        if intent == "nhap_hoc":
            return (
                "Thông tin nhập học đợt 1 năm 2025: Thí sinh xác nhận trực tuyến trên Hệ thống của Bộ GD&ĐT chậm nhất 17h00 ngày 30/08/2025.", 
                [Source(node_type="QuyDinh", name="Nhập học đợt 1")]
            )

        # Graph RAG retrieval for Majors and Scores
        if embedding:
            is_global_query = any(k in query.lower() for k in ["tất cả", "danh sách", "các ngành", "những ngành"])
            
            if is_global_query:
                try:
                    all_nganh = self.db.run_query("MATCH (n:Nganh) RETURN n.ma_nganh as ma, n.ten as ten ORDER BY n.ten")
                    nganh_list = [f"- {n['ten']} (Mã ngành: {n['ma']})" for n in all_nganh]
                    if nganh_list:
                        part = f"--- DANH SÁCH {len(nganh_list)} NGÀNH ĐÀO TẠO TẠI DNC 2025 ---\n" + "\n".join(nganh_list) + "\n-----------------------"
                        context_parts.append(part)
                        sources.append(Source(node_type="Nganh", name=f"Danh sách {len(nganh_list)} ngành của DNC"))
                except Exception as e:
                    logger.error(f"Error getting all majors: {e}")

            # Lấy chi tiết top ngành phù hợp nhất
            is_comparison = intent == "so_sanh"
            top_k = 6 if is_comparison else 4
            top_nodes = self.db.vector_search(embedding, top_k=top_k)
            
            ma_nganh_list = []
            for node in top_nodes:
                ma_nganh = node["ma_nganh"]
                ma_nganh_list.append(ma_nganh)
                sources.append(Source(node_type="Nganh", name=node["ten"], score=node.get("score")))
                
                # Expand to 1-2 hops to get full info
                full_info = self.db.get_nganh_context(ma_nganh)
                
                # Build context text
                part = f"""--- THÔNG TIN NGÀNH ---
- Mã ngành: {full_info.get("ma_nganh")}
- Tên ngành: {full_info.get("ten_nganh")}
- Nhóm: {full_info.get("nhom_nganh")}
- Mô tả: {full_info.get("mo_ta", "Đào tạo cử nhân kỹ sư chất lượng cao")}
- Điểm chuẩn 2025:
  + Thi THPT: {full_info.get("diem_thpt", "Chưa có điểm")}
  + Học bạ (lớp 12): {full_info.get("diem_hocba", "Chưa có")}
  + Thi ĐGNL (ĐHQG TPHCM): {full_info.get("diem_dgnl", "Không áp dụng")}
  + Thi V-SAT: {full_info.get("diem_vsat", "Không áp dụng")}
- Tổ hợp môn xét tuyển: {", ".join(full_info.get("tohop_mon", []))} ({", ".join(full_info.get("ten_tohop", []))})
-----------------------
"""
                context_parts.append(part)
                
            if ma_nganh_list:
                self.db.increment_search_count(ma_nganh_list)
                
            if is_comparison:
                compare_prompt = "(Hệ thống: Người dùng đang yêu cầu SO SÁNH các ngành học. Hãy tìm thông tin của các ngành được nhắc đến trong câu hỏi từ các 'THÔNG TIN NGÀNH' phía trên, lập MỘT BẢNG SO SÁNH (Markdown) tương quan. Các tiêu chí nên có gồm: Mã ngành, Tổ hợp xét tuyển, Điểm chuẩn các phương thức, và Tính chất/Mô tả ngành học. Dùng định dạng Bảng để người xem dễ hình dung. Sau bảng, hãy tóm tắt ngắn gọn sự khác biệt. TUYỆT ĐỐI KHÔNG BỊA CHẾ THÔNG TIN NGOÀI NGỮ CẢNH.)"
                context_parts.append(compare_prompt)

        # HocBong (scholarship) retrieval
        if intent == "hoc_bong":
            try:
                hoc_bong_list = self.db.get_all_hoc_bong()
                if hoc_bong_list:
                    hb_lines = []
                    for hb in hoc_bong_list:
                        hb_lines.append(f"[{hb.get('ma_hb')}] {hb.get('ten')}\n  Mô tả: {hb.get('mo_ta')}\n  Điều kiện: {hb.get('dieu_kien')}\n  Giá trị/Hỗ trợ: {hb.get('gia_tri')}\n  Đối tượng: {hb.get('doi_tuong')}")
                    part = "--- HỌC BỔNG VÀ CHÍNH SÁCH HỖ TRỢ SINH VIÊN DNC ---\n" + "\n\n".join(hb_lines) + "\n-----------------------"
                    context_parts.append(part)
                    sources.append(Source(node_type="HocBong", name="Học bổng DNC"))
                else:
                    context_parts.append("(Hệ thống: Hiện chưa có dữ liệu học bổng trong cơ sở. Hãy khuyên người dùng liên hệ Phòng Công tác Sinh viên hoặc website DNC để biết chính sách học bổng mới nhất.)")
            except Exception as e:
                logger.error(f"Error getting hoc_bong: {e}")
                context_parts.append("(Hệ thống: Tạm thời không truy xuất được thông tin học bổng. Hãy gợi ý người dùng xem trang chủ DNC hoặc liên hệ trực tiếp.)")

        # Phuong_thuc info retrieval
        if intent == "phuong_thuc" or "phương thức" in query.lower():
            # Simply get all method node descriptions
            methods_data = self.db.run_query("MATCH (p:PhuongThuc) RETURN p.ma_pt as ma, p.ten as ten, p.mo_ta as mo_ta ORDER BY p.ma_pt")
            pt_list = [f"[{m['ma']}] {m['ten']}: {m['mo_ta']}" for m in methods_data]
            
            part = f"""--- CÁC PHƯƠNG THỨC XÉT TUYỂN 2026 ---
{chr(10).join(pt_list)}
-----------------------
"""
            context_parts.append(part)
            sources.append(Source(node_type="PhuongThuc", name="9 Phương thức DNC"))

        return "\n".join(context_parts), sources

# Singleton instance
_engine = None

def get_graph_rag_engine() -> GraphRAGEngine:
    global _engine
    if _engine is None:
        _engine = GraphRAGEngine()
    return _engine
