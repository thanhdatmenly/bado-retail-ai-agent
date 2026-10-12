import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Nhúng thư mục hiện tại vào đường dẫn hệ thống để import file dễ dàng
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from tool_calling import check_inventory
from rag_engine import retrieve_policy

# 1. Khởi tạo môi trường
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("❌ Không tìm thấy GEMINI_API_KEY trong file .env.")

ai_client = genai.Client(api_key=api_key)

# ==========================================
# 2. ĐÓNG GÓI RAG THÀNH TOOL (AGENTIC RAG)
# ==========================================
def search_policy(query: str) -> str:
    """
    Tra cứu quy định, luật lệ, và chính sách của Bado Retail (đổi trả, bảo hành, vận chuyển, tích điểm...).
    Tuyệt đối phải gọi hàm này khi khách hàng phàn nàn, hỏi về cách xử lý sự cố, hoặc hỏi về luật của cửa hàng.

    Args:
        query: Câu hỏi hoặc từ khóa về chính sách (vd: 'phí vận chuyển', 'đổi trả áo thun', 'máy in hỏng').
    """
    print(f"\n[📚 HỆ THỐNG RAG] AI đang lật sổ tay chính sách tìm: '{query}'...")
    
    # Lấy về mảng các đoạn văn bản (list[str])
    policy_docs = retrieve_policy(query, top_k=1)
    
    if policy_docs:
        # Nối các phần tử trong list thành một chuỗi text sạch sẽ, cách nhau bằng dấu xuống dòng
        clean_text = "\n\n".join(policy_docs)
        return f"Thông tin chính sách tìm thấy:\n{clean_text}"
        
    return "Dạ, em không tìm thấy quy định nào liên quan đến vấn đề này trong sổ tay."

# ==========================================
# 3. KÍCH HOẠT ĐẶC VỤ BADO (AGENT)
# ==========================================
def run_bado_agent():
    # Cấu hình Nhân cách & Luật lệ cốt lõi (System Prompt)
    system_instruction = (
        "Bạn là AI Agent chăm sóc khách hàng chính thức của chuỗi Bado Retail.\n"
        "QUY TẮC SỐNG CÒN:\n"
        "1. Xưng hô 'em' và gọi khách là 'anh/chị'. Thái độ luôn từ tốn, chuyên nghiệp.\n"
        "2. TUYỆT ĐỐI KHÔNG TỰ BỊA ĐẶT THÔNG TIN. Khi khách hỏi về giá, số lượng, phải dùng công cụ check_inventory.\n"
        "3. Khi khách hỏi về quy định đổi trả, bảo hành, giao hàng, phải dùng công cụ search_policy.\n"
        "4. Nếu khách hỏi những thứ ngoài phạm vi bán hàng (thời tiết, chính trị, code...), hãy từ chối lịch sự."
    )

    # Đeo "ba lô" chứa 2 công cụ (SQLite và RAG) cho Agent
    #types.GenerateContentConfig:là một đối tượng cấu hình (configuration object) được sử dụng trong các thư viện SDK của Google Gen AI (như Google Gen AI SDK dành cho Python, JavaScript, v.v.) để tinh chỉnh cách mô hình Gemini tạo ra văn bản, mã nguồn hoặc các nội dung khác.
    config = types.GenerateContentConfig(
        tools=[check_inventory, search_policy],
        system_instruction=system_instruction,
        temperature=0.2  # Giữ ở mức thấp để tránh sinh ảo giác
    )

    chat = ai_client.chats.create(
        model="gemini-2.5-flash",
        config=config
    )

    print("\n" + "="*60)
    print("🤖 [BADO AGENT ĐÃ SẴN SÀNG]")
    print("💡 Mẹo test: Thử hỏi trộn lẫn giá cả và chính sách bảo hành.")
    print("Gõ 'quit' hoặc 'exit' để tắt bot.")
    print("="*60)
    
    # Vòng lặp chat liên tục
    while True:
        user_input = input("\n👤 Khách hàng: ")
        
        if user_input.lower() in ['quit', 'exit', 'thoát']:
            print("👋 Bado Agent xin chào tạm biệt!")
            break
            
        if not user_input.strip():
            continue
            
        try:
            # Gửi tin nhắn và để Agent tự quyết định dùng tool nào
            response = chat.send_message(user_input)
            print(f"\n💬 Trợ lý Bado:\n{response.text}")
        except Exception as e:
            # Xử lý lỗi API quá tải (Rate limit / 429 / 503) theo chuẩn an toàn
            print(f"\n❌ [LỖI MẠNG] Hệ thống đang bận hoặc gián đoạn API: {str(e)}")
            print("Vui lòng thử lại sau vài giây.")

if __name__ == "__main__":
    run_bado_agent()