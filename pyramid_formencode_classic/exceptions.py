"""exceptions
"""


class BaseException(Exception):
    """base exception class"""

    errors = None
    form = None

    def __init__(self, message="", errors=None, form=None):
        self.message = message
        self.errors = errors
        self.form = form
        self.args = (message, errors, form)  # standardize to `Exception` usage

    def __str__(self):
        return repr(self.message)


class FormInvalid(BaseException):
    """Raise in your code when a Form is invalid"""

    def __init__(
        self,
        message="",
        errors=None,
        form=None,
        message_append=True,
        message_prepend=False,
    ):
        super(FormInvalid, self).__init__(message=message, errors=errors, form=form)
        if form:
            form.register_error_main_exception(
                self, message_append=message_append, message_prepend=message_prepend
            )


class FormFieldInvalid(FormInvalid):
    """Raise in your code when a Form's Field is invalid"""

    pass


class CsrfInvalid(FormFieldInvalid):
    """Raise in your code when a Form's CSRF Field is invalid"""

    pass


class ValidationStop(BaseException):
    """Stop validating"""

    pass


__all__ = (
    "BaseException",
    "FormInvalid",
    "FormFieldInvalid",
    "CsrfInvalid",
    "ValidationStop",
)
