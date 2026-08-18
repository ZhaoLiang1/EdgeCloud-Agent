# Day4 学习笔记

## 今日完成
任务：开发 FastAPI 文件上传接口 + 基础 RAG 问答接口；实现「上传文档→分片向量化入库」API 能力，搭建基础问答链路

1. FastAPI 文件上传接口，支持pdf/txt
2. 文档上传自动分片、向量化写入Milvus
3. 语义检索接口，向量召回文档片段

业务流程新增链路
前端上传文件 → Controller接收 → service文档加载分片 → embedding向量化 → milvus存入向量库
用户提问接口 → Controller接收query → embedding编码 → milvus语义检索 → 返回相关文本片段（Day4暂不接入LLM生成回答，只完成检索）

## 踩坑记录

1、语法相关
   （1）ALLOW_SUFFIX = {".pdf", ".txt"}：是一个集合（Set）
   （2）上传文件参数相关含义
        @router.post("/upload")
        async def upload_document(
            file: UploadFile = File(...),
            collection_name: str = Query(default="edge_cloud_rag", description="Milvus向量集合名称")
        ):
        I: file: UploadFile = File(...)（接收文件, body）
           含义：告诉 FastAPI 从请求体（Body）中接收一个文件。
           UploadFile：这是 FastAPI 提供的特殊类型，用于处理上传的文件。它包含了文件名（filename）、文件类型（content_type）以及读取文件内容的方法（如 await file.read()）。
           File(...)：这是一个依赖注入函数。括号里的 ...（Ellipsis）表示这是一个必填项。如果客户端上传请求中没有包含名为 file 的文件，FastAPI 会自动返回 422 验证错误。
        II: collection_name: str = Query(...)（接收查询参数，query）
            含义：告诉 FastAPI 从 URL 的查询字符串（Query String）中获取一个名为 collection_name 的字符串参数。
            default="edge_cloud_rag"：如果用户在请求时没有传这个参数，系统会自动使用 "edge_cloud_rag" 作为默认的 Milvus 集合名称。
            description="Milvus向量集合名称"：这不仅是代码注释，FastAPI 还会把它自动渲染到 Swagger UI（自动生成的 API 文档）中，方便前端开发者理解。
   （3）suffix = "." + file.filename.split(".")[-1].lower()
        其实这个很简单，只不过是[-1]需要知道，在python中[-1]代表list中倒数第一个。
    (4) 异常处理
        try:
          ...
        except BusinessException as e:
          只有当代码抛出的异常精确地是 BusinessException（或者是它的子类）时，才会走这里。
        except Exception as e:
          Python 内置的其他任何常规错误
    (5) 自定义异常以及使用
       异常：
       class BusinessException(Exception):
            def __init__(self, msg: str, code: int = 400):
             ...
       使用：
       raise BusinessException(...)
   （6）全局异常处理
        @app.exception_handler(BusinessException)
        async def business_exception_handler(request: Request, exc: BusinessException):
            # 捕获手动抛出的业务异常
            return JSONResponse(
                content=fail(code=exc.code, msg=exc.msg),
                status_code=200  # HTTP状态码统一200，靠业务code区分；也可改为exc.code
            )
        解释：@app.exception_handler(BusinessException)告诉FastAPI注册了一个函数 business_exception_handler。以后只要程序里抛出了 BusinessException（或者它的子类），就自动去调用这个函数，把异常对象传给它。request: Request是FastAPI 框架在后台自动传的。exc: BusinessException是代码抛出 raise BusinessException(...)。
   （7）full_text = file_bytes.decode("utf-8", errors="ignore")
        file_bytes：当通过 FastAPI 的 await file.read() 读取上传的文件时，拿到的并不是直接的文本，而是一串底层的二进制字节（Bytes）。
        .decode("utf-8", ...)：把字节（Bytes）翻译回字符串（String）。
        errors="ignore"：如果在翻译的过程中，遇到了无法用 UTF-8 解释的乱码或损坏的字节，Python 会直接跳过（忽略）这些坏字节，继续翻译后面的内容，而不是抛出异常导致整个程序崩溃。
    (8) 使用 pdfplumber 从内存二进制加载pdf，不需要落地磁盘
        import io
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
        使用 pdfplumber 库，从内存中的 PDF 二进制数据里，逐页提取出所有的纯文本内容。
        io.BytesIO(file_bytes): 将通过 await file.read() 读取到的二进制数据（file_bytes），包装成一个“内存中的虚拟文件对象”。
        with pdfplumber.open(...) as pdf:：pdfplumber 的 open() 方法默认是接收一个真实的文件路径（比如 "./docs/test.pdf"）的。但在 Web 接口中，文件是直接上传到内存里的，并没有保存到硬盘上。io.BytesIO 就像是一个“伪装者”，让 pdfplumber 以为它正在读取一个真实的本地文件。
        for page in pdf.pages:：遍历这个列表，一页一页地处理。
        page.extract_text()：这是 pdfplumber 的核心方法。它会精准识别当前这一页上的文字，保留原有的排版和空格，并将它们拼接成一个完整的字符串（page_text）返回。
   （9）方法中的self
        当函数在类中时，self必须在函数中体现（因为会自动传）；没有类时，self是不自动传的
    (10) search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        这里定义了搜索的策略。
        "metric_type": "COSINE"：表示用“余弦相似度”来算谁跟谁更像（夹角越小越像）。
        "nprobe": 10：这是搜索的精细度，数字越大搜得越细，但速度越慢。
    (11) results = collection.search(data=[query_vector], anns_field="embedding",                 param=search_params,limit=top_k, output_fields=["text", "source"])
         I: 含义：拿着一个向量，去数据库里找最相似的几条数据，并把指定的字段内容带回来。
         II: data=[query_vector]: Milvus 搜的是向量（一串数字），不是文字。query_vector 就是你把用户的问题（比如“怎么使用RAG”）通过模型转换成的向量数组。这里必须包在列表 [] 里，因为 Milvus 支持批量搜索，哪怕你只搜一个问题，也要写成 [向量] 的格式。
         III: anns_field="embedding": 数据库表（Collection）里可能有很多列（比如 ID、文本、向量）。这个参数指定了 “请去名为 embedding 的这一列里做数学计算”。这个名字必须和创建数据库表时定义的向量字段名完全一致。
         IV: param=search_params: 搜索的策略配置。这里传入了你之前定义好的字典（包含 metric_type: COSINE 等）。它决定了是用“余弦相似度”还是“欧氏距离”来算谁跟谁更像，以及搜索的速度/精度平衡（nprobe）。
         V: limit=top_k: 也就是“只给我前几名”。如果 top_k 是 4，数据库算出几万个相似度后，只把得分最高的 4 条返回给你。
         VI: output_fields=["doc_name", "chunk_index", "content", "embedding"]: 向量检索本来只返回 ID 和分数。如果你想要看具体的文本内容，必须显式地告诉 Milvus：“把这几列的数据也顺便查出来给我”。
         VII: 返回值：两层嵌套，因为 Milvus 支持“批量搜索”（一次搜好几个问题），所以它的返回值结构必须能容纳多个问题的结果。外层列表 (results)，对应你传入的 data 数量，如果你传了 1 个向量，这里就有 1 组结果；如果你传了 10 个向量，这里就有 10 组结果。内层列表 (hits)，对应 top_k，每一组里包含了 K 个匹配到的对象。
