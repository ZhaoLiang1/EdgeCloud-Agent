from fastapi import APIRouter, UploadFile, File, Query

from common.response import success, fail
from common.exceptions import BusinessException
from service.rag_service import save_document_to_milvus, search_knowledge, rag_query

router = APIRouter(prefix="/document", tags=["文档管理"])

# 允许的文件类型
ALLOW_SUFFIX = {".pdf", ".txt"}

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    collection_name: str = Query(default="edge_cloud_rag", description="Milvus向量集合名称")
):
    """
    上传文档，自动分片、向量化存入Milvus
    """
    # 1.校验文件后缀
    filename = file.filename
    suffix = "." + filename.split(".")[-1].lower()
    if suffix not in ALLOW_SUFFIX:
        raise BusinessException(msg=f"不支持文件类型{suffix}，仅支持pdf、txt")

    try:
        # 调用service执行文档解析+入库
        result = await save_document_to_milvus(file, collection_name)
        return success(data=result, msg="文档入库成功")
    except BusinessException as e:
        return fail(code=e.code, msg=e.msg)
    except Exception as e:
        return fail(msg=f"文档处理异常:{str(e)}")

@router.get("/query")
async def query_knowledge(
    query: str = Query(..., description="用户提问"),
    collection_name: str = Query(default="edge_cloud_rag"),
    top_k: int = Query(default=4, description="返回检索片段数量")
):
    """
    知识库语义检索接口，返回匹配文本片段
    """
    try:
        result = await search_knowledge(query, collection_name, top_k)
        return success(data=result, msg="检索成功")
    except Exception as e:
        return fail(msg=f"检索异常:{str(e)}")

# ========== 新增完整RAG问答接口 ==========
@router.get("/rag_chat")
async def document_rag_chat(
    query: str = Query(..., description="用户提问"),
    collection_name: str = Query(..., description="向量集合名称"),
    top_k: int = Query(3, description="向量召回条数"),
    score_threshold: float = Query(0.6, description="相似度最低阈值")
):
    """
    RAG问答接口：自动检索文档并基于文档生成答案
    """
    result = rag_query(
        question=query,
        collection_name=collection_name,
        top_k=top_k,
        score_threshold=score_threshold
    )
    return success(data=result)