# Day2 学习笔记

## 今日完成
- [x] Docker Compose 启动 Milvus 单机版（etcd + minio + milvus）
- [x] pymilvus 连接 Milvus，创建 doc_chunks 集合，含 5 个字段
- [x] 为 embedding 字段创建 IVF_FLAT 索引（COSINE）
- [x] DocumentLoader 支持 PDF（pdfplumber）和 TXT（多编码兜底）
- [x] 联调测试通过

## 踩坑记录
1、docker-compose.yml 配置
   （1） 环境变量注入：
    services:
      milvus:
        environment:
          ETCD_ENDPOINTS: etcd:2379   # 告诉 Milvus：去连接名为 "etcd" 的容器的 2379 端口
          MINIO_ADDRESS: minio:9000   # 告诉 Milvus：去连接名为 "minio" 的容器的 9000 端口
    注：这里的 etcd 和 minio 是 Docker 内部的服务名（Service Name）。Docker 内置的 DNS 会自动把这两个名字解析成对应的容器 IP。千万不要写成 localhost，否则 Milvus 会去容器内部找 localhost，肯定找不到。
   （2）数据持久化（相当于挂载磁盘）
    services:
      milvus:
        volumes:
          - ./milvus_data:/var/lib/milvus  # 宿主机目录:容器目录
    注：这保证了即使你删除了容器（docker-compose down），数据依然保存在你电脑当前目录下的 milvus_data 文件夹里。下次启动时，数据还在。
   （3）端口映射（相当于 Nginx 反向代理）
    services:
      milvus:
        ports:
          - "19530:19530" # SDK 连接端口
          - "9091:9091"   # 监控指标端口
    注：你的 Java/Python 代码连接 Milvus 时，用的就是宿主机的 19530 端口。
   （4）Milvus 与 Etcd 的版本关系
       现在配置：Milvus v2.4.10 + Etcd v3.5.5
       依赖规则：Milvus 2.4.x 版本系列通常依赖 Etcd v3.5.x
   （5）Milvus 与 MinIO 的版本关系
       配置：Milvus v2.4.10 + MinIO RELEASE.2023-03-20...
       依赖规则：Milvus 2.4.x 依赖 MinIO 的特定 API 行为
   （6）与SDK对应版本
       SDK 2.4.x + Server 2.4.x，大版本最好一样
2、Docker启动
   启动 Docker Desktop : 打开桌面Dockers应用
   启动 Milvus 容器:
     cd cloud_server\docker
     docker compose up -d
   查看状态: docker compose ps
3、单例
   （1）调用类之后（MilvusClient()），自动调用__new__和__init__
   （2）__new__ 是 Python 创建对象的方法，在这里控制只创建一次
       __new__方法内判断if cls._instance is None:，若为None则创建cls._instance = super().__new__(cls)
4、hasattr含义
   hasattr(object, name) 是 Python 的一个内置函数，作用是：检查这个对象身上，有没有叫 name 的属性，有返回True，无返回False
