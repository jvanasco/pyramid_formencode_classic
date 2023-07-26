# stdlib
import logging
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import TYPE_CHECKING
from typing import Union

# pypi
import formencode
import formencode.htmlfill
from pyramid.interfaces import IResponse
from pyramid.renderers import render as pyramid_render
from pyramid.response import Response as PyramidResponse

# local
from ._defaults import DEFAULT_ERROR_MAIN_KEY
from ._defaults import DEFAULT_ERROR_MAIN_TEXT
from ._defaults import DEFAULT_FORM_STASH
from .exceptions import FormFieldInvalid
from .exceptions import FormInvalid
from .exceptions import ValidationStop
from .formatters import formatter_nobr  # default formatter
from .objects import FormStash
from .utils import determine_response_charset
from .utils import encode_formencode_errors

if TYPE_CHECKING:
    from formencode import Schema
    from pyramid.request import Request
    from pyramid.response import Response
    from webob.multidict import MultiDict

# ==============================================================================

log = logging.getLogger(__name__)

# ------------------------------------------------------------------------------


def form_validate(
    request: "Request",
    schema: Optional["Schema"] = None,
    form_stash: str = DEFAULT_FORM_STASH,
    form_stash_object: Optional[FormStash] = None,
    validate_post: bool = True,
    validate_get: bool = False,
    validate_params: Optional["MultiDict"] = None,
    variable_decode: bool = False,
    dict_char: str = ".",
    list_char: str = "-",
    state: Optional[Any] = None,  # passthrough to formencode
    error_main_text: str = DEFAULT_ERROR_MAIN_TEXT,
    error_main_key: str = DEFAULT_ERROR_MAIN_KEY,
    error_string_key: str = "Error_String",
    return_stash: bool = True,
    raise_FormInvalid: bool = False,
    raise_FormFieldInvalid: bool = False,
    csrf_name: str = "csrf_",
    csrf_token: Optional[str] = None,
    is_unicode_params: bool = False,
    foreach_defense: bool = True,
) -> Union[bool, Tuple[bool, FormStash]]:
    """form validation only: returns True/False ; sets up Errors ;

    Validate input for a FormEncode schema.

    This is largely ported Pylons core, as is all of the docstring!

    Given a form schema, validate will attempt to validate the schema

    If validation was successful, the valid result dict will be saved as
    ``request.formResult.results``.

    .. warnings::
            ``validate_post`` and ``validate_get`` applies to *where* the
            arguments to be validated come from. It does *not* restrict the form
            to only working with post, merely only checking POST vars.

            ``validate_params`` will exclude get and post data

    ``schema`` (None)
        Refers to a FormEncode Schema object to use during validation.

    ``form_stash`` (pyramid_formencode_classic.DEFAULT_FORM_STASH = '_default')
        Name of the attribute the FormStash will be saved into.
        Useful if you have multiple forms.

    ``form_stash_object`` (None)
        you can pass in a form stash object if you decided to subclass or alter FormStash

    ``validate_post`` (True)
        Boolean that indicates whether or not POST variables
        should be included during validation.

    ``validate_get`` (True)
        Boolean that indicates whether or not GET variables
        should be included during validation.

    ``validate_params``
        MultiDict of params if you want to validate by hand

    ``variable_decode`` (False)
        Boolean to indicate whether FormEncode's variable decode
        function should be run on the form input before validation.

    ``dict_char`` ('.')
        Passed through to FormEncode. Toggles the form field naming
        scheme used to determine what is used to represent a dict. This
        option is only applicable when used with variable_decode=True.

    ``list_char`` ('-')
        Passed through to FormEncode. Toggles the form field naming
        scheme used to determine what is used to represent a list. This
        option is only applicable when used with variable_decode=True.

    ``state``
        Passed through to FormEncode for use in validators that utilize a state object.

    ``error_main_key`` ('Error_Main')
        If there are any errors that occur, this will be the key they are dropped into.

    ``error_main_text`` ('There was an error with your form submittion.')
        If there are any errors that occur, this will drop an error in the key that
        corresponds to ``error_main_key``.

    ``error_string_key`` ('Error_String')
        If there are is a string-based error that occurs, this will be the key they are
        dropped into.

    ``return_stash`` (True)
        When set to True, returns a tuple of the status and the wrapped stash.
        Otherwise just returns the status, and a separate call is needed to get the Stash.
        As True:
            (status, stash)= form_validate()
        else:
            status = form_validate()

    ``is_unicode_params`` (False)
        passthrough to new `Form`


    ``foreach_defense`` (True)
        Implementing `ForEach` in FormEncode (such as dealing with checkboxes) can
        generate a LIST of errors instead of a single error.
        When `True`, this is detected and consolidated into a single error.

    """
    if __debug__:
        log.debug("form_validate - starting...")
    errors = {}
    if form_stash_object is None:
        formStash = FormStash(
            error_main_key=error_main_key,
            error_main_text=error_main_text,
            name=form_stash,
            is_unicode_params=is_unicode_params,
        )
    else:
        formStash = form_stash_object
    formStash.schema = schema

    try:
        # if we don't pass in ``validate_params``...
        # we must validate via GET, POST or BOTH
        if validate_params is None:
            if validate_post and validate_get:
                validate_params = request.params
            elif validate_post and not validate_get:
                validate_params = request.POST
            elif not validate_post and validate_get:
                validate_params = request.GET
            elif not validate_post and not validate_get:
                formStash.set_error(
                    field=formStash.error_main_key, message="Nothing submitted."
                )
                raise ValidationStop("no `validate_params`")

        validate_params = validate_params.mixed()

        if variable_decode:
            if __debug__:
                log.debug("form_validate - running variable_decode on params")
            decoded_params = formencode.variabledecode.variable_decode(
                validate_params, dict_char, list_char
            )
        else:
            decoded_params = validate_params

        # if there are no params to validate against, then just stop
        if not decoded_params:
            formStash.is_submitted_vars = False
            formStash.set_error(
                field=formStash.error_main_key, message="Nothing submitted."
            )
            raise ValidationStop("no `decoded_params`")
        else:
            formStash.is_submitted_vars = True

        # initialize our results
        results = {}

        if schema:
            if __debug__:
                log.debug("form_validate - validating against a schema")
            try:
                results = schema.to_python(
                    decoded_params,
                )
            except formencode.Invalid as e:
                errors = e.unpack_errors(variable_decode, dict_char, list_char)
                if isinstance(errors, str):
                    errors = {error_string_key: errors}
            formStash.is_parsed = True

        formStash.results = results
        formStash.errors = errors
        formStash.defaults = decoded_params

        if errors:
            if __debug__:
                log.debug("form_validate - Errors found in validation")
            formStash.is_error = True
            if foreach_defense:
                for _error_key in errors:
                    if isinstance(errors[_error_key], list):
                        _error_condensed = (
                            ", ".join([i for i in errors[_error_key] if i]) or "error"
                        )
                        errors[_error_key] = _error_condensed
            if error_main_text:
                # don't raise an error, because we have to stash the form
                formStash.set_error(
                    field=formStash.error_main_key, message=error_main_text
                )
        else:
            if csrf_token is not None:
                if request.params.get(csrf_name) != csrf_token:
                    # don't raise an error, because we have to stash the form
                    formStash.set_error(
                        field=formStash.csrf_error_field,
                        message=formStash.csrf_error_string,
                        is_error_csrf=True,
                    )
                    formStash.is_error_csrf = True

    except ValidationStop as exc:  # noqa: F841
        if __debug__:
            log.debug("form_validate - encountered a ValidationStop")
        pass

    # save the form onto the request
    request.pyramid_formencode_classic[form_stash] = formStash

    # now raise if needed
    if formStash.is_error:
        if raise_FormInvalid:
            raise FormInvalid()
        if raise_FormFieldInvalid:
            raise FormFieldInvalid()

    if return_stash:
        return (not formStash.is_error, formStash)
    return not formStash.is_error


