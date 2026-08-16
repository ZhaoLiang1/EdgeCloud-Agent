from datetime import datetime


class HealthService:
    @staticmethod
    def check_server() -> dict:
        """
        健康检测业务逻辑
        Service层：纯业务代码，不依赖FastAPI框架
        """
        return {
            "status": "online",
            "service_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


# 全局实例
health_service = HealthService()