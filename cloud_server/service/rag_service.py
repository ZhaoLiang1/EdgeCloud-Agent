from common.milvus_client import MilvusClient
from common.embedding import batch_text2vector
from config.settings import settings

from fastapi import UploadFile
from .document_loader import DocumentLoader


def insert_chunks_to_milvus(chunk_texts: list[str], file_name: str):
    """
    文本块批量向量化并写入Milvus
    :param chunk_texts: 分片文本列表
    """
    if not chunk_texts:
        return

    # 文档名称
    file_names_list = [file_name] * len(chunk_texts)

    # 分片序号
    chunk_index_list = list(range(len(chunk_texts)))

    # 批量生成向量
    vector_list = batch_text2vector(chunk_texts)

    # 组装数据
    data = [
        file_names_list,
        chunk_index_list,
        chunk_texts,
        vector_list
    ]

    client = MilvusClient()
    client.insert(data)
    

async def save_document_to_milvus(file: UploadFile, collection_name: str):
    """
    接收上传文件，解析分片，向量化写入Milvus
    """
    # 读取文件二进制流
    file_bytes = await file.read()
    filename = file.filename

    # 文本分片
    documentLoader = DocumentLoader()
    chunks = documentLoader.split_document(file_bytes, filename)
    if not chunks:
        raise Exception("文档未解析出有效文本片段")

    # 批量向量化
    vectors = batch_text2vector(chunks)

    # 文档名称
    file_names_list = [filename] * len(chunks)
    
    # 分片序号
    chunk_index_list = list(range(len(chunks)))

    # 组装入库数据
    data_list = [
        file_names_list, 
        chunk_index_list,
        chunks, 
        vectors
    ]

    client = MilvusClient(collection_name)
    client.insert(data_list)

    return {
        "filename": filename,
        "chunk_count": len(chunks)
    }

async def search_knowledge(query: str, collection_name: str, top_k: int = 4):
    """
    根据问题检索知识库片段
    """
    # query向量化
    query_vector = batch_text2vector([query])[0]
    client = MilvusClient(collection_name=collection_name)
    search_result = client.search(
        query_vector=query_vector,
        top_k=top_k
    )
    return search_result