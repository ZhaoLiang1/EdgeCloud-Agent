# Day1 学习笔记

## 今日完成
- [x] Docker Compose 启动 Milvus 单机版（etcd + minio + milvus）
- [x] pymilvus 连接 Milvus，创建 doc_chunks 集合，含 5 个字段
- [x] 为 embedding 字段创建 IVF_FLAT 索引（COSINE）
- [x] DocumentLoader 支持 PDF（pdfplumber）和 TXT（多编码兜底）
- [x] 联调测试通过

## 踩坑记录
1、FastAPI使用方式
   初始化APIRouter: router = APIRouter(prefix="/api/v1", tags=["健康检测"]) 
   为router指定get方法和路径：@router.get("/health")
   初始化FastAPI: app = FastAPI(title=settings.SERVICE_NAME, debug=settings.DEBUG)
   main中的FastAPI注册其他路由: app.include_router(health_router)
2、uvicorn.run("main:app",host=settings.SERVICE_HOST,port=settings.SERVICE_PORT,
reload=settings.DEBUG) 解释
   （1）uvicorn 是一个极速的 Python ASGI（异步服务器网关接口）服务器。它专门用来运行像 FastAPI 这样支持异步的现代 Python Web 框架。
   （2）"main:app"：去 main.py 这个文件里，找到名为 app 的变量（通常它是 app = FastAPI() 的实例）。Uvicorn 会根据这个字符串动态导入并运行它。
   （3）host=settings.SERVICE_HOST：监听的网络接口（域名）
   （4）port=settings.SERVICE_PORT：监听的端口号
   （5）reload=settings.DEBUG：只要在编辑器里保存了代码，服务器会自动重启并加载最新代码
3、相关CMD命令
   创建虚拟环境：python -m venv venv（项目根目录 EdgeCloud-Agent）
   激活虚拟环境：venv\Scripts\activate或.\venv\Scripts\Activate.ps1（项目根目录 EdgeCloud-Agent）
   安装依赖：pip install -r requirements.txt（虚拟，进入 cloud_server）
   运行项目：uvicorn main:app --reload


## Day1当前目录结构

EDGECLOUD-AGENT/
├── cloud_server/
│   ├── common/
│   │   ├── __init__.py
│   │   ├── exceptions.py
│   │   └── response.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── controller/
│   │   ├── __init__.py
│   │   └── health_controller.py
│   ├── service/
│   │   ├── __init__.py
│   │   └── health_service.py
│   ├── static/
│   ├── .env
│   ├── main.py
│   └── requirements.txt
├── docs/
│   └── day1_notes.md
├── venv/
└── .gitignore