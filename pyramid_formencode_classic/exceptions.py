"""exceptions
"""


class BaseException(Exception):
    """base exception class"""
    
    errors = None
    form = None

    def __init__(self, message='', errors=None, form=None):
        self.message = message
        self.errors = errors
        self.form = form
        self.args = (message, errors, form)  # standardize to `Exception` usage

    def __str__(self):
        return repr(self.message)


class FormInvalid(BaseException):
    """Raise in your code when a form is invalid"""

    def __init__(self, message='', errors=None, form=None):
        super(FormInvalid, self).__init__(message=message, errors=errors, form=form)
    


class FieldInvalid(BaseException):
    """Raise in your code when a formfield is invalid"""
    pass


class CsrfInvalid(FormInvalid, FieldInvalid):
    """Raise in your code when a formfield is invalid"""
    pass


class ValidationStop(BaseException):
    """Stop validating"""
    pass


__all__ = ('BaseException',
           'FormInvalid',
           'FieldInvalid',
           'CsrfInvalid',
           'ValidationStop',
           )
