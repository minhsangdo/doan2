"""
LLM Client to interact with Google Gemini for the Chatbot Engine
"""
import os
import logging
from typing import List, Dict, Any, Tuple
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY") # Still using this var name as configured
        
        if self.api_key:
            logger.info(f"Configuring Gemini with API key: {self.api_key[:3]}...{self.api_key[-3:]}")
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')
        else:
            self.model = None

        self.base_system_prompt = """Bạn là Chatbot Tư vấn Tuyển sinh Đại học Nam Cần Thơ (DNC) hỗ trợ thí sinh nhập học năm 2025. 
Nhiệm vụ của bạn là đọc Câu hỏi và Ngữ cảnh được cung cấp để trả lời thí sinh một cách chính xác, thân thiện, và chi tiết nhất.

Quy tắc quan trọng:
1. TRẢ LỜI CHI TIẾT, ĐẦY ĐỦ THÔNG TIN, CHUYÊN NGHIỆP VÀ RÕ RÀNG. Có thể liệt kê đầy đủ các ý nếu câu hỏi yêu cầu (như danh sách ngành, danh sách tổ hợp, thông tin điểm). KHÔNG LẶP LẠI TOÀN BỘ CÂU HỎI. 
2. Hãy chỉ sử dụng dữ liệu được cung cấp trong phần CONTEXT để trả lời. TUYỆT ĐỐI KHÔNG SUY ĐOÁN. 
3. Nếu không tìm thấy thông tin từ hệ thống, hãy phản hồi: "Hiện tại hệ thống chưa tìm thấy thông tin phù hợp cho câu hỏi của bạn. Vui lòng liên hệ trực tiếp ban tư vấn tuyển sinh DNC." 
4. Văn phong: Xưng hô "mình/bạn" hoặc "Chatbot/thí sinh", vui vẻ, thân thiện.
5. Nếu câu hỏi yêu cầu so sánh, hãy dùng bảng (Markdown).

--- DƯỚI ĐÂY LÀ NGỮ CẢNH ĐƯỢC CUNG CẤP CHO BẠN ---
[CONTEXT]
{context}
[/CONTEXT]
"""

    def generate_response(self, question: str, context: str, history: List[Dict] = None) -> Tuple[str, List[str]]:
        if not self.model:
            logger.error("API Key not found!")
            return ("Lỗi cấu hình API. Chatbot chưa sẵn sàng.", [])

        prompt = self.base_system_prompt.replace("{context}", context)
        
        # Format history if any
        full_prompt = prompt + "\n\nCÂU HỎI CỦA NGƯỜI DÙNG: " + question

        try:
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=2500
                )
            )
            answer = response.text.strip()
            
            suggestions = self._extract_suggestions(answer)
            clean_answer = self._clean_answer(answer)
            
            if not suggestions:
                suggestions = self.generate_suggested_questions(question, answer)

            return clean_answer, suggestions
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            if "API_KEY_INVALID" in str(e) or "API key not valid" in str(e):
                return ("Lỗi cấu hình. API Key không hợp lệ. Vui lòng cập nhật API_KEY mới trong file .env.", [])
            return ("Xin lỗi, hệ thống bị gián đoạn. Không thể sinh câu trả lời lúc này.", [])

    def generate_suggested_questions(self, user_q: str, bot_a: str) -> List[str]:
        if not self.model:
            return []
            
        sys_msg = """Bạn là trợ lý ảo tuyển sinh. 
Dựa vào câu hỏi người dùng vừa hỏi và câu trả lời của chatbot, 
hãy gợi ý chính xác 3 câu hỏi tiếp theo ngắn gọn (dưới 15 chữ).
Định dạng đầu ra CHỈ LÀ CÁC DÒNG CÓ ĐÁNH SỐ:
1. câu hỏi 1
2. câu hỏi 2
3. câu hỏi 3"""

        try:
            prompt = sys_msg + f"\n\nHỏi: {user_q}\nĐáp: {bot_a[-200:]}"
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(temperature=0.6, max_output_tokens=100)
            )
            raw = response.text.strip()
            suggs = []
            for line in raw.split("\n"):
                if line.strip() and (line[0].isdigit() or line.startswith("-")):
                    suggs.append(line.lstrip("1234567890.- ").strip())
                    
            return suggs[:3]
        except:
            return []

    def _extract_suggestions(self, answer: str) -> List[str]:
        suggs = []
        lines = answer.split("\n")
        potential = lines[-5:]
        for line in potential:
            line = line.strip()
            if not line:
                continue
            if line.lower().startswith("gợi ý:") or line.lower().startswith("bạn có thể hỏi:"):
                continue
            if "- " in line[:4] or (line[0].isdigit() and ". " in line[:4]):
                if "?" in line:
                    suggs.append(line.lstrip("1234567890.-* ").strip())
        return suggs

    def _clean_answer(self, answer: str) -> str:
        lower_ans = answer.lower()
        idx = lower_ans.rfind("gợi ý câu hỏi")
        if idx == -1: idx = lower_ans.rfind("các câu hỏi bạn có thể quan tâm")
        if idx == -1: idx = lower_ans.rfind("bạn có thể hỏi tiếp")
        
        if idx != -1 and len(answer) - idx < 200:
            return answer[:idx].strip()
        return answer

_llm_client = None
def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
