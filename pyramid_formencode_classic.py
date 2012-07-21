"""
v 0.0.11

a port of some classic pylons styling, but without much of the cruft that was not used often


This allows for a very particular coding style, which i prefer.

As you can see below, 'methods' are broken into multiple parts:

- a callable dispatcher ( login )
- a private printer ( _login_print )
- a private submit processor ( _login_submit )

The formencode schema does not interact with the database.  it is used entirely for "lightweight" validation and cheap operations ( length, presence, etc )

The more involved operations occur in the submit processor.

At any time, if an error is occured, a call to "form_reprint" can be made.  that function makes a subrequest and runs htmlfill on it.

Custom errors can be set as well.

If you want to set a "oh noes! message" for the form, pass in the `error_main` argument to validate, that will set an error in Error_Main , which will do one of two things:
a-  formencode.htmlfill will replace this marking in your template
        <form:error name="Error_Main"/>
    with the follwing :
        <span class="error-message">${error_main}</span><br/>

    caveat:
        <form:error name="Error_Main"/> will appear on valid documents , as htmlfill won't be called to strip it out
        if you want to strip it out, you could do the following :

            - pass your formStash into a template via the print mechanism
            - test for form validity in the form ; the FormStash class has an is_error attribute which is set True on errors ( and cleared when no errors exist )



b- if the marking is not in your template, it will be at the top of the document ( before the html ) as
    <!-- for: Error_Main -->
    <span class="error-message">${error_main}</span>

As with all formencode implementaitons, you can control where an error message appears by placing an explicit <form:error name="${formfield}"/>


there is a trivial attempt at multiple form handling - a "form_stash" argument can be used , which will store different "FormStash" wrapped structures in the names provided.

MAJOR CAVEATS
    1. it doesn't support using a "render" on the form object -- it expects forms to be manually coded , and errors to be regexed out via htmlfill. live with it.
    2. this REQUIRES one of the following two scenarios:
        a-  the form methods return a response object via "pyramid.renderers.render_to_response"

            your handlers would look like this

                def test(self):
                    if 'submit' in self.request.POST:
                        return self._test_submit()
                    return self._test_print()

                def _test_print(self):
                    return render_to_response( "/test_form.mako" , {"project":"MyApp"} , self.request)

                def _test_submit(self):
                    try:
                        ( result , formStash ) = formhandling.form_validate( self.request , schema=forms.FormLogin , error_main="Error")
                        if not result:
                            raise formhandling.FormInvalid()
                        userAccount= query_for_useraccount( formStash.results['email'] )
                        if not userAccount:
                            formStash.setError( section='email', message='Invalid' , raise_form_invalid=True )
                        ...
                    except formhandling.FormInvalid :
                        # you could set a field manually too
                        #formhandling.formerrors_set(self.request,section="field",message='missing this field')
                        return formhandling.form_reprint( self.request , self._login_print )

        b- you use an action decorator

            your handlers would look like this

                @action(renderer='/test_form.mako')
                def test(self):
                    if 'submit' in self.request.POST:
                        return self._test_submit()
                    return self._test_print()

                def _test_print(self):
                    return {"project":"MyApp"}

                def _test_submit(self):
                    try:
                        result = formhandling.form_validate( self.request , schema=forms.FormLogin , error_main="Error")
                        if not result:
                            raise formhandling.FormInvalid()
                        ...
                    except formhandling.FormInvalid :
                        # you could set a field manually too
                        #formhandling.formerrors_set(self.request,section="field",message='missing this field')
                        return formhandling.form_reprint( self.request , None , render_view=self._test_print , render_view_template="/test_form.mako" )


Needly to say: this is really nice and clean in the first scenario, and messy in the latter.


80% of this code is adapted from Pylons, 20% is outright copy/pasted.


define your form
=================

    import formencode

    class _Schema_Base(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False

    class FormLogin(_Schema_Base):
        email_address = formencode.validators.Email(not_empty=True)
        password = formencode.validators.UnicodeString(not_empty=True)
        remember_me = formencode.validators.Bool()


define your view/handler
========================

    import pyramid_formencode_classic as formhandling

    class WebLogin(base):

        def login(self):
            if 'login' in self.request.POST:
                return self._login_submit()
            return self._login_print()


        def _login_print(self):
            return render_to_response( "web/account/login.mako" , {"project":"MyApp" } , self.request)


        def _login_submit(self):

            try :
                if not formhandling.form_validate( self.request , schema=forms.FormLogin , error_main="OH NOES!" ):
                    raise formhandling.ValidationStop("Invalid Form")

                results= self.request.formStash.results

                useraccount = model.find_user( results['email_address'] )
                if not useraccount:
                    formhandling.formerrors_set(self.request,section="email_address",message="Email not registered")

                if not useraccount.verify_submitted_password( results['password'] ):
                    formhandling.formerrors_set(self.request,section="email_address",message="Wrong password")

            except formhandling.ValidationStop :
                formhandling.formerrors_set(self.request,section="Error_Main",message="There was an error with your form")
                return formhandling.form_reprint( self.request , self._login_print )

            except:
                raise

            # login via helper
            h.do_login()
            return HTTPFound(location='/account/home')


Twitter Bootstrap Example
=========================

    To handle  twitter bootstrap style errors, it's a bit more manual work -- but doable

        Mako:
            <% form= formhandling.get_form(request) %>
            ${form.htmlErrorMain('Error_Main')|n}
            <div class="control-group ${form.cssError('email_address')}">
                <label class="control-label" for="email_address">Email</label>
                <input id="email_address" name="email_address" placeholder="Email Address" size="30" type="text" />
                ${form.htmlError('email_address')|n}
            </div>

            you could also show an error with:
                % if form.hasError('email_address'):
                    <span class="help-inline">${form.getError('email_address')}</span>
                % endif



        Pyramid:
            text= formhandling.form_reprint( self.request , self._login_print , auto_error_formatter=formhandling.formatter_none )

    in the above example there are a few things to note:

        1. in the mako template we use `get_form` to pull/create the default formStash object for the request.  You can specify a specific formStash object if you'd like.
        2. a call is made to `form.cssError()` specifying the 'email_address' field.  this would result in the "control-group error" css mix if there is an error in 'email_address'.
        3. We tell pyramid to use 'formhandling.formatter_none' as the error formatter.  This surpresses errors.  We need to do that instead of using custom error formatters, because FormEncode places errors BEFORE the fields, not AFTER.
        4. I've included two methods of presenting field errors.  they are funtinoally the same.
        5. I've used an ErrorMain to show that there are issues on the form - not just a specific field.




released under the BSD license, as it incorporates some Pylons code (which was BSD)
"""
import logging
log = logging.getLogger(__name__)

