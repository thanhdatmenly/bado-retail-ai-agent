import os
import re
import chromadb
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. Đọc biến môi trường từ file .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(" Không tìm thấy GEMINI_API_KEY trong file .env. Vui lòng kiểm tra lại!")

# 2. Cấu hình đường dẫn
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
TXT_PATH = os.path.join(DATA_DIR, 'chinh_sach_bado.txt')
CHROMA_PATH = os.path.join(DATA_DIR, 'chroma_db')

# Khởi tạo client Gemini
ai_client = genai.Client(api_key=api_key)

def split_policy_documents(file_path: str) -> list[str]:
    """Tách tài liệu và chỉ giữ lại các đoạn bắt đầu bằng số thứ tự '1.', '2.',...

    Loại bỏ hoàn toàn tiêu đề tài liệu hoặc dòng trống rác.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    raw_sections = re.split(r'\n(?=\d+\.\s)', content) # kỹ thuật lookahead kỹ thuật này giúp cắt ngay sau xuống dòng là 1 chữ số dâu chấm và khoảng trắng vd 1. 
    # Bắt buộc đoạn văn phải bắt đầu bằng chữ số theo sau là dấu chấm
    chunks = [
        sec.strip() for sec in raw_sections 
        if sec.strip() and re.match(r'^\d+\.', sec.strip())
    ]
    return chunks

def build_vector_db():
    """Khởi tạo và nạp dữ liệu chính sách vào ChromaDB."""
    print("1. Đang đọc và chia nhỏ tài liệu...")
    chunks = split_policy_documents(TXT_PATH)
    print(f"-> Đã trích xuất chính xác {len(chunks)} mục chính sách.")

    print("2. Đang kết nối ChromaDB...")
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    
    try:
        chroma_client.delete_collection(name="bado_policies")
    except Exception:
        pass

    collection = chroma_client.create_collection(
        name="bado_policies", 
        metadata={"hnsw:space": "cosine"}# cái này để so sánh mức độ giống nhau bằng sosine
    )

    print("3. Đang tạo Batch Embedding (RETRIEVAL_DOCUMENT)...")
    response = ai_client.models.embed_content(
        model="gemini-embedding-001",
        contents=chunks,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT" #Gắn cờ thông báo cho AI biết: "Đây là dữ liệu văn bản gốc cần lưu kho, hãy tối ưu vector để làm tài liệu đối chiếu"
        )
    )

    vectors = [item.values for item in response.embeddings]
    ids = [f"policy_{i+1}" for i in range(len(chunks))] #["policy_1", "policy_2", ..., "policy_5"]

    collection.add(
        ids=ids,
        embeddings=vectors, #Dãy tọa độ số do Gemini tạo ra cho từng đoạn.
        documents=chunks #: Nội dung chữ tiếng Việt gốc ban đầu.
    )
    #collection sẽ dán 3 thứ này lại với nhau thành một bộ hoàn chỉnh và ghi xuống ổ cứng.
    
    print(f"✅ Hoàn tất index {len(chunks)} mục vào ChromaDB!")

def retrieve_policy(query: str, top_k: int = 1) -> list[str]:
    """Tìm kiếm các đoạn chính sách liên quan nhất tới câu hỏi của khách hàng.

    Sử dụng model gemini-embedding-001 với task_type='RETRIEVAL_QUERY'.
    """
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma_client.get_collection(name="bado_policies")

    # Embed câu hỏi của người dùng
    query_response = ai_client.models.embed_content(
        model="gemini-embedding-001",
        contents=query,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY"
        )
    )
    query_vector = query_response.embeddings[0].values

    # Lấy top_k kết quả có khoảng cách cosine gần nhất
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k
    )

    # Trả về danh sách nội dung văn bản tìm được
    return results['documents'][0] if results['documents'] else []

if __name__ == "__main__":
    # 1. Chạy nạp dữ liệu vào Vector DB
    build_vector_db()

    # 2. Test thử tính năng truy xuất (Retrieval) ngay lập tức
    print("\n--- TEST THỬ TÍNH NĂNG TRUY XUẤT (RETRIEVAL) ---")
    test_question = "Máy in hóa đơn bị rơi vỡ có được bảo hành không?"
    print(f" Câu hỏi test: '{test_question}'")
    
    docs = retrieve_policy(test_question, top_k=1)
    if docs:
        print(f" Đoạn chính sách tìm thấy:\n{docs[0]}")
    else:
        print(" Không tìm thấy thông tin phù hợp.")