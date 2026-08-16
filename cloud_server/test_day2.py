"""
Day2 联调测试脚本
运行方式：在 cloud_server 目录下执行 python ../test_day2.py
（因为代码里 from config.settings import settings，需要 cloud_server 在 Python 路径里）
"""

import sys
import os

# 把 cloud_server 加入 Python 模块搜索路径
#sys.path.insert(0, os.path.join(os.path.dirname(__file__), "cloud_server"))

from common.milvus_client import MilvusClient
from service.document_loader import DocumentLoader


def test_milvus():
    """测试 Milvus 连接和集合创建"""
    print("\n" + "=" * 50)
    print("测试 1：Milvus 连接 + 集合创建")
    print("=" * 50)
    client = MilvusClient()
    collection = client.get_collection()
    print(f"集合名称: {collection.name}")
    print(f"当前数据条数: {client.count()}")
    print(f"字段列表: {[f.name for f in collection.schema.fields]}")
    print("✅ Milvus 测试通过\n")


def test_document_loader():
    """测试文档加载（需要准备一个测试文件）"""
    print("=" * 50)
    print("测试 2：文档加载")
    print("=" * 50)
    loader = DocumentLoader()

    # --- 测试 TXT ---
    # 先创建一个测试 TXT 文件
    test_txt = os.path.join(os.path.dirname(__file__), "test_sample.txt")
    with open(test_txt, "w", encoding="utf-8") as f:
        f.write("这是一个测试文档。\n它用来验证 DocumentLoader 能否正常读取 TXT 文件。\n")

    result = loader.load(test_txt)
    print(f"文件名: {result['doc_name']}")
    print(f"文本内容:\n{result['full_text']}")
    print(f"文本长度: {len(result['full_text'])} 字符")
    print("✅ TXT 加载测试通过\n")

    # 测试完删掉临时文件
    os.remove(test_txt)

    # --- 测试 PDF（如果你手头有 PDF 就改下面路径，没有就跳过）---
    # pdf_path = "C:/path/to/your/test.pdf"
    # if os.path.exists(pdf_path):
    #     result = loader.load(pdf_path)
    #     print(f"PDF 文件名: {result['doc_name']}")
    #     print(f"PDF 前 200 字: {result['full_text'][:200]}")
    #     print("✅ PDF 加载测试通过\n")
    # else:
    #     print("ℹ️  未找到测试 PDF，跳过 PDF 测试（自己找个 PDF 放进去再测）")


if __name__ == "__main__":
    test_milvus()
    test_document_loader()
    print("🎉 Day2 全部测试通过！")