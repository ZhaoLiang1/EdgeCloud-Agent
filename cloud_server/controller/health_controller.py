from fastapi import APIRouter
from common.response import success
from service.health_service import health_service

# 创建独立路由对象，替代全局app
router = APIRouter(prefix="/api/v1", tags=["健康检测"])


@router.get("/health")
async def health_check():
    """服务健康检测接口"""
    # Controller只做转发，无业务逻辑
    result = health_service.check_server()
    return success(data=result)