# pypi
import formencode
from pyramid.request import Request

# local
import pyramid_formencode_classic

# ------


class _Schema_Base(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True


class Form_Email(_Schema_Base):
    email = formencode.validators.Email(not_empty=True)


# ------


def prevent_MissingReturnStatement(request: Request) -> int:
    """
    run mypy to ensure `formStash.fatal_form` is typed correctly to raise an
    Exception; otherwise we can get `missing return statement` errors.
    """
    try:
        (result, formStash) = pyramid_formencode_classic.form_validate(
            request,
            schema=Form_Email,
        )
        if not result:
            raise pyramid_formencode_classic.FormInvalid(formStash)
        return 1
    except Exception as exc:
        formStash.fatal_form(error_main="%s" % exc)
