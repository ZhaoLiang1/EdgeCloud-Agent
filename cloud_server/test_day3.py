import os
import sys
# 将cloud_server加入模块搜索路径，避免导入报错
#sys.path.append(os.path.join(os.path.dirname(__file__), "cloud_server"))

from service.document_loader import DocumentLoader
from service.rag_service import insert_chunks_to_milvus
from common.milvus_client import MilvusClient

# 获取当前文件所在文件夹：cloud_server
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    # 1. 初始化Milvus集合（不存在则创建）
    MilvusClient()

    # 准备一个测试txt/pdf文件，自行放到项目路径
    test_file = os.path.join(SCRIPT_DIR, "test_doc.txt")
    if not os.path.exists(test_file):
        # 自动生成测试文本，方便新手直接运行
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("""端云协同AI Agent项目介绍
本项目分为云端FastAPI服务和Android端侧程序。
云端使用Milvus向量数据库实现RAG知识库检索。
使用BGE-M3进行文本向量化，两级RAG提升检索精度。
端侧依靠llama.cpp运行Qwen1.5-1B-GGUF离线大模型。
支持本地离线对话与联网知识库问答两种模式。""")
        print("已自动生成 test_doc.txt 测试文件")

    # 2. 加载文档并分片
    documentLoader = DocumentLoader()
    chunks = documentLoader.load_and_split_document(test_file)
    print(f"文档分片总数：{len(chunks)}")
    for idx, c in enumerate(chunks):
        print(f"【分片{idx}】{c[:60]}...")

    # 3. 向量化并写入Milvus
    file_name = os.path.basename(test_file)
    insert_chunks_to_milvus(chunks, file_name)
    print("==== Day3 完整链路执行完成 ====")