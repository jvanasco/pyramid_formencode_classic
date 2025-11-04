![Python package](https://github.com/jvanasco/pyramid_formencode_classic/workflows/Python%20package/badge.svg)

`pyramid_formencode_classic` is a port of some classic `Pylons` form validation concepts onto the `Pyramid` framework.

The package automates validation of `.formencode.Schema` objects under Pyramid, and offers its own `FormStash` object to manage the validation results.

## Lighweight Validation

Formencode validators offer lightweight validation.  They essentially check to see if submitted data matches certain formats, regexes and options.  They can be chained together for complex tasks, however they do not do advanced validation: they can be used to determine if a login/password meet required input characteristics, but do not check to see if this information is in the database or not.

To handle complex situations, this package offers a FormStash object that can be used to persist data around business logic

## The FormStash object

A `FormStash` object is created when validating a form and used to manage the results.

There are several key attributes:

* `FormStash.results` - a dict of successfully validated field values
* `FormStash.errors` - a dict of fields that failed validation, along with the errors
* `FormStash.defaults` - a dict of containing the pre-validated form data, which is used as the defaults when rendering the form.

There are several helpful utility functions that can be used to check the validation state:

* `FormStash.set_error`
* `FormStash.get_error`
* `FormStash.has_errors`

And there are several functions that can be used to Fail validation after processing:

* `FormStash.fatal_form`
* `FormStash.fatal_field`


## Advanced (Common) Usage

Here is an example of validating a form with advanced logic:

	try:
		(result, formStash) = form_validate(
		    request, schema=Form_Login, raise_FormInvalid=True
		)
		dbUser = ctx.load_user(
		    username=formStash.results["username"],
		    raw_password_=formStash.results["password"],
		)
		if not dbUser:
		    # fatal_form and fatal_field will both raise a FormInvlalid
		    #     formStash.fatal_form("Invalid Credentials")
		    # or ...
		    formStash.fatal_field(field="password, error_field=""Password invalid.")
	except FormInvalid as exc:
	    # formStash is an attribute of FormInvalid
		formStash = exc.formStash


## Installation

This requires the 2.0 branch of formencode.


### Current Version(s)

Version 0.8.0 is current and recommended.  It has major breaking changes against earlier versions.  The API has slightly changed but should be easy to adapt.

Version 0.7.0 offers minimal breaking changes against earlier versions while fixing some issues.


## Under the Hood

A `FormStash` object saves the parsed form data into a `ParsedForm` dict.

    FormStash.parsed_form: ParsedForm = {}

The `ParsedForm` dict has 3 entries, which are all dicts:

    results
    errors
    defaults

`results`, `errors` and `defaults` have accessor properties on the FormStash object.

"special_errors", such as "nothing_submitted", are stored in the main "errors" dict
with an asterisk prefix (e.g. "*nothing_submitted")

The errors have multiple accessors:

    `FormStash.errors` - returns `FormStash.errors_normal`
    `FormStash.errors_normal` - only returns `ParsedForm["errors"]` without a "*" prefix
    `FormStash.errors_special` - only returns `ParsedForm["errors"]` with a "*" prefix
    `FormStash.errors_all` - returns all `ParsedForm["errors"]`


### Debugging

Debug logging was introduced in the 0.11.x branch and updated in 0.12.x branch.

The main ways to trigger debugging:

1- Monkeypatch the library

    import pyramid_formencode_classic._defaults

    pyramid_formencode_classic._defaults.DEBUG_FAILS = True


2- Set an ENV variable

    export PYRAMID_FORMENCODE_CLASSIC__DEBUG_FAILS=1
    python myapp.py


3- Use as needed; the debugging occurs on

    # populate objects/methods for automatic debug logging
    pyramid_formencode_classic.form_validate(debug_fails=True)
    pyramid_formencode_classic.objects.FormStash(debug_fails=True)
    pyramid_formencode_classic.exceptions.FormInvalid(debug_fails=True)

    # manual debug on demand
    pyramid_formencode_classic.exceptions.FormInvalid.debug()


### Error Concepts

For the purpose of this package, errors can be grouped into two concepts:

meta-errors
    Errors about the Form itself, such as:
        "There is an error with the form"
        "nothing was submitted."
field-errors
    Errors for specific fields

#### meta-errors: Error_Main or error_main_key

To integrate meta-errors into the form, the FormStash will create an "Error_Main"
entry in the `PrasedForm["errors"]`  dict, which is available as `FormStash.errors`.

`Error_Main` is a key in the `FormStash.error` (`ParsedForm["errors"]`) Dict which corresponds
to the main message of a form failure.

The `set_error` routine will integrate meta errors, such as `nothing_submitted` into
the `Error_Main` text, when setting the main form error.

#### field errors

The `errors` dict will contain the field errors as validated.


### Versioning Policy

This project using a Semantic Versioning Policy: `Major.Minor.Patch`.

`Major`: significant API changes
`Minor`: backwards incompatible API changes
`Patch`: backwards compatible API changes and bugfixes

The recommended usage is to pin versioning within the `Major.Minor` range:

	pyramid_formencode_classic >=0.9.0, <0.10.0


## This looks more complicated than it should be.

Yes, it is.

This library tries to generate and manage useful errors.

Assume we have a login for that is just email/password::

    class Form_Login(formencode.Schema):
        username = formencode.validators.UnicodeString(not_empty=True)
        password = formencode.validators.UnicodeString(not_empty=True)

And this is our basic validation pattern::

    (result, formStash) = pyramid_formencode_classic.form_validate(
        request,
        schema=Form_Login,
    )

What should happen if we don't fill anything out?

We don't just want to simply indicate an error, we also need to note there was
nothing submitted to the form.

This package offers defaults, but can customize messages like such:

    (result, formStash) = pyramid_formencode_classic.form_validate(
        request,
        schema=Form_Login,
        error_main_text = "There was an error with your form",
        error_no_submission_text = "Nothing submitted.",
    )

The package will then merge the `error_main_text` and `error_no_submission_text`
into `FormStash.errors["error_main"] = "There was an error with your form. Nothing submitted."`

Now imagine you need to set a form error yourself:

    (result, formStash) = pyramid_formencode_classic.form_validate(
        request,
        schema=Form_Login,
        error_main_text = "There was an error with your form",
        error_no_submission_text = "Nothing submitted.",
    )
    user = get_user_by_login(formStash.results["username"], formStash.results["password"])
    if not user:
        formStash.fatal_form("Invalid credentials")
        # or
        # raise FormInvalid(formStash, "Invalid credentials")

How should that render?

We don't want to just see:

    Invalid Credentials.

We want to see as the "form error":

     There was an error with your form. Invalid credentials.

So this package tries to do the right thing, and merges `error_main_text` with `Invalid credentials`.

If you only want to show a specific message though, you can invoke:

    if not user:
        formStash.fatal_form("Invalid credentials", error_main_overwrite=True)
        # or
        # raise FormInvalid(formStash, "Invalid credentials", error_main_overwrite=True)

Which will render:

    Invalid Credentials.

Most of the work put into this package over the past decade has been to keep a
simple interface to achieve this type of error rendering, while also giving the
flexibility to be more interactive.


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


## How does this handle form validation?

The simplest way to utilize this library is with this code:

    result: bool
    formStash: pyramid_formencode_classic.FormStash
    request: pyramid.request.Request
    Form_Email: formencode.Schema

	(result, formStash) = pyramid_formencode_classic.form_validate(request, schema=Form_Email)

`form_validate` can either raise an Exception (`pyramid_formencode_classic.exceptions.FormInvalid`) or return `False``, based on the kwargs.

if `form_validate` raises an Exception, the `FormStash` is available as an attribute.

Formencode's htmlfill can be used to re-render the form with errors.

## Pyramid Integration

Just do this::

	config.include('pyramid_formencode_classic')

Which will invoke `Pyramid`'s `add_request_method` to add a new attribute to your request.

`request.pyramid_formencode_classic` will be a per-request instance of `pyramid_formencode_classic.FormStashList`.

Parsing a form will manage the formdata in `request.pyramid_formencode_classic['_default']` the default form stash.

If you want to specify a particular stash, because you use multiple forms on a page or have other needs:

* `request.pyramid_formencode_classic.get_form(...)` accepts a `form_stash` kwarg, which defaults to `_default`
* `form_validate(...)` accepts a `form_stash` kwarg, which defaults to `_default`
* `form_reprint(...)` accepts a `form_stash` kwarg, which defaults to `_default`


## Caveats, Oddities, Etc

### Custom Errors, Custom Error Displays and Missing Fields

#### Where are errors placed?  What about missing fields?

`formencode.htmlfill` prefers to upgrade a html form element with the error information.

If the html input for an error is missing, such as a custom `Error_Main` field, `formencode` will attempt to do two things:

1. `formencode` will look for a custom `form:error` field, such as `<form:error name="Error_Main"/>`.
2. If no fields are available, `formencode` will *PREPEND* the error messages to the document.  This can create problems if you are running the reprint on a full (not partial) html page.

#### How are errors styled?

`formencode` styles errors using two arguments.

* `auto_error_formatter` is a function that formats the error messages for fields which do not appear on the document and are pre-pended.
* `error_formatters` is a dict of error formatters that can be passed into `htmlfill`.  if provided, these will be merged into the htmlfill defaults.

`htmlfill` allows a bit of customization by supporting a `format` attribute in `<form:error/>` declarations, which will invoke the respective entry in the `error_formatters` dict.

#### How can a "global" form error be handled?

Handling a custom error can be achieved by reserving a special `error_main` key. By default, `pyramid_formencode_classic` uses `Error_Main`.

Once you set that field as a form error,  `formencode.htmlfill` will replace this markup in your template

    <form:error name="Error_Main"/>

with the following html:

    <!-- for: Error_Main -->
	<span class="error-message">%(Error_Main)s</span><br/>

In which the `Error_main` text has been run through `error_formatters['default']`

There is a small caveat:

In order for the text to appear in the form where you wish, you must write `<form:error name="Error_Main"/>` in the form.  Non-error views will contain that text in the html source, but not render it; error views will replace it with properly formatted errors.

This package offers a convenience method to conditionally render that text:

	<html><head></head><body><div>
	<form action="/" method="POST">
		<% form = request.pyramid_formencode_classic.get_form() %>
		${form.html_error_placeholder()|n}
		<input type="text" name="email" value="" />
		<input type="text" name="username" value="" />
	</form>
	</div></body></html>


If the marking is not in your template, it will be at the top of the document (before the html), after being run through the `auto_error_formatter`

    <!-- for: Error_Main -->
    <span class="error-message">${error_main}</span>


### Why doesn't form_validate` raise an Exception by default?

This design choice was made to allow for flexible scoping by default::

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
										  error_field_="Email not registered",
										  )

                if not useraccount.verify_submitted_password(results['password']):
                	# set a custom error and raise an exception to reprint
                    # `formStash.fatal_field(` will raise `formhandling.FormInvalid(`
                    formStash.fatal_field(
                        field="email_address",
                        error_field_="Wrong password",
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


#### How does it work?

The `form_stash` argument represents the unique `FormStash` object on the `request` (when it is not explicitly provided, it defaults to `_default`)

The `data_formencode_form` argument is passed from `form_reprint` to `formencode.htmlfill`; when provided, `formencode` will ignore tags which don't match the active formencode form's elements.

The HTML form elements are associated with a form via the attribute `data-formencode-form`


