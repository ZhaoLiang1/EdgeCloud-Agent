class BusinessException(Exception):
    """
    业务自定义异常
    """
    def __init__(self, msg: str, code: int = 400):
        self.code = code
        self.msg = msg
        super().__init__(self.msg)