5、索引相关知识
   （1）index_type: "IVF_FLAT"
        I: FLAT（暴力搜索）
           原理：不建任何索引，直接把查询向量和库里所有的向量挨个算一遍距离。
           特点：准确率 100%，但数据量超过 10 万就会非常慢。
        II: IVF 系列（倒排文件 / 聚类分桶）
            原理：用 K-Means 算法把数据聚成 N 个簇（桶），搜索时只去最相关的几个桶里找。
            特点：大幅减少计算量，适合大规模数据。
            常见变种：IVF_FLAT（桶内不压缩，最准）、IVF_PQ（桶内做乘积量化压缩，极度省内存）、IVF_SQ8（标量量化，折中方案）。
        III: HNSW（分层导航小世界图）
             原理：在内存中构建一个多层级的图结构。搜索时像“坐电梯”一样，从顶层快速定位到大致区域，再逐层下沉到最底层进行精确搜索。
             特点：当前工业界线上高并发场景的首选。查询极快，召回率极高，但非常吃内存。
        项目代码用了 IVF_FLAT：这是最经典的折中方案，适合你当前中小规模的数据量，既能保证 100% 准确，速度又比 FLAT 快得多。
   （2）metric_type: "COSINE"
       想象你在一张白纸上画了两个箭头（向量），它们都有方向和长度。
       I: COSINE（余弦相似度）
          只看这两个箭头的方向是否一致，完全不管它们有多长。
          场景：比如“国王”和“王后”这两个词，不管它们出现的频率（长度）差多少，只要语义相近，它们在空间里的方向就是一致的，余弦相似度就极高。这就是为什么大模型（BGE等）生成的文本向量，默认都用余弦相似度。
       II: L2（欧氏距离）
           算这两个箭头终点之间的直线距离。距离越小越相似。它不仅看方向，还看长度。
           场景：适合图像识别，或者比较用户的年龄、收入等数值特征。
       III: IP（内积）
            把两个向量的对应坐标相乘再相加。它既受方向影响，也受长度影响。
            场景：通常用于推荐系统（比如根据用户历史行为推荐商品），前提是向量必须经过归一化处理。
    (3) nlist: 128
        I: 含义：nlist 的全称是 Number of Lists（分桶数 / 聚类中心数）。
        II: 举例：图书管理员先把这 100 万本书，按照主题分成了 128 个大书架（这就是 nlist=128）。当你来查“人工智能”时，管理员先扫一眼这 128 个书架的标签，发现第 3 号和第 45 号书架最相关。然后，管理员只去这两个书架里翻书，剩下的 126 个书架看都不看。
        III: 赋值：太大太小都不好，通常设为数据总量的平方根。对于 100 万以内的数据，128 是一个非常经典的黄金经验值。
    例：
      index_params = {
        "index_type": "IVF_FLAT",   # 索引类型：倒排文件 + 精确量化，适合中小数据量
        "metric_type": "COSINE",     # 相似度度量：余弦相似度，BGE 系列推荐用 COSINE
        "params": {"nlist": 128},    # 聚类中心数，数据量 < 100万时 128 够用
      }
      collection.create_index(
        field_name="embedding",
        index_params=index_params,
      )
 6、一些常用的语法
    (1) 判断文件是否存在：if not os.path.exists(file_path):。
    (2) 获取文件名和后缀（splitext），之后获取后缀并转为小写：os.path.splitext(file_path)  [1].lower()。
    (3) 判断字符串"ext"是否存在于数组中：if ext not in self.SUPPORTED_EXTENSIONS:
    (4) 获取文件名（带后缀）：os.path.basename(file_path)
    (5) 去掉头尾空白：full_text.strip()
    (6) with 语句确保文件操作完自动关闭，不会资源泄漏: with pdfplumber.open(file_path) as pdf:(打开文件是非常危险的 IO 操作。如果在读取过程中发生异常（比如内存溢出），普通的 close() 可能不会执行，导致文件句柄泄漏。with 语句保证了无论发生什么，退出代码块时都会自动、安全地释放资源。)
    (7) enumerate(iterable, start=1)：这是 Python 的神器。它会在遍历列表的同时，自动提供一个从 1 开始的索引（page_num）和当前的元素（page）。如：for page_num, page in enumerate(pdf.pages, start=1):
   （8）page_text = page.extract_text()：获取pdf文件中的文字；if page_text:含义:       page_text不为None、空字符串 ""、空列表 []
   （9）"\n\n".join(text_parts)：将列表转换为字符串，并拼接回车到列表中的每一项后边
   （10）遍历列表：for encoding in ("utf-8", "gbk", "utf-8-sig"):
   （11）try...except...
         try:
           with open(file_path, "r", encoding=encoding) as f:
             return f.read()
         except UnicodeDecodeError:
           # 当前编码读不了，试下一个
           continue
    (12) with open(file_path, "r", encoding=encoding) as f:
        with: 等价于 Java 7 引入的 try-with-resources 语法,try{}离开大括号时，JVM 自动调用 f.close()。
        file_path：文件的路径。
        "r"：代表 Read（只读模式）。如果是 "w" 就是 Write（写入），"a" 就是 Append（追加）。
        encoding=encoding：指定文件的编码格式（比如前面提到的 utf-8 或 gbk）。
        as f: 把打开的文件对象赋值给变量 f。接下来的缩进代码块里，就可以用 f.read() 来读取内容了。
   （13）test_txt = os.path.join(os.path.dirname(__file__), "test_sample.txt")
         __file__：当前 Python 文件的路径。
         os.path.dirname(__file__)：获取当前文件所在的文件夹目录。
         os.path.join(..., "test_sample.txt")：把目录和文件名拼起来。
   （14）with open(test_txt, "w", encoding="utf-8") as f:
          f.write("这是一个测试文档。\n它用来验证 DocumentLoader 能否正常读取TXT文件。\n")
        "w"：Write 模式。如果文件不存在就创建，如果存在就清空重写。
        f.write(...)：把这段测试文本写入到刚才创建的 TXT 文件中。
   (15) sys.path.insert(0, os.path.join(os.path.dirname(__file__), "cloud_server"))
        把 cloud_server 加入 Python 模块搜索路径
        sys.path: 相当于 JVM 的 Classpath（类路径）。它是一个列表（List），里面装满了 Python 解释器用来寻找模块的文件夹路径。
        sys.path.insert(0, ...)：相当于 classpath.add(0, newPath)。(代表插到列表的最前面。为什么要插到最前面？因为 Python 找模块是从上往下找的。插到最前面，意味着赋予这个目录最高优先级。如果系统自带的库或者别的地方也有同名模块，Python 会优先使用你这里的。)
        注：此处不对，按照项目目录，应该直接删掉，因为写为sys.path.insert(0, os.path.dirname(__file__))无意义