import cgi
import formencode
import formencode.htmlfill
import sys
import types
from pyramid.response import Response as PyramidResponse
from pyramid.renderers import render as pyramid_render


class BaseException(Exception):
    """base exception class"""
    def __init__(self,message='',errors=None):
        self.message= message
        if errors:
            self.errors= errors
    def __str__(self):
        return repr(self.message)

class FormInvalid(BaseException):
    """Raise in your code when a form is invalid"""
    pass

class FieldInvalid(BaseException):
    """Raise in your code when a formfield is invalid"""
    pass

class ValidationStop(BaseException):
    """Stop validating"""
    pass


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



def formatter_help_inline(error):
    """
    Formatter that escapes the error, wraps the error in a span with
    class ``help-inline``, and doesn't add a ``<br>`` ; somewhat compatible with twitter's bootstrap
    """
    return '<span class="help-inline">%s</span>\n' % formencode.rewritingparser.html_quote(error)


def formatter_nobr(error):
    """
    Formatter that escapes the error, wraps the error in a span with
    class ``error-message``, and doesn't add a ``<br>``
    """
    return '<span class="error-message">%s</span>\n' % formencode.rewritingparser.html_quote(error)


def formatter_none(error):
    """
    Formatter that ignores the error.
    This is useful / necessary when handling custom css/html
    It outputs an html comment just so you don't go insane debugging.
    """
    return '<!-- formatter_none (%s)-->' % cgi.escape(error)

