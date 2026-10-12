import streamlit as st
import sys
import os
from dotenv import load_dotenv
import chromadb

# 1. Cấu hình trang phải nằm đầu tiên
st.set_page_config(page_title="Bado Retail AI Agent", page_icon="🛍️", layout="centered")

# Nhúng thư mục src vào hệ thống
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, 'src'))

# ==========================================
# 2. KIỂM TRA BẢO MẬT & MÔI TRƯỜNG (TRƯỚC KHI IMPORT MODULE LÕI)
# ==========================================
load_dotenv(os.path.join(BASE_DIR, '.env'))
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("❌ Chưa cấu hình biến môi trường GEMINI_API_KEY. Vui lòng kiểm tra file .env hoặc cấu hình Docker.")
    st.stop()

# Đã an toàn -> Import các module cần key
from google import genai
from google.genai import types
from tool_calling import check_inventory
from rag_engine import build_vector_db, retrieve_policy

# ==========================================
# 3. TỰ ĐỘNG KHỞI TẠO DỮ LIỆU CHUẨN XÁC
# ==========================================
@st.cache_resource
def setup_databases():
    """Kiểm tra và tự động khởi tạo DB/Kho Vector nếu chưa có dữ liệu."""
    with st.spinner("🔄 Đang kiểm tra và khởi tạo hệ thống dữ liệu. Vui lòng đợi..."):
        try:
            # 3.1 Khởi tạo SQLite
            db_path = os.path.join(BASE_DIR, 'data', 'bado_retail.db')
            if not os.path.exists(db_path):
                # Import trực tiếp hàm tạo bảng (giả sử file init_db.py của bạn có hàm setup_database)
                # Nếu init_db.py của bạn chạy bằng khối __main__, hãy sửa nó thành một hàm để import vào đây!
                import subprocess
                subprocess.run([sys.executable, os.path.join(BASE_DIR, "src", "init_db.py")], check=True)
            
            # 3.2 Khởi tạo ChromaDB
            chroma_path = os.path.join(BASE_DIR, 'data', 'chroma_db')
            client = chromadb.PersistentClient(path=chroma_path)
            
            # Đếm số lượng record thay vì chỉ check thư mục tồn tại
            try:
                collection = client.get_collection("bado_policies")
                if collection.count() == 0:
                    build_vector_db()
            except Exception:
                # Nếu collection chưa tồn tại (bắn lỗi ValueError), tiến hành build
                build_vector_db()
                
            return True
        except Exception as e:
            st.error(f"❌ Lỗi nghiêm trọng khi khởi tạo dữ liệu: {str(e)}")
            st.stop()

setup_databases()

# ==========================================
# 4. GIAO DIỆN & LOGIC CHAT
# ==========================================
with st.sidebar:
    st.header("⚙️ Bảng Điều Khiển")
    st.success("Trạng thái: Trực tuyến 🟢")
    st.caption("AI Agent sử dụng mô hình Gemini 2.5 Flash, tích hợp Function Calling và RAG.")
    
    if st.button("🗑️ Xóa lịch sử chat", use_container_width=True):
        st.session_state.messages = [{"role": "assistant", "content": "👋 Dạ Bado Retail xin chào anh/chị!"}]
        if "chat_session" in st.session_state: del st.session_state.chat_session
        if "gemini_client" in st.session_state: del st.session_state.gemini_client
        st.rerun()

st.title("🛍️ Trợ lý Ảo Bado Retail")

def search_policy(query: str) -> str:
    """Tra cứu quy định, luật lệ, và chính sách của Bado Retail."""
    policy_docs = retrieve_policy(query, top_k=1)
    if policy_docs:
        clean_text = "\n\n".join(policy_docs)
        return f"Thông tin chính sách tìm thấy:\n{clean_text}"
    return "Dạ, em không tìm thấy quy định nào liên quan đến vấn đề này."

def initialize_chat():
    if "gemini_client" not in st.session_state:
        st.session_state.gemini_client = genai.Client(api_key=api_key)
        
    if "chat_session" not in st.session_state:
        system_instruction = (
            "Bạn là AI Agent chăm sóc khách hàng chính thức của chuỗi Bado Retail.\n"
            "QUY TẮC SỐNG CÒN:\n"
            "1. Xưng hô 'em' và gọi khách là 'anh/chị'. Thái độ luôn từ tốn, chuyên nghiệp.\n"
            "2. TUYỆT ĐỐI KHÔNG TỰ BỊA ĐẶT THÔNG TIN. Khi khách hỏi về giá, số lượng, phải dùng check_inventory.\n"
            "3. Khi khách hỏi về quy định đổi trả, bảo hành, giao hàng, phải dùng search_policy.\n"
            "4. Nếu khách hỏi những thứ ngoài phạm vi bán hàng (thời tiết, code...), từ chối lịch sự."
        )

        config = types.GenerateContentConfig(
            tools=[check_inventory, search_policy],
            system_instruction=system_instruction,
            temperature=0.2 
        )
        
        st.session_state.chat_session = st.session_state.gemini_client.chats.create(
            model="gemini-2.5-flash",
            config=config
        )
        
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "👋 Dạ Bado Retail xin chào anh/chị!"}]

initialize_chat()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Nhập câu hỏi của bạn...")

if user_input:
    with st.chat_message("user"): st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("🤖 Agent đang suy nghĩ..."):
            try:
                response = st.session_state.chat_session.send_message(user_input)
                bot_reply = response.text
                st.markdown(bot_reply)
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            except Exception as e:
                error_msg = f"❌ Lỗi hệ thống: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})