from pydantic import BaseModel
from typing import Any, Optional

class ResultModel(BaseModel):
    """
    全局统一接口返回格式
    类比 Android DataClass / Java实体类
    """
    code: int
    msg: str
    data: Optional[Any] = None


def success(data: Any = None, msg: str = "操作成功") -> ResultModel:
    """成功响应封装"""
    return ResultModel(code=200, msg=msg, data=data)


def fail(code: int = 500, msg: str = "操作失败", data: Any = None) -> ResultModel:
    """失败响应封装"""
    return ResultModel(code=code, msg=msg, data=data)