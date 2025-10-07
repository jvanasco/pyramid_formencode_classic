# stdlib
import logging
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import TYPE_CHECKING

# pypi
import formencode
import formencode.htmlfill
from pyramid.interfaces import IResponse
from pyramid.renderers import render as pyramid_render
from pyramid.response import Response as PyramidResponse
from webob.multidict import MultiDict

# local
from . import _defaults
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

# ==============================================================================

log = logging.getLogger("pyramid_formencode_classic")

# ------------------------------------------------------------------------------


def _form_validate_core(
    request: "Request",
    schema: "Schema",
    form_stash: Optional[str] = None,  # name of stash
    formStash: Optional[FormStash] = None,  # a subclassed object; WHY?
    validate_post: bool = True,
    validate_get: bool = False,
    validate_params: Optional[MultiDict] = None,
    variable_decode: bool = False,
    dict_char: str = ".",
    list_char: str = "-",
    state: Optional[Any] = None,  # passthrough to formencode
    error_main_text: Optional[str] = None,
    error_main_key: Optional[str] = None,
    error_string_key: str = "Error_String",
    error_no_submission_text: Optional[str] = None,
    raise_FormInvalid: bool = False,
    csrf_name: str = "csrf_",
    csrf_token: Optional[str] = None,
    is_unicode_params: bool = False,
    foreach_defense: bool = True,
    debug_fails: Optional[bool] = None,
    allow_empty: Optional[bool] = None,
) -> Tuple[bool, FormStash]:
    """form validation only: returns True/False ; sets up Errors ;

    Validate input for a FormEncode schema.

    This is largely ported Pylons core, as is all of the docstring!

    Given a form schema, validate will attempt to validate the schema

    If validation was successful, the valid result dict will be saved as
    ``request.formStash.results``.

    .. warnings::
            ``validate_post`` and ``validate_get`` applies to *where* the
            arguments to be validated come from. It does *not* restrict the form
            to only working with post, merely only checking POST vars.

            ``validate_params`` will exclude get and post data

    ``request`` required
        A pyramid.request.Request object

    ``schema`` required
        Refers to a FormEncode Schema object to use during validation.

    ``form_stash`` (pyramid_formencode_classic._defaults.DEFAULT_FORM_STASH = '_default')
        Name of the attribute the FormStash will be saved into.
        Useful if you have multiple forms.

    ``formStash`` (None)
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

    ``is_unicode_params`` (False)
        passthrough to new `Form`

    ``foreach_defense`` (True)
        Implementing `ForEach` in FormEncode (such as dealing with checkboxes) can
        generate a LIST of errors instead of a single error.
        When `True`, this is detected and consolidated into a single error.

    ``debug_fails`` (None)
        Boolean. Used to instantiate ``FormStash`` objects.

    ``allow_empty``` (None)
        Boolean. If true, will not raise an special `*nothing_submitted` error if
        no params are presented.  This allows for the package to process empty POSTs
        which will use formencode's `if_mising` to supply a default value.
    """
    if __debug__:
        log.debug("form_validate - starting...")
    if not request:
        raise ValueError("`request` is required")
    if not schema:
        raise ValueError("`schema` is required")

    # delayed defaults
    if form_stash is None:
        form_stash = _defaults.DEFAULT_FORM_STASH
    if error_main_text is None:
        error_main_text = _defaults.DEFAULT_ERROR_MAIN_TEXT
    if error_main_key is None:
        error_main_key = _defaults.DEFAULT_ERROR_MAIN_KEY
    if error_no_submission_text is None:
        error_no_submission_text = _defaults.DEFAULT_ERROR_NOTHING_SUBMITTED

    errors = {}
    if formStash is None:
        formStash = FormStash(
            schema=schema,
            name=form_stash,
            error_main_key=error_main_key,
            error_main_text=error_main_text,
            is_unicode_params=is_unicode_params,
            error_no_submission_text=error_no_submission_text,
            debug_fails=debug_fails,
        )
    else:
        if formStash.schema != schema:
            raise ValueError(
                "`formStash.schema`[%s] is not `schema`[%s]"
                % (formStash.schema, schema)
            )

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
                formStash.set_special_error(
                    error_name="*nothing_submitted",
                    error_message=error_no_submission_text,
                )
                raise ValidationStop("no `validate_params`")
        if TYPE_CHECKING:
            assert isinstance(validate_params, MultiDict)
        _validate_params: Dict = validate_params.mixed()

        if variable_decode:
            if __debug__:
                log.debug("form_validate - running variable_decode on params")
            decoded_params = formencode.variabledecode.variable_decode(
                _validate_params, dict_char, list_char
            )
        else:
            decoded_params = _validate_params

        # if there are no params to validate against, then just stop
        # TODO: test how there are no `decoded_params` after
        #       determining there are `validate_params`
        if not decoded_params and not allow_empty:
            formStash.set_special_error(
                error_name="*nothing_submitted",
                error_message=error_no_submission_text,
            )
            raise ValidationStop("no `decoded_params`")
        formStash.is_submitted_vars = True

        # initialize our results
        results = {}

        if __debug__:
            log.debug("form_validate - validating against a schema")
        try:
            results = schema.to_python(decoded_params)
        except formencode.Invalid as e:
            errors = e.unpack_errors(variable_decode, dict_char, list_char)
            if isinstance(errors, str):
                errors = {error_string_key: errors}
        formStash.is_parsed = True

        formStash.parsed_form["defaults"] = decoded_params
        formStash.parsed_form["errors"] = errors
        formStash.parsed_form["results"] = results

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
                    field=formStash.error_main_key,
                    message=error_main_text,
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
            raise FormInvalid(
                formStash,
                error_main=error_main_text,
                error_no_submission_text=error_no_submission_text,
                integrate_special_errors=True,
                raised_by="_form_validate_core",
            )

    return (not formStash.is_error, formStash)


def form_validate(
    request: "Request", schema: "Schema", **kwargs
) -> Tuple[bool, FormStash]:
    result = _form_validate_core(request, schema, **kwargs)
    if TYPE_CHECKING:
        assert isinstance(result, tuple)
    return result


def form_reprint(
    request: "Request",
    form_print_method: Optional[Callable],
    form_stash=_defaults.DEFAULT_FORM_STASH,  # name of stash
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
    ``form_stash`` (pyramid_formencode_classic._defaults.DEFAULT_FORM_STASH = _default) -- specify a stash
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
        errors=formStash.errors_normal,
        auto_error_formatter=auto_error_formatter,
        **_htmlfill_kwargs,
    )
    response.text = form_content
    return response
