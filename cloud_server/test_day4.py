"""
Day4 完整链路自动化测试脚本
接口测试：文档上传入库 + 知识库检索
"""
import httpx

BASE_URL = "http://127.0.0.1:8000"

def test_upload():
    """测试文件上传接口"""
    upload_url = f"{BASE_URL}/document/upload"
    # 替换成你本地一个测试txt/pdf路径
    test_file_path = r"test_doc.txt"
    files = {"file": open(test_file_path, "rb")}
    resp = httpx.post(upload_url, files=files)
    print("状态码：", resp.status_code)  # 👈 新增：先看状态码
    print("原始响应：", resp.text)       # 👈 新增：再看原始文本内容
    print("上传结果：", resp.json())

def test_query():
    """测试知识库检索"""
    query_url = f"{BASE_URL}/document/query"
    params = {
        "query": "Android端侧",
        "top_k": 4
    }
    resp = httpx.get(query_url, params=params)
    print("检索结果：", resp.json())

if __name__ == "__main__":
    test_upload()
    test_query()