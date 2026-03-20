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

Khi Neo4j **trống** hoặc **quá ít ngành** (ví dụ seed dở còn 4 node), app **tự rebuild** từ `data/processed` (nền, vài phút). Ngưỡng đủ: mặc định **40** node `Nganh` — đổi bằng Secret `KG_MIN_NGANH_COMPLETE` (vd `45`). Tắt tự nạp: `KG_AUTO_SEED` = `false`. Kiểm tra: `/api/health` → `nganh_count`.
