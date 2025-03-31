# stdlib
from typing import Optional
from typing import TYPE_CHECKING

# local
from . import _defaults

if TYPE_CHECKING:
    from .objects import FormStash

# ==============================================================================


class BaseException(Exception):
    """base exception class"""

    pass


class FormInvalid(BaseException):
    """Raise in your code when a Form is invalid"""

    error_main: str
    formStash: "FormStash"
    raised_by: Optional[str]

    def __init__(
        self,
        formStash: "FormStash",
        error_main: Optional[str] = None,
        error_main_overwrite: bool = False,
        error_main_append: bool = True,
        error_main_prepend: bool = False,
        raised_by: Optional[str] = None,
    ):
        self.formStash = formStash
        if error_main is None:
            error_main = _defaults.DEFAULT_ERROR_MAIN_TEXT
        self.error_main = error_main
        self.raised_by = raised_by
        super(FormInvalid, self).__init__()
        formStash.register_error_main_exception(
            self,
            error_main_overwrite=error_main_overwrite,
            error_main_append=error_main_append,
            error_main_prepend=error_main_prepend,
        )

    def __repr__(self) -> str:
        return "<FormInvalid `%s`>" % self.error_main


class FormFieldInvalid(FormInvalid):
    """Raise in your code when a Form's Field is invalid"""

    field: str
    error_field: str

    def __init__(
        self,
        formStash: "FormStash",
        field: str = "",
        error_field: Optional[str] = None,
        error_main: Optional[str] = None,
        message_append: bool = False,
        message_prepend: bool = False,
        error_main_append: bool = False,
        error_main_prepend: bool = False,
        allow_unknown_fields: bool = False,
    ):
        if not field:
            raise ValueError("field `%s` must be provided")
        if field not in formStash.schema.fields:
            if not allow_unknown_fields:
                raise ValueError(
                    "field `%s` is not in schema: `%s`" % (field, formStash.schema)
                )
        self.field = field
        if error_field is None:
            error_field = _defaults.DEFAULT_ERROR_FIELD_TEXT
        self.error_field = error_field

        # set the error so it appears in `formStash.results`
        formStash.set_error(
            field=field,
            message=error_field,
            message_append=message_append,
            message_prepend=message_prepend,
        )

        super(FormFieldInvalid, self).__init__(
            error_main=error_main,
            formStash=formStash,
            error_main_append=error_main_append,
            error_main_prepend=error_main_prepend,
        )

    def __repr__(self) -> str:
        return "<FormFieldInvalid %s: `%s`>" % (self.field, self.error_field)


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
