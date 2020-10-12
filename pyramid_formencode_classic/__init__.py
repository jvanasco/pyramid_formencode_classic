import logging

log = logging.getLogger(__name__)

# stdlib
import sys


# pypi
import formencode
import formencode.htmlfill
from pyramid.response import Response as PyramidResponse
from pyramid.interfaces import IResponse
from pyramid.renderers import render as pyramid_render
import six
import webob.compat

# local
from .exceptions import FormInvalid, FormFieldInvalid, ValidationStop
from .formatters import formatter_nobr  # default formatter


# no warnings in > 0.3.0
"""
import warnings

# define warnings
def warn_future(message):
    warnings.warn(message, FutureWarning, stacklevel=2)


def warn_user(message):
    warnings.warn(message, UserWarning, stacklevel=2)
"""


# defaults
__VERSION__ = "0.4.3"

DEFAULT_FORM_STASH = "_default"
DEFAULT_ERROR_MAIN_KEY = "Error_Main"
DEFAULT_ERROR_MAIN_TEXT = "There was an error with your form submission."

DEPRECATION_WARNING = False
AUTOMATIC_CLEANUP = True


def determine_response_charset(response):
    """FROM PYLONS -- Determine the charset of the specified Response object,
    returning the default system encoding when none is set"""
    charset = response.charset
    if charset is None:
        charset = sys.getdefaultencoding()
    if __debug__:
        log.debug("Determined result charset to be: %s", charset)
    return charset


def encode_formencode_errors(errors, encoding, encoding_errors="strict"):
    """FROM PYLONS -- Encode any unicode values contained in a FormEncode errors dict
    to raw strings of the specified encoding"""
    if errors is None:
        return errors

    if six.PY2:
        if isinstance(errors, str):
            # FormEncode<=0.7 has a Python2-String, not Python2-Unicode
            return errors

    if isinstance(errors, six.text_type):  # Py2=unicode, PY3=str
        errors = errors.encode(encoding, encoding_errors)
    elif isinstance(errors, dict):
        for key, value in list(errors.items()):
            errors[key] = encode_formencode_errors(value, encoding, encoding_errors)
    else:
        # Fallback to an iterable (a list)
        errors = [
            encode_formencode_errors(error, encoding, encoding_errors)
            for error in errors
        ]
    return errors


