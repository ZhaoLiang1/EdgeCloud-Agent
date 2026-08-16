from fastapi import FastAPI
from config.settings import settings
from controller.health_controller import router as health_router

# 创建应用实例
app = FastAPI(title=settings.SERVICE_NAME, debug=settings.DEBUG)

# 注册所有路由
app.include_router(health_router)


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