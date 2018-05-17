import logging
log = logging.getLogger(__name__)

# stdlib
import cgi
import pdb
import sys
import types


# pypi
import formencode
import formencode.htmlfill
from pyramid.response import Response as PyramidResponse
from pyramid.renderers import render as pyramid_render


# local
from .exceptions import *
from .formatters import *


# defaults
__VERSION__ = '0.1.10'

DEFAULT_FORM_STASH = '_default'

DEPRECATION_WARNING = False


def determine_response_charset(response):
    """FROM PYLONS -- Determine the charset of the specified Response object,
    returning the default system encoding when none is set"""
    charset = response.charset
    if charset is None:
        charset = sys.getdefaultencoding()
    log.debug("Determined result charset to be: %s", charset)
    return charset


def encode_formencode_errors(errors, encoding, encoding_errors='strict'):
    """FROM PYLONS -- Encode any unicode values contained in a FormEncode errors dict
    to raw strings of the specified encoding"""
    if errors is None or isinstance(errors, str):
        # None or Just incase this is FormEncode<=0.7
        pass
    elif isinstance(errors, unicode):
        errors = errors.encode(encoding, encoding_errors)
    elif isinstance(errors, dict):
        for key, value in errors.iteritems():
            errors[key] = encode_formencode_errors(value, encoding, encoding_errors)
    else:
        # Fallback to an iterable (a list)
        errors = [encode_formencode_errors(error, encoding, encoding_errors) for error in errors]
    return errors


