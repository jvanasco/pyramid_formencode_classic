"""
Custom Exceptions
"""


class BaseException(Exception):
    """base exception class"""

    pass


class FormInvalid(BaseException):
    """Raise in your code when a Form is invalid"""

    message = None
    errors = None
    form = None

    def __init__(
        self,
        message="",
        errors=None,
        form=None,
        message_append=True,
        message_prepend=False,
    ):
        self.message = message
        self.errors = errors
        self.form = form
        super(FormInvalid, self).__init__()
        if form:
            form.register_error_main_exception(
                self, message_append=message_append, message_prepend=message_prepend
            )

    def __repr__(self):
        return "<FormInvalid `%s`>" % self.message


class FormFieldInvalid(FormInvalid):
    """Raise in your code when a Form's Field is invalid"""

    field = None

    def __init__(
        self,
        field="",
        message="",
        errors=None,
        form=None,
        message_append=True,
        message_prepend=False,
    ):
        self.field = field
        super(FormFieldInvalid, self).__init__(
            message=message,
            errors=errors,
            form=form,
            message_append=message_append,
            message_prepend=message_prepend,
        )

    def __repr__(self):
        return "<FormFieldInvalid %s: `%s`>" % (self.field, self.message)


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