def form_reprint(
    request: "Request",
    form_print_method: Optional[Callable],
    form_stash=DEFAULT_FORM_STASH,
    render_view: Optional[Callable] = None,
    render_view_template: Optional[str] = None,
    auto_error_formatter: Callable = formatter_nobr,
    error_formatters: Optional[Dict[str, Callable]] = None,
    **htmlfill_kwargs,
) -> "Response":
    """reprint a form
    args:
    ``request`` -- request instance
    ``form_print_method`` -- bound method to execute
    kwargs:
    ``frorm_stash`` (pyramid_formencode_classic.DEFAULT_FORM_STASH = _default) -- specify a stash
    ``auto_error_formatter`` (formatter_nobr) -- specify a formatter for rendering
        errors this is an htmlfill_kwargs, but we default to one without a br
    ``error_formatters`` (default None) is a dict of error formatters to be passed into
        htmlfill. in order to ensure compatibilty, this dict will be merged with a copy
        of the htmlfill defaults, allowing you to override them or add extras.
    `**htmlfill_kwargs` -- passed on to htmlfill
    """
    if __debug__:
        log.debug("form_reprint - starting...")

    response = None
    if form_print_method:
        response = form_print_method()
    elif render_view and render_view_template:
        response = PyramidResponse(
            pyramid_render(render_view_template, render_view(), request=request)
        )
    else:
        raise ValueError("invalid args submitted")

    # if not isinstance(response, PyramidResponse):
    if not IResponse.providedBy(response):
        raise ValueError(
            "`form_reprint` must be invoked with functions which generate "
            "a `Pyramid.response.Response` or provides the interface "
            "`pyramid.interfaces.IResponse`."
        )

    # If the form_content is an exception response, return it
    # potential ways to check:
    # # hasattr(response, 'exception')
    # # resposne.code != 200
    # # repsonse.code == 302 <-- http found
    if hasattr(response, "exception"):
        if __debug__:
            log.debug("form_reprint - response has exception, redirecting")
        return response

    formStash = request.pyramid_formencode_classic[form_stash]

    if __debug__:
        _debug = {
            "print_method": str(form_print_method),
            "render_view": str(render_view),
            "render_view_template": str(render_view_template),
            "auto_error_formatter": str(auto_error_formatter),
            "error_formatters": str(error_formatters),
        }
        formStash._reprints.append(_debug)

    form_content = response.text

    # Ensure htmlfill can safely combine the form_content, params and
    # errors variables (that they're all of the same string type)
    if not formStash.is_unicode_params:
        if __debug__:
            log.debug(
                "Raw string form params: ensuring the '%s' form and FormEncode errors "
                "are converted to raw strings for htmlfill",
                form_print_method,
            )
        encoding = determine_response_charset(response)

        if hasattr(response, "errors"):
            # FormEncode>=0.7 errors are unicode (due to being localized via ugettext). Convert any of the possible formencode unpack_errors formats to contain raw strings
            response.errors = encode_formencode_errors({}, encoding, response.errors)

    elif not isinstance(form_content, str):
        if __debug__:
            log.debug(
                "Unicode form params: ensuring the '%s' form is converted to unicode "
                "for htmlfill",
                formStash,
            )
        # py3 - test
        encoding = determine_response_charset(response)
        form_content = form_content.decode(encoding)

    # copy these because we don't want to overwrite a dict in place
    _htmlfill_kwargs = htmlfill_kwargs.copy()
    _htmlfill_kwargs.setdefault("encoding", request.charset)
    if error_formatters is not None:
        _error_formatters = dict(
            list(formencode.htmlfill.default_formatter_dict.items())
            + list(error_formatters.items())
        )
        _htmlfill_kwargs["error_formatters"] = _error_formatters

    # _form_content = form_content
    form_content = formencode.htmlfill.render(
        form_content,
        defaults=formStash.defaults,
        errors=formStash.errors,
        auto_error_formatter=auto_error_formatter,
        **_htmlfill_kwargs,
    )
    response.text = form_content
    return response
