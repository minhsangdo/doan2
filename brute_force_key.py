import google.generativeai as genai
import itertools

# Các cụm ký tự nghi ngờ nhầm lẫn
# AIzaSy BUoe OvN4 LCB0 _ vcz7 Wqv4w JhQib yw8 Mkl

parts = [
    ["AIzaSy", "AlzaSy"], # I hoa vs l thường
    ["BUoe", "BU0e"],     # o vs 0
    ["OvN4", "0vN4"],     # O vs 0
    ["LCB0", "LCBO"],     # 0 vs O
    ["_"],
    ["vcz7", "vczT"],     # 7 vs T
    ["Wqv4w", "Wqu4w", "WqvAw"], # v vs u, 4 vs A
    ["JhQib"],
    ["yw8", "ywB"],       # 8 vs B
    ["Mkl", "MkI", "Mk1"] # l vs I vs 1
]

def check_key(key):
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        model.generate_content("test", generation_config={"max_output_tokens": 1})
        return True
    except Exception as e:
        if "API key not valid" in str(e):
            return False
        # Nếu lỗi khác (ví dụ quota) thì có thể key đúng nhưng bị giới hạn
        print(f"Key {key[:10]}... có lỗi khác: {e}")
        return False

# Chỉ thử các tổ hợp chính
possible_keys = [
    "AIzaSyBUoeOvN4LCB0_vcz7Wqv4wJhQibyw8Mkl", # Gốc
    "AIzaSyBUoeOvN4LCB0_vcz7Wqv4wJhQibywBMkl", # 8 -> B
    "AIzaSyBUoe0vN4LCB0_vcz7Wqv4wJhQibyw8Mkl", # O -> 0
    "AIzaSyBU0eOvN4LCB0_vcz7Wqv4wJhQibyw8Mkl", # o -> 0
    "AIzaSyBUoeOvN4LCBO_vcz7Wqv4wJhQibyw8Mkl", # 0 -> O
    "AIzaSyBUoeOvN4LCB0_vcz7Wqv4wJhQibyw8Mk1", # l -> 1
    "AIzaSyBUoeOvN4LCB0_vcz7Wqv4wJhQibyw8MkI", # l -> I
]

print("Đang kiểm tra các tổ hợp key...")
for k in possible_keys:
    if check_key(k):
        print(f"--- THÀNH CÔNG! Key đúng là: {k} ---")
        exit(0)

print("Không tìm thấy key trong các tổ hợp cơ bản. Đang thử rộng hơn...")
# Thử thêm một vài cái nữa
for k in ["AIzaSyBUoeOvN4LCB0_vcz7Wqv4wJhQibyw8Mkl", "AIzaSyBUoeOvN4LCB0_vcz7Wqv4wJhQibywBMkl"]:
    # Thử thay đổi I/l ở đầu
    alt_k = "AlzaSy" + k[6:]
    if check_key(alt_k):
        print(f"--- THÀNH CÔNG! Key đúng là: {alt_k} ---")
        exit(0)

print("Thất bại. Vui lòng copy và dán trực tiếp text.")
