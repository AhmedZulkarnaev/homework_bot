class ApiError(Exception):
    """Исключение для ошибок при обращении к API."""

    def __init__(self, message):
        """Сообщение об ошибке, описывающее причину исключения."""
        super().__init__(message)
        self.message = message


class VarTypeError(Exception):
    """Исключение для ошибок при обращении к данным."""

    def __init__(self, message):
        """Сообщение об ошибке, описывающее причину исключения."""
        super().__init__(message)
        self.message = message
