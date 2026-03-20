---
title: DNC Admission Chatbot
emoji: 🎓
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
license: mit
---

Chatbot tư vấn tuyển sinh ĐH Nam Cần Thơ (Graph RAG + Neo4j + Gemini).  
Thêm **Secrets** trên Space: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `OPENAI_API_KEY` (key Gemini).

Khi Neo4j **chưa có ngành**, app sẽ **tự nạp** dữ liệu từ `data/processed` lúc khởi động (chạy nền, vài phút). Tắt: Secret `KG_AUTO_SEED` = `false`. Kiểm tra: `/api/health` → `nganh_count`.
