

class NodeException(Exception):
    """节点组件包异常基类（仅包含错误内容描述）"""
    def __init__(self, message='', error={}):
        """
        :param message: 错误内容描述，可选
        """
        self.message = message
        self.error = error

    def __str__(self):
        if self.error:
            return '{msg}-{err}'.format(
                msg=self.message,
                err=self.error)
        return self.message


class APIRequestError(NodeException):
    """API请求异常"""
    pass
