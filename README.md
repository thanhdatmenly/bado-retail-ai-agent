# 🛍️ Bado Retail AI Agent

Một AI Agent thông minh tích hợp **Function Calling** (truy vấn SQLite) và **RAG** (truy xuất ChromaDB) sử dụng Gemini 2.5 Flash SDK mới nhất của Google.

## 🚀 Hướng dẫn khởi chạy bằng Docker

1. **Chuẩn bị môi trường:** Cài đặt [Docker](https://www.docker.com/).
2. **Cấu hình bảo mật:** 
   - Copy file `.env.example` thành file `.env`.
   - Điền API Key của bạn vào: `GEMINI_API_KEY=your_key_here`
   - *(Lưu ý: Dữ liệu mẫu sẽ tự động được sinh ra trong thư mục `/data` ở lần chạy đầu tiên).*
3. **Khởi chạy ứng dụng:**
   Mở Terminal và gõ:
   ```bash
   docker compose up --build