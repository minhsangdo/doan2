# 🎓 Hệ Thống Chatbot Tư Vấn Tuyển Sinh Đại Học Nam Cần Thơ (DNC) - 2025

Đồ án xây dựng một Chatbot thông minh hỗ trợ tư vấn tuyển sinh đại học cho Trường Đại học Nam Cần Thơ (DNC), ứng dụng công nghệ **Graph RAG (Retrieval-Augmented Generation) kết hợp với cơ sở dữ liệu đồ thị Neo4j** để truy xuất thông tin chính xác, minh bạch và có tính liên kết cao.

---

## 🏗️ Kiến trúc hệ thống

Hệ thống được thiết kế theo mô hình Client-Server kết hợp với Knowledge Graph và LLM:

| Thành phần | Công nghệ | Mô tả |
|------------|-----------|--------|
| **Frontend** | React.js + Vite + Tailwind CSS | Giao diện chat, markdown, xác thực, lịch sử, ngành quan tâm, phản hồi, nhập giọng nói, Text-to-Speech |
| **Backend** | FastAPI (Python 3.11) | API, JWT, Graph RAG, logic hỏi đáp |
| **Database (RDBMS)** | SQLite `chat_history.db` | Người dùng, phiên chat, tin nhắn, ngành quan tâm, phản hồi |
| **Graph DB** | Neo4j 5.x | Entities, Relationships, Embeddings cho Graph RAG |
| **AI** | OpenAI GPT-4o, Text-Embedding-3-Small, LangChain | Phân loại ý định, embedding, tổng hợp câu trả lời |

---

## 📊 Cơ sở dữ liệu (SQLite) – 5 bảng

Hệ thống sử dụng **5 bảng** trong file `chat_history.db`, liên kết với nhau như sau:

### Sơ đồ quan hệ

```
                         ┌─────────────┐
                         │   users     │
                         │  (id PK)   │
                         └──────┬─────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
          ▼                     ▼                     ▼
┌──────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│ chat_sessions    │  │ user_favorite_      │  │ message_feedbacks    │
│ user_id (FK)     │  │ majors (user_id FK) │  │ user_id (FK, null)  │
└────────┬─────────┘  └─────────────────────┘  │ message_id (FK)     │
         │ 1:N                                    └──────────┬──────────┘
         ▼                                                   │
┌──────────────────┐                                        │
│ chat_messages    │◄───────────────────────────────────────┘
│ session_id (FK)  │
└──────────────────┘
```

### Mô tả từng bảng

| # | Bảng | Khóa chính | Khóa ngoại | Mô tả |
|---|------|------------|------------|--------|
| 1 | **users** | id | — | Tài khoản: username, email, mật khẩu, khối thi, điểm dự kiến, reset password |
| 2 | **chat_sessions** | id (UUID) | user_id → users.id | Phiên chat (user_id có thể null cho khách) |
| 3 | **chat_messages** | id | session_id → chat_sessions.id | Tin nhắn user/bot trong từng phiên |
| 4 | **user_favorite_majors** | id | user_id → users.id | Ngành học người dùng đã lưu (ma_nganh, ten_nganh). UNIQUE(user_id, ma_nganh) |
| 5 | **message_feedbacks** | id | message_id → chat_messages.id, user_id → users.id | Đánh giá câu trả lời (rating: up/down). user_id nullable |

### Quan hệ tóm tắt

- **users** ↔ **chat_sessions**: 1 user có nhiều phiên (N : 1).
- **chat_sessions** ↔ **chat_messages**: 1 phiên có nhiều tin nhắn (1 : N).
- **users** ↔ **user_favorite_majors**: 1 user có nhiều ngành quan tâm (1 : N).
- **chat_messages** ↔ **message_feedbacks**: 1 tin nhắn có nhiều phản hồi (1 : N); **users** ↔ **message_feedbacks** (N : 1, user_id tùy chọn).

---

## 🧠 Sơ đồ tri thức (Knowledge Graph – Neo4j)

Mô hình đồ thị trong Neo4j (labels và quan hệ thực tế trong code):

### Node types (labels)