class FormStash(object):
    """Wrapper object, stores all the vars and objects surrounding a form validation"""

    name = None
    is_error = None
    is_error_csrf = None
    is_parsed = False
    is_unicode_params = False
    is_submitted_vars = None
    schema = None
    errors = None
    results = None
    defaults = None
    css_error = "error"
    error_main_key = "Error_Main"
    error_main_text = None
    html_error_placeholder_template = '<form:error name="%s"/>'
    html_error_placeholder_form_template = (
        '<form:error name="%(field)s" data-formencode-form="%(form)s"/>'
    )
    html_error_template = """<span class="help-inline">%(error)s</span>"""
    html_error_main_template = (
        """<div class="alert alert-error">"""
        """<div class="control-group error">"""
        """<span class="help-inline"> <i class="icon-exclamation-sign"></i> %(error)s</span>"""
        """</div></div>"""
    )

    csrf_error_string = (
        """We're worried about the security of your form submission. """
        """Please reload this page and try again. """
        """It would be best to highlight the URL in your web-browser and hit 'return'."""
    )
    csrf_error_field = csrf_error_section = "Error_Main"

    _reprints = None  # internal use for debugging
    _exceptions_integrated = None

    def __init__(
        self,
        error_main_key=None,
        name=None,
        is_unicode_params=None,
        error_main_text=None,
    ):
        self.errors = {}
        self.results = {}
        self.defaults = {}
        if error_main_key:
            self.error_main_key = error_main_key
        if error_main_text:
            self.error_main_text = error_main_text
        if name:
            self.name = name
        self.is_unicode_params = is_unicode_params
        self._reprints = []

    def set_css_error(self, css_error):
        """sets the css error field for the form"""
        self.css_error = css_error

    def set_html_error_placeholder_template(self, template):
        """
        sets the html error template field for the form
        for example:
            <form:error name="%s"/>
        """
        self.html_error_placeholder_template = template

    def set_html_error_placeholder_form_template(self, template):
        """
        sets the html error template field for the form when data-formencode-form
        is needed

        for example:
            <form:error name="%(field)s" data-formencode-form="%(form)s"/>
        """
        self.html_error_placeholder_form_template = template

    def set_html_error_template(self, template):
        """sets the html error template field for the form"""
        self.html_error_template = template

    def set_html_error_main_template(self, template):
        """sets the html error template MAIN field for the form.
        useful for alerting the entire form is bad."""
        self.html_error_main_template = template

    def has_error(self, field):
        """Returns True or False if there is an error in `field`.
        Does not return the value of the error field, because the value could be False."""
        if field in self.errors:
            return True
        return False

    def has_errors(self):
        """Returns True or False if there is are errors."""
        if self.errors:
            return True
        return False

    def css_error(self, field, css_error=""):
        """Returns the css class if there is an error.  returns '' if there is not.
        The default css_error is 'error' and can be set with `set_css_error`.
        You can also overwrite with a `css_error` kwarg."""
        if field in self.errors:
            if css_error:
                return css_error
            return self.css_error
        return ""

    def html_error(self, field, template=None):
        """Returns an HTML error formatted by a string template.
        Currently only provides for `%(error)s`"""
        if self.has_error(field):
            if template is None:
                template = self.html_error_template
            return template % {"error": self.get_error(field)}
        return ""

    def html_error_placeholder(self, field=None, formencode_form=None):
        """
        If there are errors, returns a hidden input field for `Error_Main` or `field`.
        otherwise, returns an empty string.
        the htmlfill parser will update the hidden field to the template.
        this function is used to create a placeholder in forms

             <form action="/" method="POST">
                 <% form = request.pyramid_formencode_classic.get_form() %>
                 ${form.html_error_placeholder("Error_Main")|n}
                 <input type="text" name="email" value="" />
                 <input type="text" name="username" value="" />
             </form>
        """
        if self.has_errors():
            if field is None:
                field = self.error_main_key
            if formencode_form:
                # default: '<form:error name="%s" data-formencode-form="%s"/>'
                return self.html_error_placeholder_form_template % {
                    "field": field,
                    "form": formencode_form,
                }
            # default: '<form:error name="%s"/>'
            return self.html_error_placeholder_template % field
        return ""

    # copy this method
    # it should be deprecated. this was a mistake.
    html_error_main_fillable = html_error_placeholder

    def render_html_error_main(self, field=None, template=None):
        """
        Returns an HTML error formatted by a string template.
        currently only provides for `%(error)s`
        This was previously `html_error_main` in the 0.1 branch
        """
        error = None
        # look in the main error field specifically
        if self.has_errors():
            if field is None:
                field = self.error_main_key
            if self.has_error(field):
                error = self.get_error(field)
            else:
                error = "There was an error with your submission."
            if template is None:
                template = self.html_error_main_template
            return template % {"error": error}
        return ""

    def get_error(self, field):
        """Returns the error."""
        if field in self.errors:
            return self.errors[field]

    def set_error(
        self,
        field=None,
        message="Error",
        message_append=False,
        message_prepend=False,
        is_error_csrf=None,
    ):
        """
        Manages entries in the dict of errors

        As of v0.4.0, this will not raise an exception

        `field`: the field in the form
        `message`: your error message
        `message_append`: default `False`.
                          If `True`, will append the `message` argument to any existing argument in this `field`
        `message_prepend`: default `False`.
                           If `True`, will prepend the `message` argument to any existing argument in this `field`

        ``meessage_append` and ``message_prepend``` allow you to elegantly combine errors
        """
        if field is None:
            field = self.error_main_key

        if not message:  # None or ''
            raise ValueError("use `clear_error`")

        if message_append and message_prepend:
            raise ValueError("You can not set both `message_append` `message_prepend`")
        if message_append or message_prepend:
            _message_existing = self.errors[field] if (field in self.errors) else ""
            if not _message_existing and (field == self.error_main_key):
                _message_existing = self.error_main_text

            if _message_existing != message:  # don't duplicate the error
                _message_existing = [_message_existing] if _message_existing else []
                if message_append and message:
                    _message_existing.append(message)
                elif message_prepend and message:
                    _message_existing.insert(0, message)
                message = " ".join(_message_existing)

        self.errors[field] = message

        # mark the form as invalid
        self.is_error = True

        # set the main error if needed
        if self.error_main_key not in self.errors:
            self.errors[self.error_main_key] = self.error_main_text

        if is_error_csrf:
            self.is_error_csrf = True

    def clear_error(self, field=None):
        """clear the dict of errors"""
        if self.errors:
            if field:
                if field in self.errors:
                    del self.errors[field]
                if len(self.errors) == 1:
                    if self.error_main_key in self.errors:
                        del self.errors[self.error_main_key]
            else:
                self.errors = {}
        if self.errors:
            self.is_error = True

    def fatal_form(self, message=None, message_append=True, message_prepend=False):
        """
        Sets an error for the main error key, then raises a `FormInvalid`.
        """
        _kwargs = {}
        if message_append is not None:
            _kwargs["message_append"] = message_append
        if message_prepend is not None:
            _kwargs["message_prepend"] = message_prepend
        # default to the error_main_text
        if message is None:
            message = self.error_main_text
        self.set_error(field=self.error_main_key, message=message, **_kwargs)
        self._raise_unique_FormInvalid()

    def fatal_field(
        self, field=None, message=None, message_append=True, message_prepend=False
    ):
        """
        Sets an error for ``field``, then raises a `FormInvalid`.

        consider this code:

            try:
                except CaughtError as e:
                    formStash.set_error(message="We encountered a `CaughtError`",
                                        )
                ...
            except formhandling.FormInvalid as exc:
                formStash.set_error(field='Error_Main',
                                    message="There was an error with your form.",
                                    message_prepend=True,
                                    )
                return formhandling.form_reprint(...)

        This would generate the following text for the `Error_Main` field:

            There was an error with your form.  We encountered a `CaughtError`

        """
        if field is None:
            raise ValueError("`field` must be submitted")
        if message is None:
            raise ValueError("`message` must be submitted")
        _kwargs = {}
        if message_append is not None:
            _kwargs["message_append"] = message_append
        if message_prepend is not None:
            _kwargs["message_prepend"] = message_prepend
        self.set_error(field=field, message=message, **_kwargs)
        self._raise_unique_FormInvalid()

    def _raise_unique_FormInvalid(self):
        """
        this is used to defend against integrating an exception multiple times
        via `register_error_main_exception` after being created in
        `fatal_form` or `fatal_field`.
        """
        _FormInvalid = FormInvalid()
        if self._exceptions_integrated is None:
            self._exceptions_integrated = []
        self._exceptions_integrated.append(_FormInvalid)
        raise _FormInvalid

    def register_error_main_exception(
        self, exc, message_append=True, message_prepend=False
    ):
        """
        This is a convenience method to replace this common use pattern:
        ------------------------------------------------------------------------
            try:
                ...
                raise formhandling.FormInvalid('foo')
                ...
            except formhandling.FormInvalid as exc:
                - if exc.message:
                -     formStash.set_error(field=formStash.error_main_key,
                -                         message=exc.message,
                -                         message_prepend=True
                -                         )
                + formStash.register_error_main_exception(exc)
                <<<<<
                return formhandling.form_reprint(
                    self.request,
                    self._print_form,
                )
        ------------------------------------------------------------------------
        """
        if isinstance(exc, FormInvalid):

            if self._exceptions_integrated is None:
                self._exceptions_integrated = []

            if exc not in self._exceptions_integrated:
                self._exceptions_integrated.append(exc)
                if exc.message:
                    self.set_error(
                        field=self.error_main_key,
                        message=exc.message,
                        message_append=message_append,
                        message_prepend=message_prepend,
                    )
            else:
                log.debug("exception already integrated")

    def csrf_input_field(
        self,
        id="csrf_",
        name="csrf_",
        type="hidden",
        csrf_token="",
        htmlfill_ignore=True,
    ):
        return """<input id="%(id)s" type="%(type)s" name="%(name)s" value="%(csrf_token)s"%(htmlfill_ignore)s/>""" % {
            "id": id,
            "name": name,
            "type": type,
            "csrf_token": csrf_token,
            "htmlfill_ignore": " data-formencode-ignore='1' "
            if htmlfill_ignore
            else "",
        }


