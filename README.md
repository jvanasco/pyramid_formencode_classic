![Python package](https://github.com/jvanasco/pyramid_formencode_classic/workflows/Python%20package/badge.svg)

`pyramid_formencode_classic` is a port of some classic `Pylons` form validation concepts onto the `Pyramid` framework.

## Installation

This requires the 2.0 branch of formencode.


### Versioning Policy

This project using a Semantic Versioning Policy: `Major.Minor.Patch`.

`Major`: significant API changes
`Minor`: backwards incompatible API changes
`Patch`: backwards compatible API changes and bugfixes

The recommended usage is to pin versioning within the `Major.Minor` range:

	pyramid_formencode_classic >=0.8.0, <0.9.0


## Debugtoolbar Support?

Yes. just add to your development.ini

	debugtoolbar.includes = pyramid_formencode_classic_.debugtoolbar

The debugtoolbar will now have a `FormencodeClassic` panel.

The panel shows information such as:

* which forms were processed/setup
* form results (errors, defaults, actual results)
* form schema
* form parsing status
* form configuration


### Why doesn't form_validate` raise an Exception by default?

This design choice was made to allow for flexible scoping by default

	try:
		(result, formStash) = form_validate(request, schema=Form_Email)
		if not result:
			raise FormInvalid(formStash)
	except FormInvalid as exc:
		# formStash is scoped here

The alternative is::

	try:
		(result, formStash) = form_validate(
		    request, schema=Form_Email, raise_FormInvalid=True
		)
	except FormInvalid as exc:
	    # formStash is an attribute of FormInvalid
		formStash = exc.formStash

Most implementations will want to define their own `form_validate()` function
that invokes `pyramid_formencode_classic.form_validate` with custom defaults, so
the default behavior is somewhat irrelevant. 
		

# Examples

## Usage Overview

### define your form

    import formencode

    class _Schema_Base(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False

    class FormLogin(_Schema_Base):
        email_address = formencode.validators.Email(not_empty=True)
        password = formencode.validators.UnicodeString(not_empty=True)
        remember_me = formencode.validators.Bool()


### define your view/handler

    import pyramid_formencode_classic as formhandling

    class WebLogin(base):

        def login(self):
            if 'login' in self.request.POST:
                return self._login_submit()
            return self._login_print()

        def _login_print(self):
            return render_to_response("web/account/login.mako", {}, self.request)

        def _login_submit(self):

            try:
                (result, formStash) = formhandling.form_validate(
                    self.request,
                    schema=forms.FormLogin,
                )
                if not result:
                    formStash.fatal_form("Invalid Form")

                results = formStash.results

                useraccount = model.find_user(results['email_address'])
                if not useraccount:
                	# set a custom error and raise an exception to reprint
                    # `formStash.fatal_field(` will raise `formhandling.FormInvalid(`
                    formStash.fatal_field(field="email_address",
										  message="Email not registered",
										  )

                if not useraccount.verify_submitted_password(results['password']):
                	# set a custom error and raise an exception to reprint
                    # `formStash.fatal_field(` will raise `formhandling.FormInvalid(`
                    formStash.fatal_field(
                        field="email_address",
                        message="Wrong password",
                    )

				do_login()
				return HTTPFound(location='/account/home')

            except formhandling.FormInvalid as exc:
                # our reprint logic
                return formhandling.form_reprint(
                    self.request,
                    self._login_print
                )


Bootstrap Example
=========================

    To handle bootstrap style errors, it's a bit more manual work -- but doable

        Mako:
            <% form= request.pyramid_formencode_classic.get_form() %>
            ${form.html_error_placeholder()|n}
            <div class="control-group ${form.css_error('email_address')}">
                <label class="control-label" for="email_address">Email</label>
                <input id="email_address" name="email_address" placeholder="Email Address" size="30" type="text" />
                ${form.html_error('email_address')|n}
            </div>

            you could also show an error with:
                % if form.has_error('email_address'):
                    <span class="help-inline">${form.get_error('email_address')}</span>
                % endif


        Pyramid:
            text = formhandling.form_reprint(self.request,
            								 self._login_print,
            								 auto_error_formatter=formhandling.formatter_none,
            								 )

    in the above example there are a few things to note:

        1. in the mako template we use `get_form` to pull/create the default formStash object for the request.  You can specify a specific formStash object if you'd like.
        2. a call is made to `form.css_error()` specifying the 'email_address' field.  this would result in the "control-group error" css mix if there is an error in 'email_address'.
        3. We tell pyramid to use 'formhandling.formatter_none' as the error formatter.  This surpresses errors.  We need to do that instead of using custom error formatters, because FormEncode places errors BEFORE the fields, not AFTER.
        4. I've included two methods of presenting field errors.  they are funtinoally the same.
        5. I've used an ErrorMain to show that there are issues on the form - not just a specific field.

