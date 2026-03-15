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
│ chat_messages     │◄───────────────────────────────────────┘
│ session_id (FK)   │
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

Mô hình đồ thị trong Neo4j (không phải bảng SQL):

- **Nodes**: `Program` (Ngành học), `AdmissionMethod` (Phương thức xét tuyển), `AdmissionCriteria` (Điểm chuẩn), `MajorInfo` (Tổ hợp môn).
- **Relationships**:
  - `(Program)-[:HAS_CRITERIA]->(AdmissionCriteria)`
  - `(Program)-[:HAS_INFO]->(MajorInfo)`
  - `(AdmissionMethod)-[:APPLIES_TO]->(Program)`

Mỗi node có `text_content` và vector embedding cho similarity search.

---

## 🔄 Luồng dữ liệu

### 1. Chuẩn bị dữ liệu (Offline)

1. Trích xuất dữ liệu từ PDF/DOCX → lưu JSON tại `data/processed/`.
2. Chạy `scripts/seed_neo4j.py`: tạo nodes, relationships, embeddings và Vector Index trong Neo4j.

### 2. Hỏi đáp (Online)

1. User gửi câu hỏi → POST `/api/chat/`.
2. Backend: phân loại ý định (LLM), embedding câu hỏi, vector search + graph traversal trên Neo4j.
3. Xây dựng context (Graph RAG) → GPT-4o sinh câu trả lời + gợi ý câu hỏi.
4. Lưu tin nhắn vào SQLite, trả response (kèm `bot_message_id` cho phản hồi).

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
│   ├── models/                # SQLAlchemy models, Pydantic schemas
│   ├── scripts/               # seed_neo4j, data ingestion
│   ├── main.py                # Entrypoint
│   ├── migrate_db.py          # Migration SQLite (bảng + cột)
│   └── chat_history.db        # SQLite (5 bảng)
├── frontend/                   # React + Vite + Tailwind
│   ├── src/
│   │   ├── App.jsx            # Chat, auth, favorites, feedback, voice, TTS
│   │   └── AdminDashboard.jsx
│   └── public/
├── data/
│   └── processed/             # diem_chuan.json, nganh_hoc.json, tohop_mon.json, phuong_thuc.json
├── README.md
└── docker-compose.yml         # Neo4j
```

---

## 📊 Dataset

Dữ liệu trích từ văn bản chính thức DNC:

- `Thong_bao_diem_chuan_2025_-_DNC-_22-8-2025.pdf`
- `thong-tin-tuyen-sinh-dai-hoc-nam-can-tho-2025.pdf`
- `ke_hoach_do_an_dnc_chatbot.docx`

Kết quả: `diem_chuan.json`, `nganh_hoc.json`, `tohop_mon.json`, `phuong_thuc.json` trong `data/processed/`.

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

### B2. Backend

```bash
cp .env.example .env
# Sửa .env: OPENAI_API_KEY, MAIL_* (nếu dùng quên mật khẩu)

cd backend
pip install -r requirements.txt
python migrate_db.py
python scripts/seed_neo4j.py
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

*Chatbot có thể mắc lỗi do AI. Vui lòng đối chiếu với Đề án tuyển sinh chính thức năm 2025.*
