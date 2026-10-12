import os
import sqlite3
import unicodedata
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. Khởi tạo môi trường bảo mật
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("❌ Không tìm thấy GEMINI_API_KEY trong file .env.")

ai_client = genai.Client(api_key=api_key)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'bado_retail.db')


# ==========================================
# 2. HÀM HỖ TRỢ XỬ LÝ TIẾNG VIỆT
# ==========================================
def normalize_vietnamese_string(text: str) -> str:
    """Loại bỏ dấu tiếng Việt, chuyển chữ thường, xử lý ký tự 'đ'/'Đ'."""
    if not text:
        return ""
    # Chuyển Đ/đ thành d
    text = re.sub(r'[đĐ]', 'd', text)
    # Tách dấu ra khỏi ký tự gốc và xóa dấu (loại bỏ ký tự Combining Diacritical Marks)
    text = unicodedata.normalize('NFD', text)
    text = re.sub(r'[\u0300-\u036f]', '', text)
    return text.lower().strip()


# ==========================================
# 3. ĐỊNH NGHĨA CÔNG CỤ (TOOL) CHO AI
# ==========================================
def check_inventory(product_name: str) -> list[dict]:
    """
    Tra cứu thông tin giá bán và số lượng tồn kho của sản phẩm trong hệ thống cửa hàng.
    
    Args:
        product_name: Tên sản phẩm hoặc một phần tên khách hàng nhắc đến (vd: 'ao thun', 'phần mềm', 'trà').
    
    Returns:
        Một danh sách chứa thông tin các sản phẩm khớp (tối đa 5), hoặc danh sách rỗng nếu không tìm thấy.
    """
    print(f"\n[🔧 THỰC THI HÀM] Tìm kiếm '{product_name}' trong SQLite...")
    
    query_words = normalize_vietnamese_string(product_name).split()
    matched_products = []
    
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        # Lấy toàn bộ sản phẩm vì DB rất nhỏ
        cursor.execute("SELECT id, name, price, stock FROM products")
        all_products = cursor.fetchall()
        
        for row in all_products:
            prod_id, prod_name, price, stock = row
            normalized_db_name = normalize_vietnamese_string(prod_name)
            
            # Khớp khi TOÀN BỘ các từ khóa trong search query đều xuất hiện trong tên DB
            if all(word in normalized_db_name for word in query_words):
                matched_products.append({
                    "id": prod_id,
                    "name": prod_name,
                    "price": price,
                    "stock": stock
                })
                
                if len(matched_products) >= 5: # Giới hạn 5 kết quả
                    break
                    
        return matched_products
    finally:
        # Đảm bảo luôn đóng kết nối dù code chạy thành công hay văng lỗi
        conn.close()


# ==========================================
# 4. KỊCH BẢN KIỂM THỬ (TEST CHATBOT)
# ==========================================
def test_agent_tool():
    # Cấu hình SDK tự động gọi hàm
    config = types.GenerateContentConfig(
        tools=[check_inventory],  
        temperature=0.1           
    )
    
    chat = ai_client.chats.create(
        model="gemini-2.5-flash",
        config=config
    )
    
    # Kịch bản 1: Khách gõ không dấu, thiếu chữ
    print("\n" + "="*50)
    print("👤 Khách hàng: 'Shop oi, ben minh ban ao thun nam k?'")
    response_1 = chat.send_message("Shop oi, ben minh ban ao thun nam k?")
    print(f"🤖 AI:\n{response_1.text}")
    
    # Kịch bản 2: Hỏi sản phẩm không có thực
    print("\n" + "="*50)
    print("👤 Khách hàng: 'Có bán iPhone 16 Pro Max không shop?'")
    response_2 = chat.send_message("Có bán iPhone 16 Pro Max không shop?")
    print(f"🤖 AI:\n{response_2.text}")

if __name__ == "__main__":
    test_agent_tool()