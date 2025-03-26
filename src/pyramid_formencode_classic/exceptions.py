# stdlib
from typing import Optional
from typing import TYPE_CHECKING

# local
from ._utils import TYPES_ERRORS

if TYPE_CHECKING:
    from .objects import FormStash

# ==============================================================================


class BaseException(Exception):
    """base exception class"""

    pass


class FormInvalid(BaseException):
    """Raise in your code when a Form is invalid"""

    message: str
    errors: Optional[TYPES_ERRORS] = None
    formStash: Optional["FormStash"] = None

    def __init__(
        self,
        message: str = "",
        errors: Optional[TYPES_ERRORS] = None,
        formStash: Optional["FormStash"] = None,
        message_append: bool = True,
        message_prepend: bool = False,
    ):
        self.message = message
        self.errors = errors
        self.formStash = formStash
        super(FormInvalid, self).__init__()
        if formStash:
            formStash.register_error_main_exception(
                self,
                message_append=message_append,
                message_prepend=message_prepend,
            )

    def __repr__(self) -> str:
        return "<FormInvalid `%s`>" % self.message


class FormFieldInvalid(FormInvalid):
    """Raise in your code when a Form's Field is invalid"""

    field: str

    def __init__(
        self,
        field: str = "",
        message: str = "",
        errors=None,  # ToDo: typing
        formStash: Optional["FormStash"] = None,
        message_append: bool = True,
        message_prepend: bool = False,
    ):
        self.field = field
        super(FormFieldInvalid, self).__init__(
            message=message,
            errors=errors,
            formStash=formStash,
            message_append=message_append,
            message_prepend=message_prepend,
        )

    def __repr__(self) -> str:
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
