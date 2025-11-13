"""
异常类模块
定义API客户端可能抛出的异常
"""

class APIError(Exception):
    """API错误基类"""
    def __init__(self, message, status_code=None, response=None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)

class AuthError(APIError):
    """认证错误"""
    def __init__(self, message="认证失败", status_code=401, response=None):
        super().__init__(message, status_code, response)

class RateLimitError(APIError):
    """速率限制错误"""
    def __init__(self, message="速率限制已触发", status_code=429, response=None, retry_after=None):
        self.retry_after = retry_after
        super().__init__(message, status_code, response)

class NotFoundError(APIError):
    """资源不存在错误"""
    def __init__(self, message="资源不存在", status_code=404, response=None):
        super().__init__(message, status_code, response)