2、相关CMD命令
   (1) 运行项目：python main.py
  
## 当前待优化点
1. 大文件一次性读取进内存存在OOM风险，后续支持流式写入
2. 缺少文件大小限制校验
3. 插入向量库时，缺少文档重复插入限制
4. chunk_size:int和chunk_overlap:int在分片时数值可能偏差很大
5. 查询时，不相似的相似值很高
6. 不相干文字很多

## Day4当前目录结构

EDGECLOUD-AGENT/
├── cloud_server/
│ ├── common/
│ │ ├── __init__.py
│ │ ├── exceptions.py             ←【Day4 修改】添加逻辑
│ │ ├── milvus_client.py          ←【Day4 修改】连接全局复用，支持传入不同集合名，可操作多张向量表，新增插入和search检索方法
│ │ ├── embedding.py
│ │ └── response.py
│ ├── config/
│ │ ├── __init__.py
│ │ └── settings.py
│ ├── controller/
│ │ ├── __init__.py               ←【Day4 修改】注册document路由
│ │ ├── health_controller.py
│ │ └── document_controller.py    ←【Day4 新增】文档上传、检索接口
│ ├── docker/
│ │ ├── etcd_data/
│ │ ├── milvus_data/
│ │ ├── minio_data/
│ │ └── docker-compose.yml
│ ├── service/
│ │ ├── __init__.py
│ │ ├── health_service.py
│ │ ├── document_loader.py        ←【Day4 修改】添加文件二进制 → 解析文本 → 原来的分片
│ │ └── rag_service.py            ←【Day4 修改】新增文件入库、检索方法
│ ├── static/
│ ├── .env
│ ├── main.py                     ←【Day4 修改】注册文档路由
│ └── requirements.txt            ←【Day4 修改】追加python-multipart依赖
├── docs/
│ ├── day1_notes.md
│ ├── day2_notes.md
│ ├── day3_notes.md
│ └── day4_notes.md               ←【Day4 新增】学习踩坑笔记
├── venv/
├── .gitignore
├── test_day3.py
└── test_day4.py                  ←【Day4 新增】端到端接口测试脚本