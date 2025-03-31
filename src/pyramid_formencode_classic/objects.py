# stdlib
import logging
from typing import Dict
from typing import Iterable
from typing import List
from typing import NoReturn
from typing import Optional
from typing import TYPE_CHECKING

# local
from . import _defaults
from ._utils import TYPES_ERRORS
from .exceptions import FormInvalid

if TYPE_CHECKING:
    from formencode import Schema

# ==============================================================================

log = logging.getLogger(__name__)

# ------------------------------------------------------------------------------


class FormStash(object):
    """Wrapper object, stores all the vars and objects surrounding a form validation"""

    schema: "Schema"
    name: str
    error_main_key: str
    error_main_text: str
    is_error: bool = False
    is_error_csrf: bool = False
    is_parsed: bool = False
    is_unicode_params: bool = False
    is_submitted_vars: Optional[bool] = None
    nothing_submitted_error_text: Optional[str] = None
    errors: Dict[str, str]
    results: Dict[str, str]
    defaults: Dict[str, str]

    # protected attribute; use property to access
    _css_error: str = "error"

    html_error_placeholder_template: str = '<form:error name="%s"/>'
    html_error_placeholder_form_template: str = (
        '<form:error name="%(field)s" data-formencode-form="%(form)s"/>'
    )
    html_error_template: str = """<span class="help-inline">%(error)s</span>"""
    html_error_main_template: str = (
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

    _reprints: Iterable  # internal use for debugging
    _exceptions_integrated: Optional[List] = None

    def __init__(
        self,
        schema: "Schema",
        name: Optional[str] = None,
        error_main_key: Optional[str] = None,
        error_main_text: Optional[str] = None,
        is_unicode_params: bool = False,
    ):
        self.schema = schema
        if name:
            self.name = name
        self.errors = {}
        self.results = {}
        self.defaults = {}

        if error_main_key is None:
            error_main_key = _defaults.DEFAULT_ERROR_MAIN_KEY  # "Error_Main"
        self.error_main_key = error_main_key

        if error_main_text is None:
            error_main_text = (
                _defaults.DEFAULT_ERROR_MAIN_TEXT
            )  # "There was an error with your form submission."
        self.error_main_text = error_main_text

        self.is_unicode_params = is_unicode_params
        self._reprints = []

    def set_css_error(self, css_error: str) -> None:
        """sets the css error field for the form"""
        self._css_error = css_error

    def set_html_error_placeholder_template(self, template: str) -> None:
        """
        sets the html error template field for the form
        for example:
            <form:error name="%s"/>
        """
        self.html_error_placeholder_template = template

    def set_html_error_placeholder_form_template(self, template: str) -> None:
        """
        sets the html error template field for the form when data-formencode-form
        is needed

        for example:
            <form:error name="%(field)s" data-formencode-form="%(form)s"/>
        """
        self.html_error_placeholder_form_template = template

    def set_html_error_template(self, template: str) -> None:
        """sets the html error template field for the form"""
        self.html_error_template = template

    def set_html_error_main_template(self, template: str) -> None:
        """sets the html error template MAIN field for the form.
        useful for alerting the entire form is bad."""
        self.html_error_main_template = template

    def has_error(self, field: str) -> bool:
        """Returns True or False if there is an error in `field`.
        Does not return the value of the error field, because the value could be False.
        """
        if field in self.errors:
            return True
        return False

    def has_errors(self) -> bool:
        """Returns True or False if there is are errors."""
        if self.errors:
            return True
        return False

    def css_error(
        self,
        field: str,
        css_error: Optional[str] = None,
    ) -> str:
        """Returns the css error class if there is an error; Returns '' if there is not.

        The default css_error is 'error' and can be set with `set_css_error`.
        You can also overwrite with a `css_error` kwarg."""
        if field in self.errors:
            if css_error:
                return css_error
            return self._css_error
        return ""

    def html_error(
        self,
        field: str,
        template: Optional[str] = None,
    ) -> str:
        """Returns an HTML error formatted by a string template.
        Currently only provides for `%(error)s`"""
        if self.has_error(field):
            if template is None:
                template = self.html_error_template
            return template % {"error": self.get_error(field)}
        return ""

    def html_error_placeholder(
        self,
        field: Optional[str] = None,
        formencode_form: Optional[str] = None,
    ) -> str:
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
        :param field: the field of the error. will default to `self.error_main_key`
        :formencode_form: the name of the form.
            used to discriminate when multiple forms are on a page
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

    def render_html_error_main(
        self,
        field: Optional[str] = None,
        template: Optional[str] = None,
    ) -> str:
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

    def get_error(self, field: str) -> Optional[TYPES_ERRORS]:
        """Returns the error."""
        if field in self.errors:
            return self.errors[field]
        return None

    def set_error_nothing_submitted(self):
        log.debug("`FormStash.set_error_nothing_submitted`")
        self.is_submitted_vars = False
        self.nothing_submitted_error_text = _defaults.DEFAULT_ERROR_NOTHING_SUBMITTED
        self.set_error(
            field=self.error_main_key,
            message=_defaults.DEFAULT_ERROR_NOTHING_SUBMITTED,
        )

    def set_error(
        self,
        field: Optional[str] = None,
        message: Optional[str] = "Error",
        message_overwrite: bool = False,
        message_append: bool = False,
        message_prepend: bool = False,
        error_main: Optional[str] = None,
        is_error_csrf: Optional[bool] = None,
    ) -> None:
        """
        Manages entries in the dict of errors

        As of v0.4.0, this will NOT raise an exception

        `field`: the field in the form
        `message`: your error message
        `message_append`: default `False`.
                          If `True`, will append the `message` argument to any existing argument in this `field`
        `message_prepend`: default `False`.
                           If `True`, will prepend the `message` argument to any existing argument in this `field`

        ``meessage_append` and ``message_prepend``` allow you to elegantly combine errors
        """
        log.debug("`FormStash.set_error`")
        log.debug(locals())

        if field is None:
            field = self.error_main_key

        _error_main_text = self.error_main_text

        # pass 1 - "'Nothing submitted.'"

        if not message:  # None or ''
            raise ValueError(
                "no `message` provided. use `.clear_error` to remove an error."
            )

        if message_overwrite and (message_append or message_prepend):
            raise ValueError(
                "You can not set both `message_overwrite` with `message_append` or `message_prepend`"
            )

        if message_append and message_prepend:
            raise ValueError("You can not set both `message_append` `message_prepend`")

        _message_existing = self.errors[field] if (field in self.errors) else None
        if _message_existing and not message_overwrite:
            if field == self.error_main_key:
                if not message_append and not message_prepend:
                    if _message_existing == _error_main_text:
                        message_append = True
                        message_prepend = False
                    else:
                        message_append = False
                        message_prepend = True

            if not _message_existing and (field == self.error_main_key):
                _message_existing = error_main or _error_main_text

            if self.is_submitted_vars is False:
                if _message_existing == self.nothing_submitted_error_text:
                    message_append = False
                    message_prepend = True

            if message_append or message_prepend:

                if _message_existing != message:  # don't duplicate the error
                    _msgs = [_message_existing] if _message_existing else []
                    if message_append:
                        if not _msgs[0].endswith(message):
                            _msgs.append(message)
                    elif message_prepend:
                        if not _msgs[0].startswith(message):
                            _msgs.insert(0, message)
                    message = " ".join(_msgs)

        self.errors[field] = message

        # mark the form as invalid
        self.is_error = True

        # set the main error if needed
        if self.error_main_key not in self.errors:
            self.errors[self.error_main_key] = error_main or _error_main_text

        if is_error_csrf:
            self.is_error_csrf = True

    def clear_error(
        self,
        field: Optional[str] = None,
    ) -> None:
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

    def fatal_form(
        self,
        error_main: Optional[str] = None,
        message_overwrite: bool = True,
        message_append: bool = False,
        message_prepend: bool = False,
    ) -> NoReturn:
        """
        Sets an error for the main error key, then raises a `FormInvalid`.

        `message_append`: default `False`.
                          If `True`, will append the `message` argument to any existing argument in the `self.error_main_key` field
        `message_prepend`: default `False`.
                           If `True`, will prepend the `message` argument to any existing argument in the `self.error_main_key` field
        """
        log.debug("`FormStash.fatal_form`")
        log.debug(locals())

        if error_main is None:
            error_main = _defaults.DEFAULT_ERROR_MAIN_TEXT

        _kwargs = {}
        if message_overwrite is not None:
            _kwargs["message_overwrite"] = message_overwrite
        if message_append is not None:
            _kwargs["message_append"] = message_append
        if message_prepend is not None:
            _kwargs["message_prepend"] = message_prepend
        self.set_error(
            field=self.error_main_key,
            message=error_main,
            error_main=error_main,
            **_kwargs,
        )
        self._raise_unique_FormInvalid(
            error_main=error_main,
            error_main_overwrite=message_overwrite,
            error_main_append=message_append,
            error_main_prepend=message_prepend,
            raised_by="fatal_form",
        )

    def fatal_field(
        self,
        field: str,
        error_field: Optional[str] = None,
        error_main: Optional[str] = None,
        message_overwrite: bool = False,
        message_append: bool = True,  # don't overwrite a formencode error here
        message_prepend: bool = False,
        allow_unknown_fields: bool = False,
    ) -> NoReturn:
        """
        Sets an error for ``field``, then raises a `FormInvalid`.

        `message_append`: default `True`.
                          If `True`, will append the `message` argument to any existing argument in the `self.error_main_key` field.

        `message_prepend`: default `False`.
                           If `True`, will prepend the `message` argument to any existing argument in the `self.error_main_key` field

        consider this code:

            try:
                except CaughtError as e:
                    formStash.set_error(message="We encountered a `CaughtError`",
                                        )
                ...
            except formhandling.FormInvalid as exc:
                formStash.set_error(field='Error_Main',
                                    error_field="There was an error with your form.",
                                    message_prepend=True,
                                    )
                return formhandling.form_reprint(...)

        This would generate the following text for the `Error_Main` field:

            There was an error with your form.  We encountered a `CaughtError`

        """
        log.debug("`FormStash.fatal_field`")
        log.debug(locals())

        if not field:
            raise ValueError("field `%s` must be provided" % field)
        if field not in self.schema.fields:
            if not allow_unknown_fields:
                raise ValueError(
                    "field `%s` is not in schema: `%s`" % (field, self.schema)
                )
        if not error_field:
            error_field = _defaults.DEFAULT_ERROR_FIELD_TEXT
        _kwargs = {}
        if message_overwrite is not None:
            _kwargs["message_overwrite"] = message_overwrite
        if message_append is not None:
            _kwargs["message_append"] = message_append
        if message_prepend is not None:
            _kwargs["message_prepend"] = message_prepend
        self.set_error(
            field=field, message=error_field, error_main=error_main, **_kwargs
        )
        self._raise_unique_FormInvalid(
            error_main=error_main,
            error_main_overwrite=message_overwrite,
            error_main_append=message_append,
            error_main_prepend=message_prepend,
            raised_by="fatal_field",
        )

    def _raise_unique_FormInvalid(
        self,
        error_main: Optional[str] = None,
        error_main_overwrite: bool = False,
        error_main_append: bool = True,
        error_main_prepend: bool = False,
        raised_by: Optional[str] = None,
    ) -> NoReturn:
        """
        this is used to defend against integrating an exception multiple times
        via `register_error_main_exception` after being created in
        `fatal_form` or `fatal_field`.
        """
        _FormInvalid = FormInvalid(
            self,
            error_main=error_main,
            error_main_overwrite=error_main_overwrite,
            error_main_append=error_main_append,
            error_main_prepend=error_main_prepend,
            raised_by=raised_by,
        )
        if self._exceptions_integrated is None:
            self._exceptions_integrated = []
        self._exceptions_integrated.append(_FormInvalid)
        raise _FormInvalid

    def register_error_main_exception(
        self,
        exc: FormInvalid,
        error_main_overwrite: bool = False,
        error_main_append: bool = False,
        error_main_prepend: bool = False,
    ) -> None:
        """
        This is a convenience method to replace this common use pattern:
        ------------------------------------------------------------------------
            try:
                ...
                raise formhandling.FormInvalid(formStash, 'foo')
                ...
            except formhandling.FormInvalid as exc:
                - if exc.message:
                -     formStash.set_error(
                -         field=formStash.error_main_key,
                -         message=exc.message,
                -         error_main_prepend=True,
                -         )
                + formStash.register_error_main_exception(
                +     exc,
                +     error_main_prepend=True,
                + )
                return formhandling.form_reprint(
                    self.request,
                    self._print_form,
                )
        ------------------------------------------------------------------------
        """
        if isinstance(exc, FormInvalid):
            if self._exceptions_integrated is None:
                self._exceptions_integrated = []

            if exc in self._exceptions_integrated:
                log.debug(
                    "`FormStash.register_error_main_exception`: exception already integrated"
                )
            else:
                log.debug(
                    "`FormStash.register_error_main_exception`: integrating exception"
                )
                self._exceptions_integrated.append(exc)
                if exc.error_main:
                    log.debug(
                        "`FormStash.register_error_main_exception`: invoking `set_error`"
                    )
                    log.debug(locals())
                    self.set_error(
                        field=self.error_main_key,
                        message=exc.error_main,
                        message_overwrite=error_main_overwrite,
                        message_append=error_main_append,
                        message_prepend=error_main_prepend,
                    )

    def csrf_input_field(
        self,
        id: str = "csrf_",
        name: str = "csrf_",
        type: str = "hidden",
        csrf_token: str = "",
        htmlfill_ignore: bool = True,
    ) -> str:
        return (
            """<input id="%(id)s" type="%(type)s" name="%(name)s" value="%(csrf_token)s"%(htmlfill_ignore)s/>"""
            % {
                "id": id,
                "name": name,
                "type": type,
                "csrf_token": csrf_token,
                "htmlfill_ignore": (
                    " data-formencode-ignore='1' " if htmlfill_ignore else ""
                ),
            }
        )


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
        form_stash: str = _defaults.DEFAULT_FORM_STASH,
        schema: Optional["Schema"] = None,
        error_main_key: str = _defaults.DEFAULT_ERROR_MAIN_KEY,
        error_main_text: str = _defaults.DEFAULT_ERROR_MAIN_TEXT,
        is_unicode_params: bool = False,
    ) -> FormStash:
        if form_stash not in self:
            self[form_stash] = FormStash(
                schema=schema,
                name=form_stash,
                error_main_key=error_main_key,
                error_main_text=error_main_text,
                is_unicode_params=is_unicode_params,
            )
        return self[form_stash]
