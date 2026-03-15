"""
Intent classifier using Gemini model
"""
import os
import logging
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class IntentClassifier:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')
        else:
            self.model = None

        self.system_prompt = """
Bạn là một hệ thống phân loại câu hỏi tư vấn tuyển sinh cho trường Đại học Nam Cần Thơ (DNC).
Nhiệm vụ của bạn là đọc câu hỏi của người dùng và phân loại vào MỘT trong các nhãn sau. CHỈ TRẢ VỀ ĐÚNG TÊN NHÃN.
Các nhãn:
1. "nganh_hoc": Hỏi về thông tin của một ngành, các môn học, tổ hợp môn xét tuyển của ngành, mã ngành học, nhóm ngành...
   Ví dụ: "Trường mình có ngành Y không?", "Công nghệ thông tin học khối nào?"
2. "diem_chuan": Hỏi về điểm chuẩn, điểm trúng tuyển của một ngành, điểm học bạ, điểm THPT, hoặc tư vấn với số điểm hiện có.
   Ví dụ: "Điểm chuẩn ngành Dược năm nay là bao nhiêu?", "Em được 24 điểm thì đậu Y không?"
3. "phuong_thuc": Hỏi về các phương thức xét tuyển, cách thức tính điểm, xét tuyển đánh giá năng lực, quy đổi điểm, điều kiện vào trường.
   Ví dụ: "Trường có xét bằng đánh giá năng lực không?", "Phương thức V-SAT là gì?"
4. "nhap_hoc": Hỏi về thủ tục nộp hồ sơ, giấy tờ cần chuẩn bị, thời gian nộp hồ sơ, kinh phí làm hồ sơ.
   Ví dụ: "Bao giờ hết hạn xác nhận nhập học?", "Nhập học hồ sơ cần gì?"
5. "so_sanh": Yêu cầu so sánh về hai hoặc nhiều ngành học, chuyên ngành với nhau về điểm chuẩn, tổ hợp môn, tính chất ngành.
   Ví dụ: "So sánh ngành CNTT và KHKMT", "Ngành dược và nha khoa khác nhau như thế nào?"
6. "tu_van_ca_nhan": Hỏi hệ thống tư vấn ngành học nào phù hợp với bản thân dựa trên điểm số hoặc khối thi cá nhân (ví dụ: "dựa vào hồ sơ của tôi", "ngành nào phù hợp với em", "em được 22 điểm khối A00 thì học ngành gì").
7. "khac": Hỏi về những việc không liên quan đến tuyển sinh, hoặc các thông tin chung chung, chào hỏi mở đầu.
   Ví dụ: "Học phí ra sao?", "Xin chào", "Ký túc xá thế nào?"
   
Mục tiêu của bạn là CHỈ TRẢ VỀ CHÍNH XÁC NHÃN TƯƠNG ỨNG mà không giải thích hay thừa chữ.
Ví dụ: người dùng nói "Em có điểm toán lý hóa là 20 điểm thì thi khối CNTT được ko", bạn trả về: "diem_chuan".
Ví dụ 2: người dùng nói "So sánh Dược và Điều dưỡng", bạn trả về: "so_sanh".
Ví dụ 3: người dùng nói "Dựa vào hồ sơ của em, em phù hợp ngành nào?", bạn trả về: "tu_van_ca_nhan".
"""

    def classify(self, message: str) -> str:
        """Classify the user intent into one of the 5 categories."""
        if not self.model:
            logger.warning("API key not detected. Falling back to simple keyword matching.")
            return self._heuristic_fallback(message)

        try:
            response = self.model.generate_content(
                self.system_prompt + "\n\nCÂU HỎI:\n" + message,
                generation_config=genai.types.GenerationConfig(temperature=0.0)
            )
            
            intent = response.text.strip().lower()
            
            # Verify valid intent
            valid_intents = ["nganh_hoc", "diem_chuan", "phuong_thuc", "nhap_hoc", "so_sanh", "tu_van_ca_nhan", "khac"]
            
            for valid in valid_intents:
                if valid in intent:
                    return valid
                    
            return "khac"
            
        except Exception as e:
            logger.error(f"Error during intent classification via LLM: {e}")
            return self._heuristic_fallback(message)

    def _heuristic_fallback(self, message: str) -> str:
        msg = message.lower()
        if any(w in msg for w in ["điểm chuẩn", "đậu không", "bao nhiêu điểm", "điểm thi", "điểm học bạ"]):
            return "diem_chuan"
        if any(w in msg for w in ["ngành", "tổ hợp", "học môn", "khối nào"]):
            return "nganh_hoc"
        if any(w in msg for w in ["phương thức", "cách xét tuyển", "v-sat", "đánh giá năng lực", "đgnl"]):
            return "phuong_thuc"
        if any(w in msg for w in ["nhập học", "hồ sơ", "giấy tờ", "ngày nào", "hạn"]):
            return "nhap_hoc"
        if any(w in msg for w in ["so sánh", "khác nhau", "khác biệt", "nên học ngành nào"]):
            return "so_sanh"
        if any(w in msg for w in ["phù hợp", "hồ sơ của tôi", "hồ sơ của em", "tư vấn cho em"]):
            return "tu_van_ca_nhan"
        return "khac"

_classifier = None
def get_intent_classifier() -> IntentClassifier:
    global _classifier
    if _classifier is None:
        _classifier = IntentClassifier()
    return _classifier
