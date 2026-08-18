"""
文档加载服务
------------
职责：读取本地 PDF / TXT 文件，提取纯文本内容，分片，返回统一格式。
"""

import os
import pdfplumber

from langchain_text_splitters import RecursiveCharacterTextSplitter
from config.settings import settings


class DocumentLoader:
    """文档加载器，支持 PDF 和 TXT"""

    # 支持的文件后缀（统一转小写比较）
    SUPPORTED_EXTENSIONS = {".pdf", ".txt"}

    def load(self, file_path: str) -> dict:
        """
        加载文档入口方法。
        根据文件后缀自动选择 PDF 或 TXT 解析器。

        参数：
            file_path: 文件的绝对路径或相对路径
        返回：
            {"doc_name": 文件名, "full_text": 提取到的纯文本}
        异常：
            文件不存在 / 不支持的格式 / 读取失败 时抛出异常
        """
        # 1. 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 2. 获取文件后缀（转小写，避免 .PDF 和 .pdf 区别对待）
        ext = os.path.splitext(file_path)[1].lower()

        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"不支持的文件格式: {ext}，仅支持 {self.SUPPORTED_EXTENSIONS}"
            )

        # 3. 取文件名（带后缀），用于存入 Milvus 的 doc_name 字段
        doc_name = os.path.basename(file_path)

        # 4. 根据格式分发到对应方法
        if ext == ".pdf":
            full_text = self._load_pdf(file_path)
        else:
            full_text = self._load_txt(file_path)

        # 5. 简单清洗：去掉首尾空白
        full_text = full_text.strip()

        print(
            f"[DocumentLoader] 已加载 '{doc_name}'，"
            f"文本长度 {len(full_text)} 字符"
        )
        return {"doc_name": doc_name, "full_text": full_text}

    def load_and_split_document(self, file_path: str) -> list[str]:
            """
            统一入口：加载文档并直接返回分片列表
            """
            # 1. 检查文件是否存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 2. 获取文件后缀（转小写，避免 .PDF 和 .pdf 区别对待）
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in self.SUPPORTED_EXTENSIONS:
                raise ValueError(
                    f"不支持的文件格式: {ext}，仅支持 {self.SUPPORTED_EXTENSIONS}"
                )

            # 3. 根据格式分发到对应方法
            if ext == ".pdf":
                full_text = self._load_pdf(file_path)
            else:
                full_text = self._load_txt(file_path)
            
            # 4. 简单清洗：去掉首尾空白
            full_text = full_text.strip()
            
            return self.split_text(full_text)

    # ---------- PDF 解析 ----------

    def _load_pdf(self, file_path: str) -> str:
        """
        用 pdfplumber 逐页提取 PDF 文本。

        pdfplumber 的工作原理：
        - open() 打开 PDF 文件
        - .pages 是所有页的列表
        - 每一页调用 .extract_text() 提取该页的文字
        - 页与页之间用换行符拼接

        注意：扫描版 PDF（图片型）提取不到文字，那需要 OCR，本项目暂不处理。
        """
        text_parts = []
        # with 语句确保文件操作完自动关闭，不会资源泄漏
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
                else:
                    # 有些页可能是纯图片，提取不到文字，跳过并提示
                    print(f"[DocumentLoader] 第 {page_num} 页未提取到文本（可能是图片页）")

        # 用两个换行拼接各页，区分页边界
        return "\n\n".join(text_parts)

    # ---------- TXT 解析 ----------

    def _load_txt(self, file_path: str) -> str:
        """
        读取 TXT 文件。

        编码问题是新手最常踩的坑：
        - Windows 下 TXT 常是 GBK 编码
        - 网上下载的常是 UTF-8
        - 所以先试 UTF-8，失败再试 GBK，都失败就报错
        """
        for encoding in ("utf-8", "gbk", "utf-8-sig"):
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                # 当前编码读不了，试下一个
                continue
        # 所有编码都失败
        raise UnicodeDecodeError(
            "utf-8/gbk", b"", 0, 1, f"无法识别文件编码: {file_path}"
        )
    
    # ---------- 文本分片 ----------

    def split_text(self, text: str) -> list[str]:
        """
        文本分片
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
        )
        chunks = splitter.split_text(text)
        return chunks

    def load_document(self, file_bytes: bytes, filename: str) -> str:
        """
        根据文件二进制和文件名，解析PDF/TXT，返回全文文本
        :param file_bytes: 文件二进制流
        :param filename: 原始文件名
        :return: 拼接后的完整文本
        """
        suffix = filename.lower().split(".")[-1]
        full_text = ""

        if suffix == "txt":
            full_text = file_bytes.decode("utf-8", errors="ignore")
        elif suffix == "pdf":
            # pdfplumber 从内存二进制加载pdf，不需要落地磁盘
            import io
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
        else:
            raise ValueError(f"不支持解析文件后缀：{suffix}")

        return full_text


    def split_document(self, file_bytes: bytes, filename: str) -> list[str]:
        """
        对外统一入口：文件二进制 → 解析文本 → 分片
        给rag_service直接调用】
        """
        text = self.load_document(file_bytes, filename)
        if not text.strip():
            return []
        return self.split_text(text)