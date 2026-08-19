# Day4 学习笔记

## 今日完成

LLM生成问答

打通单层RAG完整闭环：上传文档→向量入库→向量检索→LLM生成问答(组装 Prompt 交给大模型回答)

流程：用户问题 → Embedding向量 → Milvus粗召回top_k文本片段 → 将【召回片段+用户问题】组装Prompt → 请求大模型 → 返回带参考资料的答案

## 踩坑记录

1、语法 
   resp = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
   resp.raise_for_status()
   data = resp.json()
   data["choices"][0]["message"]["content"]
   （1）requests.post(...)
        使用 Python 的 requests 库，发送一个 HTTP POST 请求。
   （2）f"{self.base_url}/chat/completions"
        含义：这是你要访问的“AI 大脑”的完整网络地址（API 端点）。
        self.base_url：这是大模型服务商提供的基础网址（比如 OpenAI 的 https://api.openai.com/v1，或者 DeepSeek 的 https://api.deepseek.com/v1）。
        /chat/completions：这是聊天补全接口的固定路径。它明确告诉服务器：“我要使用你们的对话模型来生成文本”。
        f"..."：这是 Python 的 f-string 语法，用于把 self.base_url 的值拼接到后面的路径前面，组成一个完整的 URL。
   （3）headers=headers
        含义：请求头
        一般包含以下参数：
          Authorization: Bearer sk-xxxxxx：你的 API 密钥（API Key），用来证明“我是谁，我有没有权限调用这个模型”。
          Content-Type: application/json：告诉服务器“我这次发过去的数据是 JSON 格式的”。
   （4）json=payload
        含义：这是寄给 AI 的“信件正文”（请求体），也就是真正要问的问题。
        一般包含以下参数：
          model：指定用哪个模型（比如 "gpt-3.5-turbo" 或 "deepseek-chat"）。
          messages：一个列表，包含了你们的对话历史。比如 [{"role": "user", "content": "请根据以下背景知识回答问题..."}]。
          temperature：控制回答的创造性（值越高越发散，值越低越严谨）。
          max_tokens：限制 AI 最多回答多少个字。
        为什么用 json=：requests 库非常聪明，当使用 json= 参数时，它会自动把 Python 的字典转换成 JSON 字符串，并自动把 Content-Type 设置为 application/json，省去了手动转换的麻烦。
   （5）resp.raise_for_status()
        含义：requests 库提供的一个“错误自动拦截器”
        调用大模型的 API 时，服务器会返回一个状态码。raise_for_status() 会根据这个状态码做出不同的反应：
          如果请求成功（状态码是 2xx，比如 200 OK）：这行代码什么都不做，静默通过，程序继续往下执行 resp.json() 解析数据。
          如果请求失败（状态码是 4xx 或 5xx）：它会立刻抛出一个 requests.exceptions.HTTPError 异常。
   （6）data = resp.json()
        含义：Python 会把这段json字符串变成一个字典，赋值给 data 变量
   （7）data["choices"][0]["message"]["content"]
        拿到所需的数据
   （8）这只是兼容OpenAI的格式，不适合以后的本地模型等，后期可以用工厂模式优化，统一入参和出参
2、if not reference_list: 
        answer = "【知识库没有找到相关内容】"
   else: 
        answer = "【内容为*****】"
   answer可以在if...else...之外使用
3、LLM调用时temperature不要设置过高，>0.5容易产生幻觉；RAG推荐0.1以内；
4、向量检索与query编码必须同时开启normalize_embeddings=True；
5、score阈值需要根据Embedding模型微调，BGE-M3一般0.55~0.65区间。
6、如果使用本地模型，需要开启本地Ollama服务
7、本地1.8b模型太坑，改为使用智谱glm-4-flash
8、相关CMD命令
   cmd中进入OllamaSetup.exe文件夹，输入OllamaSetup.exe /DIR="D:\Ollama"，安装Ollama
   运行或安装模型：ollama run qwen:1.8b
   

## 测试记录
测试文档：test_doc.txt
测试提问：Milvus中的Collection是什么？
1. chunk_size=512，overlap=60
    现象：目标分片混杂大量无关文本，相似度偏低；容易排在候选列表后面；
2. chunk_size=300，overlap=60
    现象：分片主题更单一，向量语义更聚焦，相似度分数提升。

## 当前待优化点
1. 只有粗向量检索，无Rerank重排序；相关分片排序靠后问题Day8解决；
2. 没有文档重复上传检测，重复上传持续新增数据（Day9优化）；
3. chunk_size/overlap代码硬编码，暂不支持动态配置（Day9优化）。
4. 不兼容OpenAI的大模型，llm_client不能使用，后期需要优化。

## Day5当前目录结构

EDGECLOUD-AGENT/
├── cloud_server/
│ ├── common/
│ │ ├── __init__.py
│ │ ├── exceptions.py
│ │ ├── milvus_client.py
│ │ ├── embedding.py
│ │ ├── llm_client.py          ←【Day5 新增】LLM通用调用封装
│ │ └── response.py
│ ├── config/
│ │ ├── __init__.py
│ │ └── settings.py            ←【Day5 修改】追加LLM相关配置
│ ├── controller/
│ │ ├── __init__.py
│ │ ├── health_controller.py
│ │ └── document_controller.py ←【Day5 修改】新增/rag_chat RAG问答接口
│ ├── docker/
│ │ ├── etcd_data/
│ │ ├── milvus_data/
│ │ ├── minio_data/
│ │ └── docker-compose.yml
│ ├── service/
│ │ ├── __init__.py
│ │ ├── health_service.py
│ │ ├── document_loader.py
│ │ ├── prompt_factory.py      ←【Day5 新增】RAG提示词模板工厂
│ │ └── rag_service.py         ←【Day5 修改】新增rag_query完整RAG函数
│ ├── static/
│ ├── .env
│ ├── main.py
│ └── requirements.txt
├── docs/
│ ├── day1_notes.md
│ ├── day2_notes.md
│ ├── day3_notes.md
│ ├── day4_notes.md
│ └── day5_notes.md            ←【Day5 新增】联调测试记录、踩坑笔记
├── venv/
├── .gitignore
├── test_day3.py
└── test_day4.py               ←【Day5 修改】追加rag_chat接口测试代码