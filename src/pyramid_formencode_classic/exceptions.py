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
    error_no_submission_text: Optional[str]
    formStash: "FormStash"
    raised_by: Optional[str]
    integrate_special_errors: bool

    def __init__(
        self,
        formStash: "FormStash",
        error_main: Optional[str] = None,
        error_no_submission_text: Optional[str] = None,
        integrate_special_errors: bool = True,
        raised_by: Optional[str] = None,
    ):
        self.formStash = formStash
        if error_main is None:
            error_main = _defaults.DEFAULT_ERROR_MAIN_TEXT
        self.error_main = error_main
        self.error_no_submission_text = error_no_submission_text
        self.integrate_special_errors = integrate_special_errors
        self.raised_by = raised_by
        super(FormInvalid, self).__init__()
        formStash.register_error_main_exception(
            self,
            integrate_special_errors=integrate_special_errors,
            error_no_submission_text=error_no_submission_text,
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
        allow_unknown_fields: bool = False,
        raised_by: Optional[str] = None,
        integrate_special_errors: bool = True,
        error_no_submission_text: Optional[str] = None,
    ):
        if not field:
            raise ValueError("`field` must be provided")
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
        )
        super(FormFieldInvalid, self).__init__(
            formStash=formStash,
            error_main=error_main,
            raised_by=raised_by,
            integrate_special_errors=integrate_special_errors,
            error_no_submission_text=error_no_submission_text,
        )
        formStash.register_error_main_exception(
            self,
            integrate_special_errors=integrate_special_errors,
            error_no_submission_text=error_no_submission_text,
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