| Label | Mô tả | Số lượng (sau seed mẫu) |
|-------|--------|-------------------------|
| **Nganh** | Ngành đào tạo (ma_nganh, ten, nhom, mo_ta); có vector embedding | 45 |
| **DiemChuan** | Điểm chuẩn 2025 (THPT, học bạ, ĐGNL, V-SAT) theo từng ngành | 45 |
| **TohopMon** | Tổ hợp môn xét tuyển (ma_tohop, ten, cac_mon) | 41 |
| **PhuongThuc** | Phương thức xét tuyển (ma_pt, ten, mo_ta) | 9 |
| **NhomNganh** | Nhóm ngành (Y-Duoc, KT-CN, ...) | 10 |
| **HocBong** | Học bổng và chính sách hỗ trợ (ma_hb, ten, mo_ta, dieu_kien, gia_tri, doi_tuong) | 8 |

### Relationships

- `(Nganh)-[:HAS_SCORE]->(DiemChuan)`
- `(Nganh)-[:USES_COMBO]->(TohopMon)`
- `(Nganh)-[:BELONGS_TO]->(NhomNganh)`
- `(Nganh)-[:ACCEPTS_METHOD]->(PhuongThuc)`

Vector index: **Nganh.embedding** (1536 chiều, cosine) dùng cho similarity search khi tư vấn ngành/điểm chuẩn.

---

## 🔄 Luồng dữ liệu

### 1. Chuẩn bị dữ liệu (Offline)

1. Trích xuất dữ liệu từ PDF/DOCX → lưu JSON tại `data/processed/`.
2. Chạy **`python scripts/seed_neo4j.py`** (từ thư mục gốc): tạo nodes, relationships, embeddings và Vector Index trong Neo4j. Script đọc: `phuong_thuc.json`, `tohop_mon.json`, `nganh_hoc.json`, `diem_chuan.json`, `hoc_bong.json` (nếu có).

### 2. Hỏi đáp (Online)

1. User gửi câu hỏi → POST `/api/chat/`.
2. Backend: phân loại ý định (LLM) — gồm **hoc_bong** khi hỏi về học bổng.
3. Embedding câu hỏi (nếu cần), vector search + graph traversal trên Neo4j; với intent **hoc_bong** thì lấy toàn bộ node HocBong.
4. Xây dựng context (Graph RAG) → GPT-4o sinh câu trả lời + gợi ý câu hỏi.
5. Lưu tin nhắn vào SQLite, trả response (kèm `bot_message_id` cho phản hồi).

---

## 🛠️ Chức năng hệ thống

### 1. Quản lý người dùng & xác thực

- Đăng ký, đăng nhập (JWT).
- Quên mật khẩu: gửi link khôi phục qua email.
- Hồ sơ: cập nhật khối thi, điểm dự kiến (phục vụ gợi ý ngành).

### 2. Chat & tư vấn tuyển sinh

- Tư vấn **45 ngành đào tạo**, mã ngành, tổ hợp môn.
- Tra cứu **điểm chuẩn năm 2025** theo hình thức xét tuyển.
- **9 phương thức xét tuyển**, thủ tục nhập học.
- **Học bổng và chính sách hỗ trợ**: học bổng tân sinh viên (20 triệu, 40%, 30%), học bổng sinh viên chính quy (hoàn cảnh khó khăn, xuất sắc, tốt nghiệp xuất sắc, Hội khuyến học/doanh nghiệp), thông tin liên hệ Phòng QLSV & Tư vấn tuyển sinh.
- **Gợi ý câu hỏi** sau mỗi câu trả lời.
- **Nguồn tham chiếu (Sources)** hiển thị minh bạch từ Neo4j.

### 3. Quản lý trò chuyện

- Lưu nhiều **phiên chat** theo tài khoản; xem lại lịch sử.
- Tin nhắn lưu trong `chat_messages` theo `chat_sessions`.

### 4. Ngành quan tâm (Favorites)

- **Lưu ngành** (mã ngành, tên ngành) vào danh sách quan tâm (bảng `user_favorite_majors`).
- Xem danh sách, xóa ngành đã lưu (sidebar khi đăng nhập).
- API: GET/POST `/api/auth/favorites`, DELETE `/api/auth/favorites/{ma_nganh}`.

### 5. Phản hồi câu trả lời (Feedback)

