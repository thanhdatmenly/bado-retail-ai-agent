import sqlite3
import os

# Đường dẫn trỏ file database vào thư mục /data
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BASE_DIR, 'data', 'bado_retail.db')

def create_and_seed_db():
    # Kết nối SQLite (tự động tạo file nếu chưa có)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Tạo bảng Products
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            price REAL,
            stock INTEGER
        )
    ''')

    # 2. Dữ liệu mẫu bám sát hệ sinh thái Bado (Bán lẻ, FnB, Thiết bị)
    sample_products = [
        ('Áo thun polo nam', 250000, 50),
        ('Trà đào cam sả', 35000, 15),
        ('Phần mềm quản lý Bado Retail (1 năm)', 2990000, 999),
        ('Máy in hóa đơn Xprinter', 1200000, 10)
    ]

    # 3. Chèn dữ liệu (bỏ qua nếu đã tồn tại nhờ IGNORE)
    cursor.executemany('''
        INSERT OR IGNORE INTO products (name, price, stock)
        VALUES (?, ?, ?)
    ''', sample_products)

    # Lưu và đóng kết nối
    conn.commit()
    conn.close()
    print(f"✅ Đã khởi tạo thành công Database tại: {db_path}")

if __name__ == "__main__":
    create_and_seed_db()