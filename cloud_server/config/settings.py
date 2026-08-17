from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

# 加载根目录.env文件
# load_dotenv()

# 加载 .env 文件（找当前文件的上一级目录下的 .env）
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path)

class Settings(BaseSettings):
    """全局配置类，读取环境变量"""
    # 服务配置
    SERVICE_NAME: str = "EdgeCloud-Agent"
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8000
    DEBUG: bool = True
    # Milvus
    MILVUS_HOST: str = os.getenv("MILVUS_HOST", "127.0.0.1")
    MILVUS_PORT: int = int(os.getenv("MILVUS_PORT", "19530"))
    MILVUS_COLLECTION_NAME: str = os.getenv("MILVUS_COLLECTION_NAME", "doc_chunks")
    # 向量维度
    EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "1024"))
    # Embedding配置
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME")
    EMBEDDING_MODEL_CACHE: str = os.getenv("EMBEDDING_MODEL_CACHE")
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "512"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "64"))
    # 后续扩展：大模型密钥都放这里

# 全局单例配置实例
settings = Settings()