class FormStash(object):
    """Wrapper object, stores all the vars and objects surrounding a form validation"""
    name = None
    is_error = None
    is_error_csrf = None
    is_parsed = False
    is_unicode_params = False
    schema = None
    errors = None
    results = None
    defaults = None
    css_error = 'error'
    error_main_key = 'Error_Main'
    html_error_template = """<span class="help-inline">%(error)s</span>"""
    html_error_main_template = """<div class="alert alert-error"><div class="control-group error"><span class="help-inline"><i class="icon-exclamation-sign"></i> %(error)s</span></div></div>"""

    csrf_error_string = """We're worried about the security of your form submission. Please reload this page and try again. It would be best to highlight the URL in your web-browser and hit 'return'."""
    csrf_error_field = csrf_error_section = 'Error_Main'

    def __init__(self, error_main_key=None, name=None, is_unicode_params=None):
        self.errors = {}
        self.results = {}
        self.defaults = {}
        if error_main_key:
            self.error_main_key = error_main_key
        if name:
            self.name = name
        self.is_unicode_params = is_unicode_params

    def set_css_error(self, css_error):
        """sets the css error field for the form"""
        self.css_error = css_error

    def set_html_error_template(self, html_error_template):
        """sets the html error template field for the form"""
        self.html_error_template = html_error_template

    def set_html_error_main_template(self, html_error_main_template):
        """sets the html error template MAIN field for the form.  useful for alerting the entire form is bad."""
        self.html_error_main_template = html_error_main_template

    def has_error(self, field):
        """Returns True or False if there is an error in `field`.  Does not return the value of the error field, because the value could be False."""
        if field in self.errors:
            return True
        return False

    def has_errors(self):
        """Returns True or False if there is are errors."""
        if self.errors:
            return True
        return False

    def css_error(self, field, css_error=''):
        """Returns the css class if there is an error.  returns '' if there is not.  The default css_error is 'error' and can be set with `set_css_error`.  You can also overwrite with a `css_error` kwarg."""
        if field in self.errors:
            if css_error:
                return css_error
            return self.css_error
        return ''

    def html_error(self, field, template=None):
        """Returns an HTML error formatted by a string template.  currently only provides for `%(error)s`"""
        if self.has_error(field):
            if template is None:
                template = self.html_error_template
            return template % {'error': self.get_error(field)}
        return ''
    
    def html_error_main_fillable(self, field=None):
        """If there are errors, returns a hidden input field for `Error_Main` or `field`.
           otherwise, returns an empty string.
           the htmlfill parser will update the hidden field to the template.
        """
        if field is None:
            field = self.error_main_key
        if self.has_errors():
            return '<input type="hidden" name="%s" />' % field
        return ''

    def html_error_main(self, field=None, template=None, section=None):
        """Returns an HTML error formatted by a string template.  currently only provides for `%(error)s`"""
        if (section is not None) and (field is None):
            log.debug("FormStash - `section` is being deprecated for `field`")
            field = section
        error = None
        # look in the main error field specifically
        if field is None:
            field = self.error_main_key
        if self.has_errors():
            if self.has_error(field):
                error = self.get_error(field)
            else:
                error = "There was an error with your submission."
            if template is None:
                template = self.html_error_main_template
            return template % {'error': error}
        return ''

    def get_error(self, field):
        """Returns the error."""
        if field in self.errors:
            return self.errors[field]

    def set_error(self,
                  field = None,
                  message = "Error",
                  raise_form_invalid = None,
                  raise_field_invalid = None,
                  message_append = False,
                  message_prepend = False,
                  is_error_csrf = None,
                  section = None,  # this is being deprecated out
                  raise_FormInvalid = None,
                  raise_FieldInvalid = None,
                  ):
        """manages the dict of errors

            `field`: the field in the form
            `message`: your error message
            `raise_form_invalid`: default `False`. if `True` will raise `FormInvalid`
            `raise_field_invalid`: default `False`. if `True` will raise `FieldInvalid`
            `message_append`: default `False`.  if true, will append the `message` argument to any existing argument in this `field`
            `message_prepend`: default `False`.  if true, will prepend the `message` argument to any existing argument in this `field`

            meessage_append and message_prepend allow you to elegantly combine errors

            consider this code:

                try:
                    except CaughtError, e:
                        formStash.set_error(message="We encountered a `CaughtError`", raise_form_invalid=True)
                    ...
                except formhandling.FormInvalid:
                    formStash.set_error(field='Error_Main', message="There was an error with your form.", message_prepend=True)
                    return formhandling.form_reprint(...)

            This would generate the following text for the `Error_Main` field:

                There was an error with your form.  We encountered a `CaughtError`
        """
        if (section is not None) and (field is None):
            log.debug("FormStash - `section` is being deprecated for `field`")
            field = section
        if field is None:
            field = self.error_main_key
        if message is None:
            if field in self.errors:
                del self.errors[field]
        else:
            if message_append and message_prepend:
                raise ValueError("You can not set both `message_append` `message_prepend`")
            if message_append or message_prepend:
                _message_existing = self.errors[field] if (field in self.errors) else ''
                if message_append:
                    message = _message_existing + ' ' + message
                elif message_prepend:
                    message = message + ' ' + _message_existing
            self.errors[field] = message
            if is_error_csrf:
                self.is_error_csrf = True
        if self.errors:
            self.is_error = True

        # deprecation helpers
        if (raise_form_invalid is not None) or (raise_field_invalid is not None):
            log.debug("FormStash - `raise_form_invalid` is being deprecated to `raise_FormInvalid`; `raise_field_invalid` is being deprecated to `raise_FieldInvalid`.")
        if raise_FormInvalid is None:
            raise_FormInvalid = raise_form_invalid
        if raise_FieldInvalid is None:
            raise_FieldInvalid = raise_field_invalid

        if raise_FormInvalid:
            raise FormInvalid()
        if raise_FieldInvalid:
            raise FieldInvalid()

    def clear_error(self, field=None, section=None):
        """clear the dict of errors"""
        if (section is not None) and (field is None):
            log.debug("FormStash - `section` is being deprecated for `field`")
            field = section
        if self.errors:
            if field:
                if field in self.errors:
                    del self.errors[field]
            else:
                self.errors = {}
        if self.errors:
            self.is_error = True

    def csrf_input_field(self, id="csrf_", name="csrf_", type="hidden", csrf_token='', htmlfill_ignore=True):
        return """<input id="%(id)s" type="%(type)s" name="%(name)s" value="%(csrf_token)s"%(htmlfill_ignore)s/>""" % \
            {
                'id': id,
                'name': name,
                'type': type,
                'csrf_token': csrf_token,
                'htmlfill_ignore': " data-formencode-ignore='1' " if htmlfill_ignore else '',
            }

    # --------------------------------------------------------------------------
    # deprecation support

    def hasError(self, field):
        if DEPRECATION_WARNING:
            log.debug("`hasError` is being deprecated to `has_error`")
        return self.has_error(field)

    def cssError(self, section, css_error=''):
        if DEPRECATION_WARNING:
            log.debug("`cssError` is being deprecated to `css_error`")
        return self.css_error(section, css_error=css_error)

    def htmlError(self, section, template=None):
        if DEPRECATION_WARNING:
            log.debug("`htmlError` is being deprecated to `html_error`")
        return self.html_error(section, template=template)

    def htmlErrorMain(self, section=None, template=None):
        if DEPRECATION_WARNING:
            log.debug("`htmlErrorMain` is being deprecated to `html_error_main`")
        return self.html_error_main(section=section, template=template)

    def getError(self, section):
        if DEPRECATION_WARNING:
            log.debug("`getError` is being deprecated to `get_error`")
        return self.get_error(section)

    def setError(self,
                 section = None,
                 message = "Error",
                 raise_form_invalid = None,
                 raise_field_invalid = None,
                 is_error_csrf = None,
                 ):
        if DEPRECATION_WARNING:
            log.debug("`setError` is being deprecated to `set_error`")
        return self.set_error(section = section,
                              message = message,
                              raise_form_invalid = raise_form_invalid,
                              raise_field_invalid = raise_field_invalid,
                              is_error_csrf = is_error_csrf,
                              )

    def clearError(self, section=None):
        if DEPRECATION_WARNING:
            log.debug("`clearError` is being deprecated to `clear_error`")
        return self.clear_error(section=section)


