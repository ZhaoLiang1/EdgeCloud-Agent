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

    # 去掉单例
    # 类变量，保存唯一实例（单例）
    #_instance = None

    #def __new__(cls, *args, **kwargs):
    #    """__new__ 是 Python 创建对象的方法，在这里控制只创建一次"""
    #    if cls._instance is None:
    #        cls._instance = super().__new__(cls)
    #    return cls._instance

    """Milvus 操作封装
    连接全局复用，支持传入不同集合名，可操作多张向量表
    """
    # 静态变量：全局连接标记
    _connected = False
    # 静态缓存：{集合名: Collection对象}，防止重复load
    _collection_cache = {}

    def __init__(self, collection_name: str = settings.MILVUS_COLLECTION_NAME):
        self.collection_name = collection_name
        # 全局只建立一次连接
        if not MilvusClient._connected:
            self._connect()
            MilvusClient._connected = True

        # 缓存命中则直接使用，不存在则创建/加载
        if self.collection_name not in MilvusClient._collection_cache:
            coll = self._get_or_create_collection()
            MilvusClient._collection_cache[self.collection_name] = coll
        self.collection = MilvusClient._collection_cache[self.collection_name]

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

        #不要写死，修改为动态获取
        #collection_name = settings.MILVUS_COLLECTION_NAME
        collection_name = self.collection_name

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

    def insert(self, data_list: list[list]):
        coll: Collection = self.collection
        # 写入向量库
        coll.insert(data_list)
        # 持久化
        coll.flush()
        print(f"成功插入 {len(data_list)} 条文本向量")


    def search(self, query_vector, top_k=4, score_threshold: float = 0.6):
        """
        向量检索
        :param query_vector: 向量数组
        :param top_k: 返回条数
        :return:
        """
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 32}
        }
        collection: Collection = self.collection
        results = collection.search(
            data=[query_vector],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["doc_name", "chunk_index", "content", "embedding"]
        )
        output = []
        for hits in results:
            for hit in hits:
                hit_score = hit.score
                if hit_score > score_threshold: 
                    output.append({
                        "score": hit.score,
                        "doc_name": hit.entity.get("doc_name"),
                        "chunk_index": hit.entity.get("chunk_index"), 
                        "content": hit.entity.get("content"), 
                        "embedding": hit.entity.get("embedding")
                    })
        return output