class FormStash( object ):
    """Wrapper object, stores all the vars and objects surrounding a form validation"""
    name= None
    is_error= None
    is_parsed= False
    is_unicode_params= False
    schema= None
    errors= None
    results= None
    defaults= None
    css_error= 'error'
    error_main_key= 'Error_Main'
    html_error_template= """<span class="help-inline">%(error)s</span>"""
    html_error_main_template = """<div class="alert alert-error"><div class="control-group error"><span class="help-inline"><i class="icon-exclamation-sign"></i> %(error)s</span></div></div>"""

    csrf_error_string = """We're worried about the security of your form submission. Please reload this page and try again. It would be best to highlight the URL in your web-browser and hit 'return'."""
    csrf_error_section = 'Error_Main'


    def __init__(self,error_main_key=None,name=None):
        self.errors= {}
        self.results= {}
        self.defaults= {}
        if error_main_key:
            self.error_main_key = error_main_key
        if name:
            self.name = name

    def set_css_error(self,css_error):
        """sets the css error field for the form"""
        self.css_error= css_error

    def set_html_error_template(self,html_error_template):
        """sets the html error template field for the form"""
        self.html_error_template = html_error_template

    def set_html_error_template(self,html_error_template):
        """sets the html error template MAIN field for the form.  useful for alerting the entire form is bad."""
        self.html_error_main_template = html_error_main_template

    def hasError(self,section):
        """Returns True or False if there is an error.  Does not return the value of the error field, because the value could be False."""
        if section in self.errors :
            return True
        return False

    def cssError(self,section,css_error=''):
        """Returns the css class if there is an error.  returns '' if there is not.  The default css_error is 'error' and can be set with `set_css_error`.  You can also overwrite with a `css_error` kwarg."""
        if section in self.errors :
            if css_error:
                return css_error
            return self.css_error
        return ''

    def htmlError( self,section,template=None):
        """Returns an HTML error formatted by a string template.  currently only provides for `%(error)s`"""
        if self.hasError(section):
            if template is None:
                template = self.html_error_template
            return template % { 'error': self.getError(section) }
        return ''

    def htmlErrorMain( self,section=None,template=None):
        """Returns an HTML error formatted by a string template.  currently only provides for `%(error)s`"""
        if section is None:
            section= self.error_main_key
        if self.hasError(section):
            if template is None:
                template = self.html_error_main_template
            return template % { 'error': self.getError(section) }
        return ''


    def getError(self,section):
        """Returns the error."""
        if section in self.errors :
            return self.errors[section]

    def setError( self, section=None , message="Error" , raise_form_invalid=False , raise_field_invalid=False ):
        """manages the dict of errors"""
        if section is None :
            section= self.error_main_key
        if message is None:
            if section in self.errors:
                del self.errors[section]
        else:
            self.errors[section]= message
        if self.errors:
            self.is_error = True
        if raise_form_invalid:
            raise FormInvalid()
        if raise_field_invalid:
            raise FieldInvalid()

    def clearError(self,section=None):
        """clear the dict of errors"""
        if self.errors :
            if section:
                if section in self.errors :
                   del self.errors['section']
            else:
                self.errors= {}
        if self.errors:
            self.is_error = True


    def csrf_input_field( self , id="csrf_" , name="csrf_", type="hidden" , csrf_token='' ):
        return """<input id="%(id)s" type="%(type)s" name="%(name)s" value="%(csrf_token)s" />""" % \
            {
                'id':id ,
                'name':name,
                'type':type,
                'csrf_token':csrf_token
             }



def get_form( request, form_stash='formStash' , error_main_key=None ):
    """helper function. to proxy FormStash object.  this is deprecated and just wrapping _form_ensure."""
    return _form_ensure( request , form_stash=form_stash , error_main_key=error_main_key )


def _form_ensure( request , form_stash='formStash' , error_main_key=None ):
    """helper function. ensures there is a FormStash instance attached to the request"""
    if not hasattr( request , form_stash ):
        setattr( request , form_stash , FormStash( name=form_stash , error_main_key=error_main_key ) )
    return getattr( request , form_stash )