7、dotenv使用
   from dotenv import load_dotenv
   import os
   使用load_dotenv(env_path)加载env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")之后，就可以使用os.getenv("MILVUS_COLLECTION_NAME", "doc_chunks")加载.env文件中设置的常量了。
8、相关CMD命令
   进入 docker 目录：cd cloud_server\docker
   拉取镜像并后台启动：docker compose up -d（不会每次拉取，如果有，不会拉取）
   查看容器状态：docker compose ps
   运行文件：python test_day2.py
   

## Day2当前目录结构

EDGECLOUD-AGENT/
├── cloud_server/
│   ├── common/
│   │   ├── __init__.py
│   │   ├── exceptions.py
│   │   ├── milvus_client.py          ← 【Day2 新增】Milvus 连接+建集合工具类
│   │   └── response.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py               ← 【Day2 修改】新增 Milvus 配置读取
│   ├── controller/
│   │   ├── __init__.py
│   │   └── health_controller.py
│   ├── docker/
│   │   ├── etcd_data/                ← Docker 自动生成的数据目录
│   │   ├── milvus_data/              ← Docker 自动生成的数据目录
│   │   ├── minio_data/               ← Docker 自动生成的数据目录
│   │   └── docker-compose.yml        ← 【Day2 确认】Milvus 三件套配置
│   ├── service/
│   │   ├── __init__.py
│   │   ├── health_service.py
│   │   └── document_loader.py        ← 【Day2 新增】PDF/TXT 文档加载服务
│   ├── static/
│   ├── .env                          ← 【Day2 修改】新增 MILVUS_HOST/PORT 等
│   ├── main.py
│   └── requirements.txt
├── docs/
│   ├── day1_notes.md
│   └── day2_notes.md                 ← 【Day2 新增】学习笔记+踩坑记录
├── venv/
├── .gitignore
└── test_day2.py                      ← 【Day2 新增】联调测试脚本