- Nút **Hữu ích** / **Báo sai** dưới tin nhắn bot (bảng `message_feedbacks`).
- Gửi đánh giá kèm `message_id`; có thể gửi khi chưa đăng nhập (user_id nullable).
- API: POST `/api/chat/feedback` (body: `message_id`, `rating`: 'up' | 'down').

### 6. Trải nghiệm đa phương tiện

- **Nhập bằng giọng nói**: Web Speech API (Chrome/Edge, localhost hoặc HTTPS), xin quyền microphone.
- **Text-to-Speech**: Đọc nội dung câu trả lời (tiếng Việt).

### 7. Admin

- Thống kê Neo4j, rebuild graph, xem lịch sử chat, quản lý ngành (tùy cấu hình).

---

## 📁 Cấu trúc thư mục

```text
doan2_chatboxtuyensinh_DoMinhSang/
├── backend/                    # FastAPI
│   ├── api/                   # Routes: chat, auth, admin
│   ├── core/                  # Graph RAG, LLM, Neo4j, Security, DB
│   ├── knowledge/             # graph_builder (đọc JSON, tạo Neo4j)
│   ├── models/                # SQLAlchemy models, Pydantic schemas
│   ├── main.py                # Entrypoint
│   ├── migrate_db.py          # Migration SQLite (bảng + cột)
│   └── chat_history.db        # SQLite (5 bảng)
├── frontend/                   # React + Vite + Tailwind
│   ├── src/
│   │   ├── App.jsx            # Chat, auth, favorites, feedback, voice, TTS
│   │   └── AdminDashboard.jsx
│   └── public/
├── data/
│   ├── raw/                   # PDF/DOCX nguồn (diem chuan, tuyen sinh, hoc bong...)
│   └── processed/             # JSON: diem_chuan, nganh_hoc, tohop_mon, phuong_thuc, hoc_bong
├── docs/                       # Hướng dẫn (vd: thêm dữ liệu học bổng)
├── scripts/
│   └── seed_neo4j.py          # Seed toàn bộ graph từ data/processed/
├── README.md
└── docker-compose.yml         # Neo4j
```

---

## 📊 Dataset

Dữ liệu trích từ văn bản chính thức DNC:

| Nguồn | Nội dung | File JSON (trong `data/processed/`) |
|-------|----------|--------------------------------------|
| Thông báo điểm chuẩn 2025, Thông tin tuyển sinh 2025, Kế hoạch đồ án | Ngành, điểm chuẩn, tổ hợp môn, phương thức | `diem_chuan.json`, `nganh_hoc.json`, `tohop_mon.json`, `phuong_thuc.json` |
| **HỌC BỔNG ĐẠI HỌC NAM CẦN THƠ.pdf** | Học bổng tân sinh viên, sinh viên chính quy, liên hệ | `hoc_bong.json` |

- File PDF học bổng có thể đặt trong `data/raw/` (vd: `data/raw/HỌC BỔNG ĐẠI HỌC NAM CẦN THƠ.pdf`). Dữ liệu đã được trích và chuẩn hóa vào `hoc_bong.json` để seed Neo4j.
- Hướng dẫn **thêm/sửa dữ liệu học bổng**: xem `docs/HUONG_DAN_THEM_DU_LIEU_HOC_BONG.md`.

---

## 🚀 Cài đặt & Chạy

### Yêu cầu

- Docker, Docker Compose  
- Python 3.11+  
- Node.js v18+  
- OpenAI API Key  

### B1. Neo4j

```bash
docker-compose up -d neo4j
```

### B2. Backend và seed graph

```bash
cp .env.example .env
# Sửa .env: OPENAI_API_KEY, MAIL_* (nếu dùng quên mật khẩu)

cd backend
pip install -r requirements.txt
python migrate_db.py
```

Từ **thư mục gốc** project:

```bash
python scripts/seed_neo4j.py
```

Sau đó chạy backend:

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### B3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Truy cập: **http://localhost:5173/**

---

## 👤 Tech Credits

| | |
|---|---|
| **Sinh viên** | DoMinhSang |
| **Khách hàng** | Đại Học Nam Cần Thơ (DNC) |
| **Khoa** | Công Nghệ Thông Tin |
| **Năm** | 2024-2025 |

---

*Chatbot có thể mắc lỗi do AI. Vui lòng đối chiếu với Đề án tuyển sinh và văn bản học bổng chính thức của DNC.*