class FormStashList(dict):
    """
    dict for holding multiple `FormStash`
    this allows for more than one form to be processed on a request
    this should be registered onto a request as

        `request.pyramid_formencode_classic = FormStashList()`

    the preferred mechanism is to use pyramid's `add_request_method`
    """

    def get_form(
        self,
        form_stash=DEFAULT_FORM_STASH,
        error_main_key=DEFAULT_ERROR_MAIN_KEY,
        error_main_text=DEFAULT_ERROR_MAIN_TEXT,
    ):
        if form_stash not in self:
            self[form_stash] = FormStash(
                name=form_stash,
                error_main_key=DEFAULT_ERROR_MAIN_KEY,
                error_main_text=DEFAULT_ERROR_MAIN_TEXT,
            )
        return self[form_stash]


def form_validate(
    request,
    schema=None,
    form_stash=DEFAULT_FORM_STASH,
    form_stash_object=None,
    validate_post=True,
    validate_get=False,
    validate_params=None,
    variable_decode=False,
    dict_char=".",
    list_char="-",
    state=None,
    error_main_text=DEFAULT_ERROR_MAIN_TEXT,
    error_main_key=DEFAULT_ERROR_MAIN_KEY,
    error_string_key="Error_String",
    return_stash=True,
    raise_FormInvalid=None,
    raise_FormFieldInvalid=None,
    csrf_name="csrf_",
    csrf_token=None,
    is_unicode_params=None,
    foreach_defense=True,
):
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

    ``is_unicode_params`` (None)
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
                results = schema.to_python(decoded_params, state)
            except formencode.Invalid as e:
                errors = e.unpack_errors(variable_decode, dict_char, list_char)
                if isinstance(errors, six.string_types):
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

    except ValidationStop as e:
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
    request,
    form_print_method,
    form_stash=DEFAULT_FORM_STASH,
    render_view=None,
    render_view_template=None,
    auto_error_formatter=formatter_nobr,
    error_formatters=None,
    **htmlfill_kwargs
):
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
            # WSGIResponse's content may (unlikely) be unicode in Python2
            if six.PY2:
                if isinstance(form_content, six.text_type):  # PY2=unicode()
                    form_content = form_content.encode(encoding, response.errors)

            # FormEncode>=0.7 errors are unicode (due to being localized via ugettext). Convert any of the possible formencode unpack_errors formats to contain raw strings
            response.errors = encode_formencode_errors({}, encoding, response.errors)

    elif not isinstance(form_content, six.text_type):  # PY2=unicode()
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
        **_htmlfill_kwargs
    )
    response.text = form_content
    return response


def _form_cleanup(request):
    """
    make sure we close all fieldstorage objects
    """
    for _form in set(request.pyramid_formencode_classic.values()):
        for (k, v) in list(_form.results.items()):
            try:
                # don't compare to Boolean, as some Form objects can't handle that
                if isinstance(v, webob.compat.cgi_FieldStorage):
                    v.fp.close()
            except Exception as exc:
                pass


def _new_request_FormStashList(request):
    """
    This is a modern version of `init_request` from the .1 branch
    It is a memoized property via the pyramid `includeme` configuration hook
    This merely creates a new FormStashList object
    """
    if AUTOMATIC_CLEANUP:
        request.add_finished_callback(_form_cleanup)
    return FormStashList()


def includeme(config):
    """
    pyramid hook for setting up a form method via the configurator
    """
    config.add_request_method(
        _new_request_FormStashList, "pyramid_formencode_classic", reify=True
    )