class FormStashList(dict):
    """dict for holding `FormStash`"""
    pass


def init_request(request):
    """helper function. ensures there is a `pyramid_formencode_classic` dict on the request"""
    if not hasattr(request, 'pyramid_formencode_classic'):
        setattr(request, 'pyramid_formencode_classic', FormStashList())


def set_form(request, form_stash=DEFAULT_FORM_STASH, formObject=None):
    init_request(request)
    request.pyramid_formencode_classic[form_stash] = formObject


def get_form(request, form_stash=DEFAULT_FORM_STASH, error_main_key=None):
    """DEPRECATED.  helper function. to proxy FormStash object.  this is just wrapping _form_ensure."""
    return _form_ensure(request, form_stash=form_stash, error_main_key=error_main_key)


def _form_ensure(request, form_stash=DEFAULT_FORM_STASH, error_main_key=None):
    """helper function. ensures there is a FormStash instance attached to the request"""
    init_request(request)
    if form_stash not in request.pyramid_formencode_classic:
        request.pyramid_formencode_classic[form_stash] = FormStash(name=form_stash, error_main_key=error_main_key)
    return request.pyramid_formencode_classic[form_stash]


def formerrors_set(request, form_stash=DEFAULT_FORM_STASH, field=None, message='There was an error with your submission...', raise_form_invalid=None, raise_field_invalid=None, section=None, ):
    """helper function. to proxy FormStash object"""
    if (section is not None) and (field is None):
        log.debug("FormStash - `section` is being deprecated for `field`")
        field = section
    form = _form_ensure(request, form_stash=form_stash)
    form.set_error(section=section, message=message, raise_form_invalid=raise_form_invalid, raise_field_invalid=raise_field_invalid)


def formerrors_clear(request, form_stash=DEFAULT_FORM_STASH, field=None, section=None):
    """helper function. to proxy FormStash object"""
    if (section is not None) and (field is None):
        log.debug("FormStash - `section` is being deprecated for `field`")
        field = section
    form = _form_ensure(request, form_stash=form_stash)
    form.clear_error(section=section)


