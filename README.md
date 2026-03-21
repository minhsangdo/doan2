# 🎓 Hệ Thống Chatbot Tư Vấn Tuyển Sinh Đại Học Nam Cần Thơ (DNC) - 2025

Đồ án xây dựng chatbot hỗ trợ **tư vấn tuyển sinh đại học** cho Trường Đại học Nam Cần Thơ (DNC), ứng dụng **Graph RAG (Retrieval-Augmented Generation)** kết hợp **Neo4j** để truy xuất tri thức có cấu trúc, hiển thị **nguồn tham chiếu (sources)** và gợi ý câu hỏi tiếp theo.

---

## Demo trực tuyến

| | |
|---|---|
| **Hugging Face Space** | [https://huggingface.co/spaces/minhsangdo/dnc-admission-chatbot](https://huggingface.co/spaces/minhsangdo/dnc-admission-chatbot) |

Mở link trên để dùng chatbot trên trình duyệt (không cần cài đặt local).

---

## Tổng quan

| Thành phần | Chi tiết |
|------------|----------|
| **Bài toán** | Chatbot tư vấn tuyển sinh DNC: ngành đào tạo, điểm chuẩn, tổ hợp môn, phương thức xét tuyển, học bổng… |
| **Giao diện** | React.js + Vite + Tailwind — `frontend/src/App.jsx` (chat, auth, lịch sử, favorites, feedback, giọng nói, TTS), `frontend/src/AdminDashboard.jsx` (admin) |
| **Backend & Graph RAG** | FastAPI — `backend/main.py`; logic RAG tập trung tại `backend/core/graph_rag.py`, `backend/core/intent_classifier.py`, `backend/core/llm_client.py`, `backend/core/embeddings.py` |
| **API** | REST dưới prefix `/api` — `backend/api/routes/chat.py`, `auth.py`, `admin.py` |
| **CSDL đồ thị** | Neo4j 5.x — nodes/relationships ngành, điểm, tổ hợp, phương thức, học bổng; vector index trên embedding ngành |
| **Embedding** | Gemini Embeddings API (cấu hình qua biến môi trường; mặc định trong code tương thích Gemini) |
| **LLM chính** | Gemini (chat + phân loại ý định) — qua `backend/core/llm_client.py` |
| **CSDL quan hệ** | SQLite `backend/chat_history.db` — người dùng, phiên chat, tin nhắn, ngành quan tâm, phản hồi |
| **Nguồn dữ liệu tri thức** | JSON tại `data/processed/` (trích từ PDF/DOCX tuyển sinh, điểm chuẩn, học bổng…); seed vào Neo4j bằng `scripts/seed_neo4j.py` |

---

## Tính năng

### 1. Hỏi đáp Graph RAG

- Nhận câu hỏi từ giao diện React → `POST /api/chat/`.
- **Phân loại ý định** (LLM), gồm intent **`hoc_bong`** khi hỏi về học bổng.
- **Embedding** câu hỏi khi cần, **vector search** + **graph traversal** trên Neo4j; với `hoc_bong` có thể truy toàn bộ node `HocBong`.
- **Gemini** sinh câu trả lời dựa trên context đã truy xuất; kèm **gợi ý câu hỏi** và **sources** từ Neo4j.
- Lưu tin nhắn vào SQLite, trả về `bot_message_id` phục vụ feedback.

### 2. Chuẩn bị & cập nhật tri thức (Knowledge Graph)

- Trích dữ liệu từ tài liệu nguồn → JSON trong `data/processed/`.
- Điểm chuẩn đợt 1 năm 2025 căn cứ **Thông báo 227/TB-ĐHNCT (22/8/2025)** (đồng bộ `nganh_hoc.json`, `diem_chuan.json`, …).
- Seed Neo4j: `python scripts/seed_neo4j.py` (tạo nodes, relationships, embeddings, vector index).
- **Admin**: `POST /api/admin/rebuild` — rebuild pipeline tri thức (tùy chọn full ingest); trên HF Space có thể **tự bootstrap** khi graph trống/thiếu (xem `deploy/hf-README.md`).

### 3. Quản lý người dùng & xác thực

- Đăng ký, đăng nhập (JWT), `GET /api/auth/me`, cập nhật `PUT /api/auth/profile` (khối thi, điểm dự kiến…).
- Quên mật khẩu: `POST /api/auth/forgot-password`, `POST /api/auth/reset-password` — email qua **Gmail SMTP** (local) hoặc **Resend** (khuyến nghị trên Hugging Face Space).

### 4. Phiên chat, ngành quan tâm, phản hồi

- Nhiều **phiên chat** theo user; lịch sử `GET /api/auth/history`.
- **Ngành quan tâm**: `GET/POST /api/auth/favorites`, `DELETE /api/auth/favorites/{ma_nganh}`.
- **Phản hồi chất lượng**: `POST /api/chat/feedback` (`message_id`, `rating`: `up` \| `down`).

### 5. Trải nghiệm đa phương tiện

- **Nhập giọng nói**: Web Speech API (Chrome/Edge; HTTPS hoặc localhost).
- **Text-to-Speech**: đọc câu trả lời (tiếng Việt).

### 6. Trang quản trị (Admin)

- Yêu cầu tài khoản **admin** (theo logic backend).
- **Thống kê KG**: `GET /api/admin/stats`.
- **Ngành tra cứu nhiều**: `GET /api/admin/stats/popular-majors`.
- **Lịch sử chat toàn hệ thống**: `GET /api/admin/chat-history`.
- **Danh sách / cập nhật ngành**: `GET /api/admin/majors`, `PUT /api/admin/majors/{ma_nganh}`.
- **Rebuild KG**: `POST /api/admin/rebuild`.

### 7. API & health

- `GET /` — kiểm tra nhanh (tùy cấu hình static/build).
- `GET /api/health` — trạng thái backend (kèm thông tin KG khi có).
- Swagger/OpenAPI: `/docs` (khi chạy Uvicorn).

---

## Kiến trúc

```text
Người dùng / Admin
        │
        ▼
React (Vite) — App.jsx / AdminDashboard.jsx
        │
        │  HTTP  /api/chat, /api/auth, /api/admin
        ▼
FastAPI (backend/main.py)
        │
        ├── Intent classifier (Gemini)
        ├── Embeddings (Gemini API)
        ├── Graph RAG (backend/core/graph_rag.py)
        │      └── Neo4j: vector search + graph traversal
        ├── LLM sinh câu trả lời (Gemini)
        │
        ├──▶ SQLite (backend/chat_history.db)
        │      users, chat_sessions, chat_messages,
        │      user_favorite_majors, message_feedbacks
        │
        └──▶ Neo4j
               Nganh, DiemChuan, TohopMon, PhuongThuc,
               NhomNganh, HocBong + relationships
```

---

## Cấu trúc thư mục

```text
doan2_chatboxtuyensinh_DoMinhSang/
├── backend/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py          # POST /api/chat, feedback
│   │   │   ├── auth.py          # register, login, profile, favorites, forgot/reset password
│   │   │   └── admin.py         # stats, rebuild, majors, chat-history
│   │   └── middleware.py
│   ├── core/
│   │   ├── graph_rag.py         # Pipeline Graph RAG
│   │   ├── intent_classifier.py
│   │   ├── llm_client.py
│   │   ├── embeddings.py
│   │   ├── neo4j_client.py
│   │   ├── database.py
│   │   ├── security.py
│   │   ├── email_utils.py
│   │   └── kg_bootstrap.py
│   ├── knowledge/
│   │   └── graph_builder.py     # Đọc JSON → Neo4j
│   ├── models/                  # SQLAlchemy + Pydantic schemas
│   ├── main.py                  # FastAPI entrypoint
│   ├── migrate_db.py
│   └── chat_history.db          # SQLite (runtime)
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── AdminDashboard.jsx
│   │   └── ...
│   └── public/
├── data/
│   ├── raw/                     # PDF/DOCX nguồn
│   └── processed/               # JSON: diem_chuan, nganh_hoc, tohop_mon, phuong_thuc, hoc_bong
├── docs/                        # Hướng dẫn bổ sung (ví dụ học bổng)
├── scripts/
│   └── seed_neo4j.py            # Seed Neo4j từ data/processed/
├── deploy/
│   └── hf-README.md             # Gợi ý Secrets/metadata Hugging Face Space
├── Dockerfile                   # Build static React + FastAPI (port 7860 cho HF)
├── docker-compose.yml           # Neo4j + dev stack
├── .env.example
└── README.md
```

---

## Cơ sở dữ liệu

### SQLite (`backend/chat_history.db`)

| Bảng | Mô tả |
|------|--------|
| **users** | Tài khoản, email, mật khẩu hash, khối thi, điểm dự kiến, token reset… |
| **chat_sessions** | Phiên chat (UUID), `user_id` có thể null (khách) |
| **chat_messages** | Tin nhắn user/bot theo `session_id` |
| **user_favorite_majors** | Ngành quan tâm (`ma_nganh`, `ten_nganh`) |
| **message_feedbacks** | Đánh giá tin nhắn bot (`up` / `down`) |

### Neo4j (Knowledge Graph)

| Label | Mô tả (gợi ý sau seed mẫu) |
|-------|----------------------------|
| **Nganh** | Ngành đào tạo + embedding vector |
| **DiemChuan** | Điểm chuẩn theo hình thức |
| **TohopMon** | Tổ hợp môn |
| **PhuongThuc** | Phương thức xét tuyển |
| **NhomNganh** | Nhóm ngành |
| **HocBong** | Học bổng / hỗ trợ |

**Quan hệ chính:** `HAS_SCORE`, `USES_COMBO`, `BELONGS_TO`, `ACCEPTS_METHOD` (chi tiết xem README phiên bản trước hoặc tài liệu đồ án).

**Vector index:** `Nganh.embedding` — cosine similarity, phục vụ truy vấn ngành/điểm.

---

## Luồng xử lý chính

### Chuẩn bị dữ liệu (offline)

1. PDF/DOCX → chuẩn hóa JSON vào `data/processed/`.
2. `python scripts/seed_neo4j.py` — tạo đồ thị, embedding, index trong Neo4j.

### Hỏi đáp (online)

1. Client → `POST /api/chat/` với nội dung câu hỏi và session.
2. Phân loại ý định → (nếu cần) embedding → truy vấn Neo4j.
3. Ghép context (Graph RAG) → LLM sinh câu trả lời + suggested questions.
4. Lưu SQLite → trả JSON (answer, sources, …).

---

## Dataset (nguồn tri thức)

| Nguồn | Nội dung | File JSON (`data/processed/`) |
|-------|----------|-------------------------------|
| Thông báo điểm chuẩn, thông tin TS 2025, kế hoạch… | Ngành, điểm, tổ hợp, phương thức | `diem_chuan.json`, `nganh_hoc.json`, `tohop_mon.json`, `phuong_thuc.json` |
| Tài liệu học bổng DNC | Chính sách học bổng | `hoc_bong.json` |

Hướng dẫn thêm/sửa học bổng: `docs/HUONG_DAN_THEM_DU_LIEU_HOC_BONG.md` (nếu có trong repo).

---

## Cài đặt và chạy (local)

### 1. Yêu cầu

- Docker & Docker Compose (Neo4j)
- Python 3.11+
- Node.js 18+
- **Gemini API key** — project đọc qua biến `OPENAI_API_KEY` trong `.env` (tên biến lịch sử; giá trị là key Google AI Studio / Gemini)

### 2. Biến môi trường

```bash
cp .env.example .env
```

Chỉnh tối thiểu: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `OPENAI_API_KEY` (Gemini), `FRONTEND_URL`.  
Quên mật khẩu: `MAIL_*` hoặc `RESEND_API_KEY` + `RESEND_FROM` (xem `.env.example`).

### 3. Neo4j

```bash
docker-compose up -d neo4j
```

### 4. Backend

```bash
cd backend
pip install -r requirements.txt
python migrate_db.py
cd ..
python scripts/seed_neo4j.py
cd backend
uvicorn main:app --reload --port 8000
```

### 5. Frontend

```bash
cd frontend
npm install
npm run dev
```

Mở **http://localhost:5173/** (API mặc định **http://localhost:8000** — cấu hình trong `frontend` qua `API_URL` / proxy tùy môi trường).

---

## Triển khai Hugging Face Space

| | |
|---|---|
| **Space** | [https://huggingface.co/spaces/minhsangdo/dnc-admission-chatbot](https://huggingface.co/spaces/minhsangdo/dnc-admission-chatbot) |
| **SDK** | Docker (`Dockerfile` — build React static + Uvicorn) |
| **Cổng** | 7860 |

Chi tiết Secrets (Neo4j, `OPENAI_API_KEY` = Gemini, tự seed KG…): xem **`deploy/hf-README.md`**.

### Biến môi trường gợi ý (Space)

| Biến | Bắt buộc | Mô tả |
|------|----------|--------|
| `NEO4J_URI` | Có | URI Bolt/Neo4j Aura |
| `NEO4J_USER` | Có | User Neo4j |
| `NEO4J_PASSWORD` | Có | Mật khẩu |
| `OPENAI_API_KEY` | Có | **Key Gemini** (tên biến giữ theo code) |
| `FRONTEND_URL` | Không | URL Space (CORS) |
| `RESEND_API_KEY` | Không | Gửi email quên mật khẩu qua Resend |
| `RESEND_FROM` | Không | Email người gửi (Resend) |
| `KG_AUTO_SEED` | Không | `false` để tắt tự seed khi khởi động |
| `KG_MIN_NGANH_COMPLETE` | Không | Ngưỡng số node `Nganh` coi là đủ dữ liệu |

---

## Công nghệ sử dụng

| Công nghệ | Vai trò |
|-----------|---------|
| Python 3.11 | Ngôn ngữ backend |
| FastAPI + Uvicorn | API REST |
| React + Vite + Tailwind | Giao diện |
| SQLite | Dữ liệu người dùng & hội thoại |
| Neo4j 5.x | Knowledge Graph + vector search |
| Gemini API | LLM + embeddings + intent |
| Docker | Neo4j local / HF Space |
| draw.io | Sơ đồ kiến trúc (trong `docs/`) |

---

## Tác giả

| | |
|---|---|
| **Sinh viên** | Đỗ Minh Sang |
| **Trường / Đơn vị** | Đại học Nam Cần Thơ (DNC) — Khoa Công nghệ Thông tin |
| **Niên khóa / năm** | 2024–2025 |

---

*Chatbot có thể mắc lỗi do AI. Vui lòng đối chiếu với đề án tuyển sinh và văn bản chính thức của DNC.*
