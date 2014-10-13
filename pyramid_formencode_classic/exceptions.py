"""exceptions
"""


class BaseException(Exception):
    """base exception class"""

    def __init__(self, message='', errors=None):
        self.message = message
        if errors:
            self.errors = errors

    def __str__(self):
        return repr(self.message)


class FormInvalid(BaseException):
    """Raise in your code when a form is invalid"""
    pass


class FieldInvalid(BaseException):
    """Raise in your code when a formfield is invalid"""
    pass


class ValidationStop(BaseException):
    """Stop validating"""
    pass
