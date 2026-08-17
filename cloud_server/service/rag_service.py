from common.milvus_client import MilvusClient
from common.embedding import batch_text2vector
from config.settings import settings


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

    client = MilvusClient()
    coll = client.get_collection()

    # 组装数据
    data = [
        file_names_list,
        chunk_index_list,
        chunk_texts,
        vector_list
    ]
    # 写入向量库
    coll.insert(data)
    # 持久化
    coll.flush()
    print(f"成功插入 {len(chunk_texts)} 条文本向量")