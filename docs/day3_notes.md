# Day3 学习笔记

## 今日完成
任务：文本分片+BGE-M3 Embedding+写入Milvus

## 踩坑记录

1、global _embedding_model
   在这个函数里，使用或修改在整个文件（全局作用域）中定义的那个名为 _embedding_model 的变量。
2、model.encode(text或text_list, normalize_embeddings=True)
   （1）model: 这代表你已经加载好的 Sentence-Transformer 模型（比如 all-MiniLM-L6-v2）。它就像一个“翻译官”，能把人类语言翻译成计算机能懂的数字列表。
   （2）.encode(text或text_list): 模型会性读取文字或者文字列表里的所有句子，并将它们转换成高维向量。比如输入了 3 句话，就会输出一个形状为 (3, 384) 的矩阵（假设模型维度是 384）。
   （3）normalize_embeddings=True：强制将生成的每个向量的“长度”（模长）压缩到刚好等于 1。（好处：这主要是为了后续计算余弦相似度时更方便。标准化之后，只需要计算两个向量的点积（Dot Product），就能直接得到它们的相似度得分，大大提升了检索速度。）
   （4）结果返回为 NumPy 数组，只需要.tolist()即可转为 Python 原生的 list
3、文本分片
   splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
    )
    （1）chunk_size：CHUNK_SIZE 强制规定了每个文本块的最大长度，保证检索的粒度足够细。
    （2）chunk_overlap：即使有分隔符，切割也难免会打断某些逻辑。CHUNK_OVERLAP 会让相邻的两个文本块之间产生一部分重叠的
    （3）separators 的优先级设计：遵循“优先级递减、递归尝试”的逻辑。它会先使用列表中的第一个分隔符（"\n\n"，即双换行/段落）来切割文本。如果切出来的文本块长度小于设定的 CHUNK_SIZE，那么这个块就合格了。如果切出来的某一段文本仍然大于 CHUNK_SIZE，它不会直接硬切，而是会“降级”，使用列表中的下一个分隔符（"\n"，即单换行）对这一段进行再次切割。直到切割到文本块长度小于设定的 CHUNK_SIZE。
4、settings.py文件中可优化
   老式写法：
     from pydantic_settings import BaseSettings
     from dotenv import load_dotenv
     import os

     env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
     load_dotenv(env_path)
     EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME")
   现在写法（Pydantic v2 Settings）：
     from pydantic_settings import BaseSettings, SettingsConfigDict
     BASE_DIR = Path(__file__).parent.parent
     # 告诉 pydantic 加载 .env
     model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore"  # 忽略.env里多余未定义变量，防止报错
     )
     EMBEDDING_MODEL_NAME: str = "BAAI/bge-m3"
5、语法以及写数据到向量库
   （1）file_names_list = [file_name] * len(chunk_texts)
        含义：把一个字符串复制和chunk_texts相同份数放进列表
   （2）chunk_index_list = list(range(len(chunk_texts)))
        含义：生成一个从 0 开始的连续整数列表，它的长度和文本块（chunk_texts）的长度完全一样。
   （3）组装数据
    data = [
        file_names_list,
        chunk_index_list,
        chunk_texts,
        vector_list
    ]
    将要存入向量数据库的所有数据，按照“列”打包成一个列表。（每个列表的长度必须完全相等）
   （4）写入向量库
    coll.insert(data)
   （5）持久化
    coll.flush()

6、相关CMD命令
  torch 是 sentence-transformers 运行必需，安装torch和sentence-transformers(文本向量化): 
    pip install torch --index-url https://download.pytorch.org/whl/cpu
    pip install sentence-transformers
  安装 langchain-text-splitters(文本分片)：
    pip install langchain-text-splitters
  验证：
    python test_day3.py


## Day3当前目录结构
EDGECLOUD-AGENT/
├── cloud_server/
│ ├── common/
│ │ ├── __init__.py
│ │ ├── exceptions.py
│ │ ├── milvus_client.py
│ │ ├── embedding.py ←【Day3 新增】向量工具类
│ │ └── response.py
│ ├── config/
│ │ ├── __init__.py
│ │ └── settings.py ←【Day3 修改】新增Embedding配置
│ ├── controller/
│ │ ├── __init__.py
│ │ └── health_controller.py
│ ├── docker/
│ │ ├── etcd_data/
│ │ ├── milvus_data/
│ │ ├── minio_data/
│ │ └── docker-compose.yml
│ ├── service/
│ │ ├── __init__.py
│ │ ├── health_service.py
│ │ ├── document_loader.py ←【Day3 修改】增加文本分片
│ │ └── rag_service.py ←【Day3 新增】向量入库服务
│ ├── static/
│ ├── .env ←【Day3 修改】增加Embedding环境变量
│ ├── main.py
│ └── requirements.txt ←【Day3 修改】追加新依赖
├── docs/
│ ├── day1_notes.md
│ ├── day2_notes.md
│ └── day3_notes.md ←【Day3 新增】学习踩坑笔记
├── venv/
├── .gitignore
└── test_day3.py ←【Day3 更新】完整链路测试脚本