def form_validate(
    request,
    schema=None,
    form_stash= DEFAULT_FORM_STASH,
    form_stash_object= None,
    validate_post=True,
    validate_get=False,
    validate_params=None,
    variable_decode=False,
    dict_char='.',
    list_char='-',
    state= None,
    error_main=None,
    error_main_key='Error_Main',
    error_string_key='Error_String',
    return_stash= True,
    raise_form_invalid = None,
    raise_field_invalid = None,
    raise_FormInvalid = None,
    raise_FieldInvalid = None,
    csrf_name = 'csrf_',
    csrf_token = None,
    is_unicode_params=None,
):
    """form validation only: returns True/False ; sets up Errors ;

    Validate input for a FormEncode schema.

    This is largely ported Pylons core, as is all of the docstring!

    Given a form schema, validate will attempt to validate the schema

    If validation was successful, the valid result dict will be saved as ``request.formResult.results``.

    .. warnings::
            ``validate_post`` and ``validate_get`` applies to *where* the arguments to be
            validated come from. It does *not* restrict the form to
            only working with post, merely only checking POST vars.

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

    ``error_main`` (None)
        If there are any errors that occur, this will drop an error in the key that corresponds to ``error_main_key``.

    ``error_string_key`` ('Error_String')
        If there are is a string-based error that occurs, this will be the key they are dropped into.

    ``return_stash`` (True)
        When set to True, returns a tuple of the status and the wrapped stash.  Otherwise just returns the status, and a separate call is needed to get the Stash.
        As True:
            (status, stash)= form_validate()
        else:
            status = form_validate()

    ``is_unicode_params`` (None)
        passthrough to new `Form`

    """
    log.debug("form_validate - starting...")
    errors = {}
    if form_stash_object is None:
        formStash = FormStash(error_main_key=error_main_key,
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
                formStash.set_error(field=formStash.error_main_key, message="Nothing submitted.")
                raise ValidationStop('no `validate_params`')

        validate_params = validate_params.mixed()

        if variable_decode:
            log.debug("form_validate - running variable_decode on params")
            decoded_params = formencode.variabledecode.variable_decode(validate_params, dict_char, list_char)
        else:
            decoded_params = validate_params

        # if there are no params to validate against, then just stop
        if not decoded_params:
            formStash.set_error(field=formStash.error_main_key, message="Nothing submitted.")
            raise ValidationStop('no `decoded_params`')

        # initialize our results
        results = {}

        if schema:
            log.debug("form_validate - validating against a schema")
            try:
                results = schema.to_python(decoded_params, state)
            except formencode.Invalid, e:
                errors = e.unpack_errors(variable_decode, dict_char, list_char)
                if isinstance(errors, types.StringTypes):
                    errors = {error_string_key: errors}
            formStash.is_parsed = True

        formStash.results = results
        formStash.errors = errors
        formStash.defaults = decoded_params

        if errors:
            log.debug("form_validate - Errors found in validation")
            formStash.is_error = True
            if error_main:
                # don't raise an error, because we have to stash the form
                formStash.set_error(field=formStash.error_main_key,
                                    message=error_main,
                                    raise_FormInvalid=False,
                                    raise_FieldInvalid=False,
                                    )

        else:
            if csrf_token is not None:
                if request.params.get(csrf_name) != csrf_token:
                    # don't raise an error, because we have to stash the form
                    formStash.set_error(field = formStash.csrf_error_field,
                                        message = formStash.csrf_error_string,
                                        raise_FormInvalid = False,
                                        raise_FieldInvalid = False,
                                        is_error_csrf = True,
                                        )

    except ValidationStop, e:
        log.debug("form_validate - encountered a ValidationStop")
        pass
        
    # save the form onto the request
    set_form(request, form_stash=form_stash, formObject=formStash)

    if formStash.is_error:

        # deprecation helpers
        if (raise_form_invalid is not None) or (raise_field_invalid is not None):
            log.debug("FormStash - `raise_form_invalid` is being deprecated to `raise_FormInvalid`; `raise_field_invalid` is being deprecated to `raise_FieldInvalid`.")
        if raise_FormInvalid is None:
            raise_FormInvalid = raise_form_invalid
        if raise_FieldInvalid is None:
            raise_FieldInvalid = raise_field_invalid

        # now raise
        if raise_FormInvalid:
            raise FormInvalid()
        if raise_FieldInvalid:
            raise FieldInvalid()

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
    **htmlfill_kwargs
):
    """reprint a form
        args:
        ``request`` -- request instance
        ``form_print_method`` -- bound method to execute
        kwargs:
        ``frorm_stash`` (pyramid_formencode_classic.DEFAULT_FORM_STASH = _default) -- specify a stash
        ``auto_error_formatter`` (formatter_nobr) -- specify a formatter for rendering errors
            this is an htmlfill_kwargs, but we default to one without a br
        `**htmlfill_kwargs` -- passed on to htmlfill
    """
    log.debug("form_reprint - starting...")

    response = None
    if form_print_method:
        response = form_print_method()
    elif render_view and render_view_template:
        response = PyramidResponse(pyramid_render(render_view_template, render_view(), request=request))
    else:
        raise ValueError("invalid args submitted")

    # If the form_content is an exception response, return it
    # potential ways to check:
    # # hasattr(response, 'exception')
    # # resposne.code != 200
    # # repsonse.code == 302 <-- http found
    if hasattr(response, 'exception'):
        log.debug("form_reprint - response has exception, redirecting")
        return response

    formStash = get_form(request, form_stash=form_stash)

    form_content = response.text

    # Ensure htmlfill can safely combine the form_content, params and
    # errors variables (that they're all of the same string type)
    if not formStash.is_unicode_params:
        log.debug("Raw string form params: ensuring the '%s' form and FormEncode errors are converted to raw strings for htmlfill", form_print_method)
        encoding = determine_response_charset(response)

        if hasattr(response, 'errors'):
            # WSGIResponse's content may (unlikely) be unicode
            if isinstance(form_content, unicode):
                form_content = form_content.encode(encoding, response.errors)

            # FormEncode>=0.7 errors are unicode (due to being localized via ugettext). Convert any of the possible formencode unpack_errors formats to contain raw strings
            response.errors = encode_formencode_errors({}, encoding, response.errors)

    elif not isinstance(form_content, unicode):
        log.debug("Unicode form params: ensuring the '%s' form is converted to unicode for htmlfill", formStash)
        encoding = determine_response_charset(response)
        form_content = form_content.decode(encoding)

    htmlfill_kwargs2 = htmlfill_kwargs.copy()
    htmlfill_kwargs2.setdefault('encoding', request.charset)
    form_content = formencode.htmlfill.render(
        form_content,
        defaults = formStash.defaults,
        errors = formStash.errors,
        auto_error_formatter = auto_error_formatter,
        **htmlfill_kwargs2
    )
    response.text = form_content
    return response
