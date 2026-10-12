
# Xin một cái bếp (Hệ điều hành nhỏ gọn có sẵn Python)
FROM python:3.12-slim

# Tạo một thư mục ảo tên là /app bên trong xe tải
WORKDIR /app

# Cài đặt một số công cụ hệ thống để thư viện AI chạy mượt
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Mang danh sách nguyên liệu vào và bắt đầu cài đặt (pip install)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Mang toàn bộ code thư mục ui, src, data của bạn bỏ vào xe tải
COPY . .

# Mở sẵn cánh cửa số 8501 để khách hàng có thể nhìn vào
EXPOSE 8501

# Khi xe tải khởi động, tự động bật Streamlit lên
CMD ["streamlit", "run", "ui/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]