def formerrors_set( request , form_stash='formStash' , section=None , message='There was an error with your submission...',raise_form_invalid=False,raise_field_invalid=False):
    """helper function. to proxy FormStash object"""
    form= _form_ensure( request , form_stash=form_stash )
    form.setError( section=section , message=message , raise_form_invalid=raise_form_invalid , raise_field_invalid=raise_field_invalid )


def formerrors_clear( request, form_stash='formStash' , section=None ):
    """helper function. to proxy FormStash object"""
    form= _form_ensure( request , form_stash=form_stash )
    form.clearError( section=section , message=message )

def form_validate(\
        request ,
        schema=None ,
        form_stash= 'formStash',
        form_stash_object= None,
        validate_post=True ,
        validate_get=False ,
        validate_params=None ,
        variable_decode=False ,
        dict_char='.' ,
        list_char='-'  ,
        state= None,
        error_main=None ,
        error_main_key='Error_Main',
        error_string_key='Error_String',
        return_stash= True ,
        raise_form_invalid = False ,
        raise_field_invalid = False ,
        csrf_name = 'csrf_',
        csrf_token = None
    ):
    """form validation only : returns True/False ; sets up Errors ;

    Validate input for a FormEncode schema.

    This is largely ported Pylons core, as is all of the docstring!

    Given a form schema, validate will attempt to validate the schema

    If validation was successful, the valid result dict will be saved as ``request.formResult.results``.

    .. warnings ::
            ``validate_post`` and ``validate_get`` applies to *where* the arguments to be
            validated come from. It does *not* restrict the form to
            only working with post, merely only checking POST vars.

            ``validate_params`` will exclude get and post data

    ``schema`` ( None )
        Refers to a FormEncode Schema object to use during validation.

    ``form_stash`` ( formStash )
        Name of the attribute formStash will be saved into.
        Useful if you have multiple forms.

    ``form_stash_object`` ( None )
        you can pass in a form stash object if you decided to subclass or alter FormStash

    ``validate_post`` ( True )
        Boolean that indicates whether or not POST variables
        should be included during validation.

    ``validate_get`` ( True )
        Boolean that indicates whether or not GET variables
        should be included during validation.

    ``validate_params``
        MultiDict of params if you want to validate by hand

    ``variable_decode`` ( False )
        Boolean to indicate whether FormEncode's variable decode
        function should be run on the form input before validation.

    ``dict_char`` ( '.' )
        Passed through to FormEncode. Toggles the form field naming
        scheme used to determine what is used to represent a dict. This
        option is only applicable when used with variable_decode=True.

    ``list_char`` ( '-' )
        Passed through to FormEncode. Toggles the form field naming
        scheme used to determine what is used to represent a list. This
        option is only applicable when used with variable_decode=True.

    ``state``
        Passed through to FormEncode for use in validators that utilize a state object.

    ``error_main_key`` ( 'Error_Main' )
        If there are any errors that occur, this will be the key they are dropped into.

    ``error_main`` ( None )
        If there are any errors that occur, this will drop an error in the key that corresponds to ``error_main_key``.

    ``error_string_key`` ( 'Error_String' )
        If there are is a string-based error that occurs, this will be the key they are dropped into.

    ``return_stash`` ( True )
        When set to True, returns a tuple of the status and the wrapped stash.  Otherwise just returns the status, and a separate call is needed to get the Stash.
        As True:
            ( status , stash )= form_validate()
        else:
            status = form_validate()

    """
    log.debug("form_validate - starting...")
    errors= {}
    if form_stash_object is None:
        formStash= FormStash( error_main_key=error_main_key , name=form_stash )
    else:
        formStash= form_stash_object
    formStash.schema= schema

    try:

        # if we don't pass in ``validate_params``...
        ## we must validate via GET, POST or BOTH
        if not validate_params:
            if validate_post and validate_get :
                validate_params = request.params
            elif validate_post and not validate_get :
                validate_params = request.POST
            elif not validate_post and validate_get :
                validate_params = request.GET

        validate_params = validate_params.mixed()

        if variable_decode :
            log.debug("form_validate - running variable_decode on params")
            decoded_params = formencode.variable_decode( validate_params , dict_char , list_char )
        else :
            decoded_params = validate_params

        # if there are no params to validate against, then just stop
        if not decoded_params:
            formStash.is_error= True
            raise ValidationStop()

        # initialize our results
        results= {}

        if schema:
            log.debug("form_validate - validating against a schema")
            try:
                results= schema.to_python( decoded_params , state )
            except formencode.Invalid, e:
                errors= e.unpack_errors( variable_decode , dict_char , list_char )
                if isinstance( errors , types.StringTypes ) :
                    errors= { error_string_key : errors }
            formStash.is_parsed= True

        formStash.results= results
        formStash.errors= errors
        formStash.defaults = decoded_params

        if errors:
            log.debug("form_validate - Errors found in validation")
            formStash.is_error= True
            if error_main:
                formStash.setError( section=formStash.error_main_key , message=error_main )

        else:
            if csrf_token is not None:
                if request.params.get(csrf_name) != csrf_token :
                    formStash.setError( section=formStash.csrf_error_section , message=formStash.csrf_error_string , raise_form_invalid=False , raise_field_invalid=False )


    except ValidationStop :
        log.debug("form_validate - encountered a ValidationStop")
        pass

    setattr( request , form_stash, formStash )

    if formStash.is_error:
        if raise_form_invalid:
            raise FormInvalid()
        if raise_field_invalid:
            raise FieldInvalid()

    if return_stash :
        return ( not formStash.is_error , formStash )
    return not formStash.is_error






