from common.milvus_client import MilvusClient
from common.embedding import batch_text2vector
from config.settings import settings

from fastapi import UploadFile
from .document_loader import DocumentLoader

from service.prompt_factory import build_rag_prompt
from common.llm_client import llm_client


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

def rag_query(question: str, collection_name: str, top_k: int = 3, score_threshold: float = 0.6):
    """
    完整RAG问答逻辑
    :param question: 用户提问
    :param collection_name: 向量库集合名称
    :param top_k: 召回数量
    :param score_threshold: 相似度阈值，低于该分数直接丢弃
    :return: dict {"answer":大模型回答, "reference":召回的分片列表}
    """
    # 1. 用户问题向量化
    query_vector = batch_text2vector([question])[0]

    # 2. 获取Milvus客户端，执行向量检索，返回结果
    client = MilvusClient(collection_name=collection_name)
    reference_list = []
    reference_list = client.search(
        query_vector=query_vector, 
        top_k=top_k, 
        score_threshold=score_threshold
    )

    # 3. 整理纯文本内容为list,并构造Prompt调用大模型
    if not reference_list: 
        answer = "【知识库没有找到相关内容】"
    else: 
        context_texts = []
        for reference in reference_list: 
            context_texts.append(reference["content"])
        full_prompt = build_rag_prompt(question, context_texts)
        answer = llm_client.chat(prompt=full_prompt, temperature=0.1)

    return {
        "answer": answer,
        "reference": reference_list
    }