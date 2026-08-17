"""
文本向量化
"""
from sentence_transformers import SentenceTransformer
from config.settings import settings

# 全局单例模型，程序启动只加载一次
_embedding_model = None


def get_embedding_model() -> SentenceTransformer:
    """获取向量模型单例"""
    global _embedding_model
    if _embedding_model is None:
        print(f"开始加载Embedding模型：{settings.EMBEDDING_MODEL_NAME}")
        _embedding_model = SentenceTransformer(
            model_name_or_path= settings.EMBEDDING_MODEL_NAME,
            cache_folder=settings.EMBEDDING_MODEL_CACHE
        )
        print("Embedding模型加载完成！")
    return _embedding_model


def text2vector(text: str) -> list[float]:
    """
    将单段文本转为向量
    :param text: 输入文本
    :return: float向量数组
    """
    model = get_embedding_model()
    vec = model.encode(text, normalize_embeddings=True)
    return vec.tolist()


def batch_text2vector(text_list: list[str]) -> list[list[float]]:
    """批量文本向量化，效率更高"""
    model = get_embedding_model()
    vecs = model.encode(text_list, normalize_embeddings=True)
    """其实可以直接vecs.tolist()，其内部会自动遍历"""
    return [v.tolist() for v in vecs]