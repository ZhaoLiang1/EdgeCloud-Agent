"""
Milvus 客户端工具类
------------------
职责：
1. 连接 Milvus 服务
2. 创建 / 获取文档分片集合（Collection）
3. 提供插入、查询、删除等基础方法（今天先写连接和建集合，插入/查询明天补）

设计模式：单例模式 —— 整个项目只用一个 Milvus 连接，避免重复建连浪费资源。
"""

from pymilvus import (
    connections,
    utility,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
)

from config.settings import settings


class MilvusClient:
    """Milvus 操作封装"""

    # 类变量，保存唯一实例（单例）
    _instance = None

    def __new__(cls, *args, **kwargs):
        """__new__ 是 Python 创建对象的方法，在这里控制只创建一次"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化时连接 Milvus，并确保集合存在"""
        # 用一个标志防止重复初始化
        if not hasattr(self, "_connected"):
            self._connect()
            self.collection = self._get_or_create_collection()
            self._connected = True

    # ---------- 内部方法 ----------

    def _connect(self):
        """连接 Milvus 服务"""
        # alias="default" 给这个连接起个名字，后续操作默认用它
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
        )
        print(f"[Milvus] 已连接到 {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")

    def _get_or_create_collection(self) -> Collection:
        """
        如果集合已存在就直接获取，不存在就创建。
        集合结构见文件顶部的字段设计表。
        """
        collection_name = settings.MILVUS_COLLECTION_NAME

        # 先判断集合是否已存在
        if utility.has_collection(collection_name):
            print(f"[Milvus] 集合 '{collection_name}' 已存在，直接加载")
            collection = Collection(collection_name)
            collection.load()  # 加载到内存，才能查询
            return collection

        # ---------- 不存在则创建 ----------
        # 1. 定义每个字段（FieldSchema ≈ MySQL 的列定义）
        fields = [
            FieldSchema(
                name="id",
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=True,  # 主键自增，插入时不用传 id
                description="主键，自增",
            ),
            FieldSchema(
                name="doc_name",
                dtype=DataType.VARCHAR,
                max_length=256,
                description="文档名称",
            ),
            FieldSchema(
                name="chunk_index",
                dtype=DataType.INT64,
                description="文档内分片序号",
            ),
            FieldSchema(
                name="content",
                dtype=DataType.VARCHAR,
                max_length=4096,
                description="分片文本原文",
            ),
            FieldSchema(
                name="embedding",
                dtype=DataType.FLOAT_VECTOR,
                dim=settings.EMBEDDING_DIM,
                description="文本向量（BGE-M3, 1024维）",
            ),
        ]

        # 2. 用字段列表组装集合的 Schema（表结构）
        schema = CollectionSchema(
            fields=fields,
            description="文档分片向量集合",
            enable_dynamic_field=False,  # 不允许动态加字段，结构固定
        )

        # 3. 创建集合
        collection = Collection(
            name=collection_name,
            schema=schema,
            using="default",
        )
        print(f"[Milvus] 已创建集合 '{collection_name}'")

        # 4. 为向量字段建索引（没有索引查不动，类似 MySQL 的 INDEX）
        index_params = {
            "index_type": "IVF_FLAT",   # 索引类型：倒排文件 + 精确量化，适合中小数据量
            "metric_type": "COSINE",     # 相似度度量：余弦相似度，BGE 系列推荐用 COSINE
            "params": {"nlist": 128},    # 聚类中心数，数据量 < 100万时 128 够用
        }
        collection.create_index(
            field_name="embedding",
            index_params=index_params,
        )
        print("[Milvus] 已为 embedding 字段创建 IVF_FLAT 索引 (COSINE)")

        # 5. 加载到内存（创建后必须 load 才能查询）
        collection.load()
        return collection

    # ---------- 对外公开方法（今天先写几个基础的，明天补插入和查询） ----------

    def get_collection(self) -> Collection:
        """获取当前集合对象，给外部调用"""
        return self.collection

    def count(self) -> int:
        """返回集合里当前有多少条数据"""
        return self.collection.num_entities

    def disconnect(self):
        """断开连接（项目结束时调用，平时不用）"""
        connections.disconnect("default")
        print("[Milvus] 已断开连接")