def form_reprint( request , form_print_method , form_stash='formStash', render_view=None, render_view_template=None, auto_error_formatter=formatter_nobr , **htmlfill_kwargs ):
    """reprint a form
        args:
        ``request`` -- request instance
        ``form_print_method`` -- bound method to execute
        kwargs:
        ``frorm_stash`` (formStash) -- specify a stash
        ``auto_error_formatter`` (formatter_nobr) -- specify a formatter for rendering errors
            this is an htmlfill_kwargs , but we default to one without a br
        `**htmlfill_kwargs` -- passed on to htmlfill
    """
    log.debug("form_reprint - starting...")

    response= None
    if form_print_method:
        response= form_print_method()
    elif render_view and render_view_template:
        response= PyramidResponse(pyramid_render(render_view_template , render_view(), request=request))
    else:
       raise ValueError("invalid args submitted")


    # If the form_content is an exception response, return it
    # potential ways to check:
    ## hasattr( response, 'exception')
    ## resposne.code != 200
    ## repsonse.code == 302 <-- http found
    if hasattr(response, 'exception'):
        log.debug("form_reprint - response has exception, redirecting")
        return response

    formStash= getattr( request , form_stash )

    print formStash.__dict__
    #raise ValueError('ok')

    form_content= response.text

    # Ensure htmlfill can safely combine the form_content, params and
    # errors variables (that they're all of the same string type)
    if not formStash.is_unicode_params:
        log.debug("Raw string form params: ensuring the '%s' form and FormEncode errors are converted to raw strings for htmlfill", form_print_method )
        encoding= determine_response_charset(response)

        if hasattr( response , 'errors' ):
            # WSGIResponse's content may (unlikely) be unicode
            if isinstance(form_content, unicode):
                form_content= form_content.encode(encoding, response.errors)

            # FormEncode>=0.7 errors are unicode (due to being localized via ugettext). Convert any of the possible formencode unpack_errors formats to contain raw strings
            errors= encode_formencode_errors(errors, encoding, response.errors)

    elif not isinstance( form_content, unicode):
        log.debug("Unicode form params: ensuring the '%s' form is converted to unicode for htmlfill", form)
        encoding= determine_response_charset(response)
        form_content= form_content.decode(encoding)

    htmlfill_kwargs2 = htmlfill_kwargs.copy()
    htmlfill_kwargs2.setdefault('encoding', request.charset)
    form_content= formencode.htmlfill.render(\
            form_content,
            defaults=formStash.defaults,
            errors=formStash.errors,
            auto_error_formatter=auto_error_formatter,
            **htmlfill_kwargs2
    )
    response.text= form_content
    return response
    # comment out the above return , and raise a ValueError to debug the local environment with the Pyramid interactive tool
    raise ValueError('!!!')



