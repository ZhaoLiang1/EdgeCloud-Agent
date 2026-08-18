from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from config.settings import settings
from controller.health_controller import router as health_router
from controller.document_controller import router as document_router
from common.exceptions import BusinessException
from common.response import success, fail

# 创建应用实例
app = FastAPI(title=settings.SERVICE_NAME, debug=settings.DEBUG)

# 注册所有路由
app.include_router(health_router)
app.include_router(document_router)

# ========== 全局异常处理器 ==========
@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    # 捕获手动抛出的业务异常
    return JSONResponse(
        content=fail(code=exc.code, msg=exc.msg),
        status_code=200  # HTTP状态码统一200，靠业务code区分；也可改为exc.code
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # 捕获所有未知异常，屏蔽内部错误堆栈对外输出
    return JSONResponse(
        content=fail(code=500, msg=f"服务器异常：{str(exc)}"),
        status_code=200
    )


@app.get("/")
async def root():
    return {"msg": "EdgeCloud-Agent 后端服务启动成功，访问 /docs 查看接口文档"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG
    )