![Python package](https://github.com/jvanasco/pyramid_formencode_classic/workflows/Python%20package/badge.svg)

## Current Recommended Version

`v 0.5.0 (2023.06.xx)`

New Features:
* mypy support
* drop python2
* project reorganized


## Last Python2 Version

`v 0.4.4 (2020.10.20)`

New Features:

* simplified api
* bug fixes, better integration
* python3 support
* pyramid debugtoolbar support
* automatic handling of edge cases with ForEach validator errors


### Backwards Compatible?

### 0.5.0

The library was reorganized to implement typing.
Most uses should be backwards compatible.
It is possible an object you used moved. If so, please file a ticket to see if we can pull it back in.
The default values were moved to a separate file. Those should never have been referenced in code.


### 0.4.0

* `0.3.x` No

### 0.3.0

* `0.2.x` Yes.
* `0.1.x` No. Some functionality switched between `0.1.10` and `0.2.0` and light editing is required.  See `CHANGES.txt` for full details.  Also see the migration guide below.


## Installation

This requires the 2.0 branch of formencode, which has still been an alpha release since Aug 9, 2016

	pip install formencode==2.0.0a1
	pip install pyramid_formencode_classic


## What is this package?

`pyramid_formencode_classic` is a port of some classic `Pylons` form validation concepts onto the `Pyramid` framework.

Through the version `0.1.x` releases, this package sought to integrate the Pylons validation onto Pyramid so projects could be ported easier.

Starting with version `0.2.0` strict backwards compatibility has been lost in favor of performance enhancements and streamlining the API. There were simply a handful of bugs and oddities which were not easily fixed.

## How does this handle form validation?

In the example below, form validation is broken into 4 components:

* A `formencode` form schema
* a callable dispatcher (`login`)
* a private printer (`_login_print`)
* a private submit processor (`_login_submit`)

The formencode schema does not interact with the database. It is used only for "lightweight" validation and cheap operations (length, presence, etc).

The more involved operations, such as checking a database within a transaction, can occur in the submit step.  

In this pattern, if an error is encountered at any time, a `FormInvalid` error can be raised to trigger `form_reprint`.  That function will render the template using `Pyramid`'s mechanism and then run `formencode`'s `htmlfill` on it.

If you want to set a global "oh noes!" message for the form, set an error on a special non-existent field like `Error_Main`.


## Pyramid Integration

Just do this...

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

`formencode` styles errors using two commandline arguments.

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
                (result,
                 formStash
                 ) = formhandling.form_validate(self.request,
                								schema=forms.FormLogin,
                								error_main="There was an error with your form.",
                								)
                if not result:
                    # `formStash.fatal_form(message)` will raise `formhandling.FormInvalid(message)`
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
                    formStash.fatal_field(field="email_address",
										  message="Wrong password",
										  )

				do_login()
				return HTTPFound(location='/account/home')

            except formhandling.FormInvalid as exc:
                # our reprint logic
                return formhandling.form_reprint(self.request,
                								 self._login_print
                								 )


Twitter Bootstrap Example
=========================

    To handle  twitter bootstrap style errors, it's a bit more manual work -- but doable

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



## Example Renderings

there is a trivial attempt at multiple form handling - a "form_stash" argument can be used, which will store different "FormStash" wrapped structures in the names provided.

CAVEATS

1. it doesn't support using a "render" on the form object -- it expects forms to be manually coded, and errors to be regexed out via htmlfill. live with it.
2. this REQUIRES one of the following two example scenarios 

Needless to say: this is really nice and clean in the first scenario, and messy in the latter.


### Example Rendering A - `render_to_response`

The form methods always render a response object via `pyramid.renderers.render_to_response`

	class MyView(handler):

		def test(self):
			if 'submit' in self.request.POST:
				return self._test_submit()
			return self._test_print()

		def _test_print(self):
			return render_to_response("/test_form.mako", {}, self.request)

		def _test_submit(self):
			try:
				(result,
				 formStash
				 ) = formhandling.form_validate(self.request,
												schema=forms.FormLogin,
												error_main="Error",
												)
				if not result:
					raise formhandling.FormInvalid()
				userAccount= query_for_useraccount(formStash.results['email'])
				if not userAccount:
					formStash.fatal_field(field='email',
										  message='Invalid Login',
										  )
				...
			except formhandling.FormInvalid:
				# you could set a field manually too
				#formhandling.formerrors_set(field="email", message='missing this field')
				return formhandling.form_reprint(self.request,
												 self._login_print,
												 )


### Example Rendering B - `view_config`

The form methods use a pyramid renderer

	class MyView(handler):

		@view_config(renderer='/test_form.mako')
		def test(self):
			if 'submit' in self.request.POST:
				return self._test_submit()
			return self._test_print()

		def _test_print(self):
			return {"project":"MyApp"}

		def _test_submit(self):
			try:
				(result,
				 formStash
				 ) = formhandling.form_validate(self.request,
												schema=forms.FormLogin,
												error_main="Error",
												)
				if not result:
					raise formhandling.FormInvalid()
				...
			except formhandling.FormInvalid as exc:
				return formhandling.form_reprint(self.request
												 None,
												 render_view=self._test_print,
												 render_view_template="/test_form.mako"
												 )


## Using multiple forms on a page?

In order to handle multiple form reprints correctly you need:

* pyramid_formencode_classic >= 0.2.0
* formencode >= 2.0.0

This functionality is dependent upon a PR which the formencode team was nice enough to accept in their 2.0.0 release.

This can be done in earlier versions, but you must give them each field a unique 'name' and handle them independently.

In earlier versions, reprints of error forms will not work correctly otherwise.

The following example references a unit test for the new functionality which ships with this package

### Multiple forms must be defined in html

The specific forms must be explicitly invoked in the thml

1. note the explicit `form_stash` argument in `request.pyramid_formencode_classic.get_form("a")`
2. the main error placeholder must note the form. e.g. `form.html_error_placeholder(formencode_form="a")`
3. the formfields must specify `data-formencode-form` e.g. `<input type="text" name="username" value="" data-formencode-form="a"/>`

full html example

	<html><head></head><body><div>
	<form action="/a" method="POST">
		<% form = request.pyramid_formencode_classic.get_form("a") %>
		${form.html_error_placeholder(formencode_form="a")|n}
		<input type="text" name="email" value="" data-formencode-form="a"/>
		<input type="text" name="username" value="" data-formencode-form="a"/>
	</form>
	<form action="/b" method="POST">
		<% form = request.pyramid_formencode_classic.get_form("b") %>
		${form.html_error_placeholder(formencode_form="b")|n}
		<input type="text" name="email" value="" data-formencode-form="b"/>
		<input type="text" name="username" value="" data-formencode-form="b"/>
	</form>
	</div></body></html>

### Multiple forms must be processed in Python

the call to `form_validate` must specify the desired `form_stash`

the call to `form_reprint` must specify *BOTH* the desired `form_stash` and `data_formencode_form` (which is used to handle the form attributes)

full python example:

        try:
            (result,
             formStash
             ) = pyramid_formencode_classic.form_validate(self.request,
                                                          schema=Form_EmailUsername,
                                                          form_stash='b',
                                                          error_main="There was an error with your form.",
                                                          **_validate_kwargs
                                                          )
            if not result:
                raise pyramid_formencode_classic.FormInvalid("Custom Main Error")
        except pyramid_formencode_classic.FormInvalid as exc:
            rendered = pyramid_formencode_classic.form_reprint(self.request,
                                                               _print_form_simple,
                                                               form_stash='b',
                                                               data_formencode_form='b',
                                                               **_reprint_kwargs
                                                               )
            return rendered

#### How does it work?

The `form_stash` argument represents the unique `FormStash` object on the `request` (when it is not explicitly provided, it defaults to `_default`)

The `data_formencode_form` argument is passed from `form_reprint` to `formencode.htmlfill`; when provided, `formencode` will ignore tags which don't match the active formencode form's elements.

The HTML form elements are associated with a form via the attribute `data-formencode-form`


## Dealing with unicode markers in errors (Python2)

There is an issue with formencode under Python2, where an error message shows a unicode marker (see https://github.com/formencode/formencode/issues/132) and may appear like `Value must be one of: a; b (not u'c')` instead of `Value must be one of: a; b (not 'c')`.

After much testing, the simplest way to handle this is to detect it in errors and replace it.  A better method would need to be implemented in formencode itself.
	
A quick way to handle this is to define your own implementation of `form_validate` and just use that throughout your project.

For example:

	import pyramid_formencode_classic
	from six import PY2

	def form_validate(request, **kwargs):
		"""
		kwargs
			things of interest...
			is_unicode_params - webob 1.x+ transfers to unicode.
		"""
		if 'is_unicode_params' not in kwargs:
			kwargs['is_unicode_params'] = True
		(result,
		 formStash
		 ) = pyramid_formencode_classic.form_validate(
			request,
			**kwargs
		)
		formStash.html_error_main_template = TEMPLATE_FORMSTASH_ERRORS
		formStash.html_error_placeholder_template = '<form:error name="%s" format="main"/>'
		formStash.html_error_placeholder_form_template = '<form:error name="%(field)s" format="main" data-formencode-form="%(form)s"/>'
		if not result:
			if PY2:
				# there is an issue in formencode under Python2 
				# see: https://github.com/formencode/formencode/issues/132
				for (k, v) in formStash.errors.items():
					if " (not u'" in v:
						formStash.errors[k] = v.replace( " (not u'",  " (not '")
		return (result,
				formStash
				)



# Misc

if possible, use partial forms and not entire html documents.

80% of this code is adapted from Pylons, 20% is outright copy/pasted.

released under the BSD license, as it incorporates some Pylons code (which was BSD)


## Debugtoolbar Support?

Yep. just add to your development.ini

	debugtoolbar.includes = pyramid_formencode_classic_.debugtoolbar

The debugtoolbar will now have a `FormencodeClassic` panel.

The panel shows information such as:

* which forms were processed/setup
* form results (errors, defaults, actual results)
* form schema
* form parsing status
* form configuration


### Are there tests?

Yes. Starting with the `0.2.0` release, there is a full test suite to ensure forms render as expected.


### Versioning Policy

This project using a Semantic Versioning Policy: `Major.Minor.Patch`.

`Major`: significant API changes
`Minor`: backwards incompatible API changes
`Patch`: backwards compatible API changes and bugfixes

The recommended usage is to pin versioning within the `Major.Minor` range:

	pyramid_formencode_classic >=0.4.0, <0.5.0
            

### Why doesn't form_validate` raise an Exception by default?

This design choice was made to allow for scoping within Pyramid apps:

	try:
		(result,
		 formStash
		 ) = form_validate(...)
		if not result:
			raise FormInvalid()
		# do stuff

	except FormInvalid as exc:
		# formStash is scoped here

An alternative would be something like this...

	try:
		formStash = form_validate(..., form_stash='FormId')
		# do stuff

	except FormInvalid as exc:
		formStash = request.pyramid_formencode_classic['FormId']

The latter situation can be easily accomplished by defining a custom `form_validate` function
		




## Migration Guide

### v0.1.x to v0.2.0

There are some slight changes:

`formStash.html_error_main()` was implemented poorly and rendered the actual template.  a new, better, approach is to use `formStash.html_error_placeholder()`.  if you want the previous behavior, use `formStash.render_html_error_main()`

instead of manually adding a form object, you now can/should use `config.include('pyramid_formencode_classic')` in your app's initialization.

several functions and kwargs were removed, CHANGES provides a full list but highlights include:

* camelCase methods have been removed.
* `section` no longer works as a kwarg. use `field` instead.
* the kwarg `raise_field_invalid` is removed in favor of `raise_FieldInvalid`
* the kwarg `raise_form_invalid` is removed in favor of `raise_FormInvalid`

The new setup makes invoking error formatters for htmlfill much easier.

### v0.3.x to v0.4.x

* `FormStash.set_error()` the `raise_FieldInvalid` kwarg was removed. instead, use `FormStash.fatal_field()`
* `FormStash.set_error()` the `raise_FormInvalid` kwarg was removed. instead, use `FormStash.fatal_form()`
* import formatters from `pyramid_formencode_classic.formatters` not the main namespace


