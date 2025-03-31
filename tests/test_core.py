"""
IMPORTANT

whitespace in the this file IS SIGNIFICANT AND IMPORTANT.
the test-cases check for specific whitespace
"""

# stdblib
import logging
import sys
from typing import Dict
from typing import Optional
import unittest

# pypi
import formencode
from pyramid import testing
from pyramid.interfaces import IRequestExtensions
from pyramid.renderers import render_to_response
from pyramid.request import Request
from webob.multidict import MultiDict

# local
import pyramid_formencode_classic
from pyramid_formencode_classic import _defaults
from pyramid_formencode_classic import formatters

# ==============================================================================

# Set these so it's easier to debug tests
_defaults.DEFAULT_ERROR_MAIN_TEXT = "[[DEFAULT_ERROR_MAIN_TEXT]]"
_defaults.DEFAULT_ERROR_FIELD_TEXT = "[[DEFAULT_ERROR_FIELD_TEXT]]"


DEBUG_PRINT = True
DEBUG_LOGGING = True

if DEBUG_LOGGING:
    for ll_cool_log in (
        "pyramid_formencode_classic",
        "pyramid_formencode_classic.api",
        "pyramid_formencode_classic.objects",
    ):
        log = logging.getLogger(ll_cool_log)
        log.setLevel(logging.DEBUG)


class _Schema_Base(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True


class Form_Email(_Schema_Base):
    email = formencode.validators.Email(not_empty=True)


class Form_EmailUsername(_Schema_Base):
    email = formencode.validators.Email(not_empty=True)
    username = formencode.validators.UnicodeString(not_empty=True)


# ==============================================================================


class DummyRequest(testing.DummyRequest):
    """
    extend `testing.DummyRequest` with a closer represtantion
    """

    GET: MultiDict
    POST: MultiDict

    def __init__(self):
        super(DummyRequest, self).__init__()
        self.GET = MultiDict()
        self.POST = MultiDict()


class _TestHarness(object):
    def setUp(self):
        self.config = testing.setUp()
        self.config.include("pyramid_formencode_classic")
        self.config.include("pyramid_mako")
        self.settings = {
            "mako.directories": "pyramid_formencode_classic.tests:fixtures"
        }
        self.context = testing.DummyResource()

        # use our version of DummyRequest
        self.request = DummyRequest()

        # copy the item over...
        self.request.pyramid_formencode_classic = (
            pyramid_formencode_classic._new_request_FormStashList(self.request)
        )

    def tearDown(self):
        testing.tearDown()


class _TestRenderSimple(object):
    """
    mixin class
    subclass and define a dict of test/values

    python -munittest pyramid_formencode_classic.tests.core.TestRenderSimple_FormA_HtmlErrorPlaceholder_Default \
                      pyramid_formencode_classic.tests.core.TestRenderSimple_FormA_HtmlErrorPlaceholder_Explicit \
                      pyramid_formencode_classic.tests.core.TestRenderSimple_FormA_HtmlErrorPlaceholder_Alt \
                      pyramid_formencode_classic.tests.core.TestRenderSimple_FormA_HtmlErrorPlaceholder_None
    """

    template: str
    _test_render_simple__data: Dict
    request: Request

    def test_render_simple(self):
        _template = self.template
        _expected_text = self._test_render_simple__data["response_text"]

        def _print_form_simple():
            rendered = render_to_response(_template, {"request": self.request})
            return rendered

        rendered = _print_form_simple()
        try:
            assert rendered.text == _expected_text
        except:
            if DEBUG_PRINT:
                print("------------")
                print(rendered.text)
                print("------------")
            raise


class _TestParsing(object):
    """
    mixin class
    subclass and define a dict of test/values

    python -munittest pyramid_formencode_classic.tests.core.TestParsing_FormA_HtmlErrorPlaceholder_Explicit \
                      pyramid_formencode_classic.tests.core.TestParsing_FormA_HtmlErrorPlaceholder_Alt \
                      pyramid_formencode_classic.tests.core.TestParsing_FormA_HtmlErrorPlaceholder \
                      pyramid_formencode_classic.tests.core.TestParsing_FormA_HtmlErrorPlaceholder \
                      pyramid_formencode_classic.tests.core.TestParsing_FormA_NoErrorMain \
                      pyramid_formencode_classic.tests.core.TestParsingErrorFormatters_FormA_HtmlErrorPlaceholder \
                      pyramid_formencode_classic.tests.core.TestParsingErrorFormatters_FormA_HtmlErrorPlaceholder_Alt \
                      pyramid_formencode_classic.tests.core.TestParsingErrorFormatters_FormA_NoErrorMain
    """

    _test_submit__data: Dict  # placeholder
    _test_no_params__data: Dict  # placeholder
    error_main_key: Optional[str] = None
    template: str
    request: Request

    def test_no_params(self):
        tests_completed = []
        tests_fail = []

        for test_name, test_data in self._test_no_params__data.items():
            _template = self.template
            _expected_text = test_data["response_text"]
            _reprint_kwargs: Dict = {}
            if "auto_error_formatter" in test_data:
                _reprint_kwargs["auto_error_formatter"] = test_data[
                    "auto_error_formatter"
                ]
            if "error_formatters" in test_data:
                if test_data["error_formatters"] is not None:
                    _reprint_kwargs["error_formatters"] = test_data["error_formatters"]
            _validate_kwargs: Dict = {}
            if self.error_main_key is not None:
                _validate_kwargs["error_main_key"] = self.error_main_key

            def _print_form_simple():
                rendered = render_to_response(_template, {"request": self.request})
                return rendered

            try:
                (result, formStash) = pyramid_formencode_classic.form_validate(
                    self.request,
                    schema=Form_EmailUsername,
                    **_validate_kwargs,
                )
                if not result:
                    raise pyramid_formencode_classic.FormInvalid(formStash)

                raise ValueError(
                    "`if not result:` should have raised `pyramid_formencode_classic.FormInvalid`"
                )

            except pyramid_formencode_classic.FormInvalid as exc:
                formStash.register_error_main_exception(exc)
                rendered = pyramid_formencode_classic.form_reprint(
                    self.request, _print_form_simple, **_reprint_kwargs
                )
                try:
                    assert rendered.text == _expected_text
                except:
                    if DEBUG_PRINT:
                        print("=============")
                        print("%s.test_no_params" % self.__class__)
                        print(test_name)
                        print("------------")
                        print(rendered.text)
                        print("------------")
                        print(_expected_text)
                        print("=============")
                    tests_fail.append(test_name)
            tests_completed.append(test_name)

        if tests_fail:
            raise ValueError(tests_fail)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def test_submit(self):
        # set the submit
        self.request.POST["submit"] = "submit"

        tests_completed = []
        tests_fail = []
        for test_name, test_data in self._test_submit__data.items():
            _template = self.template
            _expected_text = test_data["response_text"]
            _reprint_kwargs: Dict = {}
            if "auto_error_formatter" in test_data:
                _reprint_kwargs["auto_error_formatter"] = test_data[
                    "auto_error_formatter"
                ]
            if "error_formatters" in test_data:
                if test_data["error_formatters"] is not None:
                    _reprint_kwargs["error_formatters"] = test_data["error_formatters"]
            _validate_kwargs: Dict = {}
            if self.error_main_key is not None:
                _validate_kwargs["error_main_key"] = self.error_main_key

            def _print_form_simple():
                rendered = render_to_response(_template, {"request": self.request})
                return rendered

            try:
                (result, formStash) = pyramid_formencode_classic.form_validate(
                    self.request,
                    schema=Form_EmailUsername,
                    **_validate_kwargs,
                )
                if not result:
                    raise pyramid_formencode_classic.FormInvalid(formStash)

                raise ValueError(
                    "`if not result:` should have raised `pyramid_formencode_classic.FormInvalid`"
                )

            except pyramid_formencode_classic.FormInvalid as exc:
                formStash.register_error_main_exception(exc)
                rendered = pyramid_formencode_classic.form_reprint(
                    self.request, _print_form_simple, **_reprint_kwargs
                )
                try:
                    assert rendered.text == _expected_text
                except:
                    if DEBUG_PRINT:
                        print("------------")
                        print("%s.test_submit" % self.__class__)
                        print(test_name)
                        print(rendered.text)
                    tests_fail.append(test_name)
            tests_completed.append(test_name)

        if tests_fail:
            raise ValueError(tests_fail)


class TestSetup(_TestHarness, unittest.TestCase):
    def test_pyramid_setup(self):
        """test the request property worked"""
        exts = self.config.registry.getUtility(IRequestExtensions)
        self.assertTrue("pyramid_formencode_classic" in exts.descriptors)


class TestRenderSimple_FormA_HtmlErrorPlaceholder_Alt(
    _TestRenderSimple, _TestHarness, unittest.TestCase
):
    template = "fixtures/form_a-html_error_placeholder-alt.mako"

    # note: _test_render_simple__data
    _test_render_simple__data = {
        "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
    }


class TestRenderSimple_FormA_HtmlErrorPlaceholder_Explicit(
    _TestRenderSimple, _TestHarness, unittest.TestCase
):
    template = "fixtures/form_a-html_error_placeholder-explicit.mako"

    # note: _test_render_simple__data
    _test_render_simple__data = {
        "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
    }


class TestRenderSimple_FormA_HtmlErrorPlaceholder_Default(
    _TestRenderSimple, _TestHarness, unittest.TestCase
):
    template = "fixtures/form_a-html_error_placeholder-default.mako"

    # note: _test_render_simple__data
    _test_render_simple__data = {
        "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
    }


class TestRenderSimple_FormA_ErrorPlaceholder_None(
    _TestRenderSimple, _TestHarness, unittest.TestCase
):
    template = "fixtures/form_a-html_error_placeholder-none.mako"

    # note: _test_render_simple__data
    _test_render_simple__data = {
        "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
    }


class TestParsing_FormA_HtmlErrorPlaceholder_Default(
    _TestParsing, _TestHarness, unittest.TestCase
):
    template = "fixtures/form_a-html_error_placeholder-default.mako"

    # note the whitespace in the lines here!

    # note: _test_no_params__data
    _test_no_params__data = {
        "test_formatter_default": {
            # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_is_none": {
            "auto_error_formatter": None,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_nobr": {
            "auto_error_formatter": formatters.formatter_nobr,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_help_inline": {
            "auto_error_formatter": formatters.formatter_help_inline,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_comment": {
            "auto_error_formatter": formatters.formatter_comment,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_empty_string": {
            "auto_error_formatter": formatters.formatter_empty_string,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_hidden": {
            "auto_error_formatter": formatters.formatter_hidden,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
    }

    # note: _test_submit__data
    _test_submit__data = {
        "test_formatter_default": {
            # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
            "error_formatters": None,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s</span><br />

    <!-- for: email -->
<span class="error-message">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_nobr": {
            "auto_error_formatter": formatters.formatter_nobr,
            "error_formatters": {"default": formatters.formatter_nobr},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s</span>

    <!-- for: email -->
<span class="error-message">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_is_none": {
            "auto_error_formatter": None,
            "error_formatters": None,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s</span><br />

    <!-- for: email -->
<span class="error-message">Missing value</span><br />
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span><br />
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_comment": {
            "auto_error_formatter": formatters.formatter_comment,
            "error_formatters": {"default": formatters.formatter_comment},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- formatter_comment (%s)-->
    <!-- for: email -->
<!-- formatter_comment (Missing value)--><input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<!-- formatter_comment (Missing value)--><input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_help_inline": {
            "auto_error_formatter": formatters.formatter_help_inline,
            "error_formatters": {"default": formatters.formatter_help_inline},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="help-inline">%s</span>

    <!-- for: email -->
<span class="help-inline">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="help-inline">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_empty_string": {
            "auto_error_formatter": formatters.formatter_empty_string,
            "error_formatters": {"default": formatters.formatter_empty_string},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    
    <!-- for: email -->
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
""",
        },
        "formatter_hidden": {
            "auto_error_formatter": formatters.formatter_hidden,
            "error_formatters": {"default": formatters.formatter_hidden},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="hidden" value="%s" />

    <!-- for: email -->
<input type="hidden" value="Missing value" />
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<input type="hidden" value="Missing value" />
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
    }


class TestParsing_FormA_HtmlErrorPlaceholder_Explicit(
    TestParsing_FormA_HtmlErrorPlaceholder_Default,
    _TestParsing,
    _TestHarness,
    unittest.TestCase,
):
    """
    inherit from TestParsing_FormA_HtmlErrorPlaceholder_Default
    this should have the same exact output, but with a different template
    """

    template = "fixtures/form_a-html_error_placeholder-explicit.mako"


class TestParsing_FormA_ErrorPlaceholder_None(
    _TestParsing, _TestHarness, unittest.TestCase
):
    """
    Tests:
        the parsing sets an error, but does not include a field.
    Expected behavior:
        the error should be prepended to the HTML, and should be encoded with the right AutoFormatter

    python -munittest pyramid_formencode_classic.tests.core.TestParsing_FormA_NoErrorMain
    """

    template = "fixtures/form_a-html_error_placeholder-none.mako"

    # note the whitespace in the lines here!

    # note: _test_no_params__data
    _test_no_params__data = {
        "test_formatter_default": {
            # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
            "response_text": """\
<!-- for: Error_Main -->
<span class="error-message">%s Nothing submitted.</span>
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_is_none": {
            "auto_error_formatter": None,
            "response_text": """\
<!-- for: Error_Main -->
<span class="error-message">%s Nothing submitted.</span><br />
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_nobr": {
            "auto_error_formatter": formatters.formatter_nobr,
            "response_text": """\
<!-- for: Error_Main -->
<span class="error-message">%s Nothing submitted.</span>
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_help_inline": {
            "auto_error_formatter": formatters.formatter_help_inline,
            "response_text": """\
<!-- for: Error_Main -->
<span class="help-inline">%s Nothing submitted.</span>
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_comment": {
            "auto_error_formatter": formatters.formatter_comment,
            "response_text": """\
<!-- for: Error_Main -->
<!-- formatter_comment (%s Nothing submitted.)--><html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_empty_string": {
            "auto_error_formatter": formatters.formatter_empty_string,
            "response_text": """\
<!-- for: Error_Main -->
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
        },
        "formatter_hidden": {
            "auto_error_formatter": formatters.formatter_hidden,
            "response_text": """\
<!-- for: Error_Main -->
<input type="hidden" value="%s Nothing submitted." />
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
    }

    # note: _test_submit__data
    _test_submit__data = {
        "test_formatter_default": {
            # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
            "response_text": """\
<!-- for: Error_Main -->
<span class="error-message">%s</span>
<html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- for: email -->
<span class="error-message">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_nobr": {
            "auto_error_formatter": formatters.formatter_nobr,
            "response_text": """\
<!-- for: Error_Main -->
<span class="error-message">%s</span>
<html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- for: email -->
<span class="error-message">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_is_none": {
            "auto_error_formatter": None,
            "response_text": """\
<!-- for: Error_Main -->
<span class="error-message">%s</span><br />
<html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- for: email -->
<span class="error-message">Missing value</span><br />
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span><br />
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_comment": {
            "auto_error_formatter": formatters.formatter_comment,
            "response_text": """\
<!-- for: Error_Main -->
<!-- formatter_comment (%s)--><html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- for: email -->
<!-- formatter_comment (Missing value)--><input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<!-- formatter_comment (Missing value)--><input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_help_inline": {
            "auto_error_formatter": formatters.formatter_help_inline,
            "response_text": """\
<!-- for: Error_Main -->
<span class="help-inline">%s</span>
<html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- for: email -->
<span class="help-inline">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="help-inline">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_empty_string": {
            "auto_error_formatter": formatters.formatter_empty_string,
            "response_text": """\
<!-- for: Error_Main -->
<html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- for: email -->
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
""",
        },
        "formatter_hidden": {
            "auto_error_formatter": formatters.formatter_hidden,
            "response_text": """\
<!-- for: Error_Main -->
<input type="hidden" value="%s" />
<html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- for: email -->
<input type="hidden" value="Missing value" />
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<input type="hidden" value="Missing value" />
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
    }


class TestParsing_FormA_HtmlErrorPlaceholder_Alt(
    _TestParsing, _TestHarness, unittest.TestCase
):
    """
    this behaves slightly differently than TestParsing_FormA_HtmlErrorPlaceholder_Explicit
    """

    template = "fixtures/form_a-html_error_placeholder-alt.mako"
    error_main_key = "Error_Alt"

    # note the whitespace in the lines here!

    # note: _test_no_params__data
    _test_no_params__data = {
        "test_formatter_default": {
            # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT
        },
        "test_formatter_is_none": {
            "auto_error_formatter": None,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_nobr": {
            "auto_error_formatter": formatters.formatter_nobr,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_help_inline": {
            "auto_error_formatter": formatters.formatter_help_inline,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_comment": {
            "auto_error_formatter": formatters.formatter_comment,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_empty_string": {
            "auto_error_formatter": formatters.formatter_empty_string,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_hidden": {
            "auto_error_formatter": formatters.formatter_hidden,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
    }

    # note: _test_submit__data
    _test_submit__data = {
        "test_formatter_default": {
            # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
            "error_formatters": None,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s</span><br />

    <!-- for: email -->
<span class="error-message">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_nobr": {
            "auto_error_formatter": formatters.formatter_nobr,
            "error_formatters": {"default": formatters.formatter_nobr},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s</span>

    <!-- for: email -->
<span class="error-message">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_is_none": {
            "auto_error_formatter": None,
            "error_formatters": None,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s</span><br />

    <!-- for: email -->
<span class="error-message">Missing value</span><br />
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span><br />
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_comment": {
            "auto_error_formatter": formatters.formatter_comment,
            "error_formatters": {"default": formatters.formatter_comment},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- formatter_comment (%s)-->
    <!-- for: email -->
<!-- formatter_comment (Missing value)--><input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<!-- formatter_comment (Missing value)--><input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_help_inline": {
            "auto_error_formatter": formatters.formatter_help_inline,
            "error_formatters": {"default": formatters.formatter_help_inline},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="help-inline">%s</span>

    <!-- for: email -->
<span class="help-inline">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="help-inline">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_empty_string": {
            "auto_error_formatter": formatters.formatter_empty_string,
            "error_formatters": {"default": formatters.formatter_empty_string},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    
    <!-- for: email -->
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
""",
        },
        "formatter_hidden": {
            "auto_error_formatter": formatters.formatter_hidden,
            "error_formatters": {"default": formatters.formatter_hidden},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="hidden" value="%s" />

    <!-- for: email -->
<input type="hidden" value="Missing value" />
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<input type="hidden" value="Missing value" />
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
    }


class TestParsingErrorFormatters_FormA_HtmlErrorPlaceholder_Alt(
    _TestParsing, _TestHarness, unittest.TestCase
):
    """
    this behaves slightly differently than TestParsing_FormA_HtmlErrorPlaceholder_Alt
    """

    template = "fixtures/form_a-html_error_placeholder-alt.mako"
    error_main_key = "Error_Alt"

    # note the whitespace in the lines here!

    # note: _test_no_params__data
    _test_no_params__data = {
        "test_formatter_default": {
            # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
            "error_formatters": None,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_is_none": {
            "auto_error_formatter": None,
            "error_formatters": None,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_nobr": {
            "auto_error_formatter": formatters.formatter_nobr,
            "error_formatters": {"default": formatters.formatter_nobr},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s Nothing submitted.</span>

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_help_inline": {
            "auto_error_formatter": formatters.formatter_help_inline,
            "error_formatters": {"default": formatters.formatter_help_inline},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="help-inline">%s Nothing submitted.</span>

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_comment": {
            "auto_error_formatter": formatters.formatter_comment,
            "error_formatters": {"default": formatters.formatter_comment},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- formatter_comment (%s Nothing submitted.)-->
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_empty_string": {
            "auto_error_formatter": formatters.formatter_empty_string,
            "error_formatters": {"default": formatters.formatter_empty_string},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
        },
        "formatter_hidden": {
            "auto_error_formatter": formatters.formatter_hidden,
            "error_formatters": {"default": formatters.formatter_hidden},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="hidden" value="%s Nothing submitted." />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
    }

    # note: _test_submit__data
    _test_submit__data = {
        "test_formatter_default": {
            # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
            "error_formatters": None,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s</span><br />

    <!-- for: email -->
<span class="error-message">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_nobr": {
            "auto_error_formatter": formatters.formatter_nobr,
            "error_formatters": {"default": formatters.formatter_nobr},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s</span>

    <!-- for: email -->
<span class="error-message">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_is_none": {
            "auto_error_formatter": None,
            "error_formatters": None,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s</span><br />

    <!-- for: email -->
<span class="error-message">Missing value</span><br />
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span><br />
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_comment": {
            "auto_error_formatter": formatters.formatter_comment,
            "error_formatters": {"default": formatters.formatter_comment},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- formatter_comment (%s)-->
    <!-- for: email -->
<!-- formatter_comment (Missing value)--><input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<!-- formatter_comment (Missing value)--><input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_help_inline": {
            "auto_error_formatter": formatters.formatter_help_inline,
            "error_formatters": {"default": formatters.formatter_help_inline},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="help-inline">%s</span>

    <!-- for: email -->
<span class="help-inline">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="help-inline">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_empty_string": {
            "auto_error_formatter": formatters.formatter_empty_string,
            "error_formatters": {"default": formatters.formatter_empty_string},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    
    <!-- for: email -->
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
""",
        },
        "formatter_hidden": {
            "auto_error_formatter": formatters.formatter_hidden,
            "error_formatters": {"default": formatters.formatter_hidden},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="hidden" value="%s" />

    <!-- for: email -->
<input type="hidden" value="Missing value" />
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<input type="hidden" value="Missing value" />
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
    }


class TestParsingErrorFormatters_FormA_HtmlErrorPlaceholder_Default(
    _TestParsing, _TestHarness, unittest.TestCase
):
    template = "fixtures/form_a-html_error_placeholder-default.mako"

    # note the whitespace in the lines here!

    # note: _test_no_params__data
    _test_no_params__data = {
        "test_formatter_default": {
            # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
            "error_formatters": None,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_is_none": {
            "auto_error_formatter": None,
            "error_formatters": None,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_nobr": {
            "auto_error_formatter": formatters.formatter_nobr,
            "error_formatters": {"default": formatters.formatter_nobr},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s Nothing submitted.</span>

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_help_inline": {
            "auto_error_formatter": formatters.formatter_help_inline,
            "error_formatters": {"default": formatters.formatter_help_inline},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="help-inline">%s Nothing submitted.</span>

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_comment": {
            "auto_error_formatter": formatters.formatter_comment,
            "error_formatters": {"default": formatters.formatter_comment},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- formatter_comment (%s Nothing submitted.)-->
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_empty_string": {
            "auto_error_formatter": formatters.formatter_empty_string,
            "error_formatters": {"default": formatters.formatter_empty_string},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
        },
        "formatter_hidden": {
            "auto_error_formatter": formatters.formatter_hidden,
            "error_formatters": {"default": formatters.formatter_hidden},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="hidden" value="%s Nothing submitted." />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
    }

    # note: _test_submit__data
    _test_submit__data = {
        "test_formatter_default": {
            # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
            "error_formatters": None,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s</span><br />

    <!-- for: email -->
<span class="error-message">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_nobr": {
            "auto_error_formatter": formatters.formatter_nobr,
            "error_formatters": {"default": formatters.formatter_nobr},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s</span>

    <!-- for: email -->
<span class="error-message">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_is_none": {
            "auto_error_formatter": None,
            "error_formatters": None,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s</span><br />

    <!-- for: email -->
<span class="error-message">Missing value</span><br />
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span><br />
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_comment": {
            "auto_error_formatter": formatters.formatter_comment,
            "error_formatters": {"default": formatters.formatter_comment},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- formatter_comment (%s)-->
    <!-- for: email -->
<!-- formatter_comment (Missing value)--><input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<!-- formatter_comment (Missing value)--><input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_help_inline": {
            "auto_error_formatter": formatters.formatter_help_inline,
            "error_formatters": {"default": formatters.formatter_help_inline},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="help-inline">%s</span>

    <!-- for: email -->
<span class="help-inline">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="help-inline">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_empty_string": {
            "auto_error_formatter": formatters.formatter_empty_string,
            "error_formatters": {"default": formatters.formatter_empty_string},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    
    <!-- for: email -->
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
""",
        },
        "formatter_hidden": {
            "auto_error_formatter": formatters.formatter_hidden,
            "error_formatters": {"default": formatters.formatter_hidden},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="hidden" value="%s" />

    <!-- for: email -->
<input type="hidden" value="Missing value" />
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<input type="hidden" value="Missing value" />
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
    }


class TestParsingErrorFormatters_FormA_ErrorPlaceholder_None(
    _TestParsing, _TestHarness, unittest.TestCase
):
    """
    Tests:
        the parsing sets an error, but does not include a field.
        This variant specifies ErrorFormatters
    Expected behavior:
        the error should be prepended to the HTML, and should be encoded with the right AutoFormatter
        The ErrorFormatters should be ignored.

    python -munittest pyramid_formencode_classic.tests.core.TestParsing_FormA_NoErrorMain
    """

    template = "fixtures/form_a-html_error_placeholder-none.mako"

    # note the whitespace in the lines here!

    # note: _test_no_params__data
    _test_no_params__data = {
        "test_formatter_default": {
            # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
            "error_formatters": None,
            "response_text": """\
<!-- for: Error_Main -->
<span class="error-message">%s Nothing submitted.</span>
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_is_none": {
            "auto_error_formatter": None,
            "error_formatters": None,
            "response_text": """\
<!-- for: Error_Main -->
<span class="error-message">%s Nothing submitted.</span><br />
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_nobr": {
            "auto_error_formatter": formatters.formatter_nobr,
            "error_formatters": {"default": formatters.formatter_nobr},
            "response_text": """\
<!-- for: Error_Main -->
<span class="error-message">%s Nothing submitted.</span>
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_help_inline": {
            "auto_error_formatter": formatters.formatter_help_inline,
            "error_formatters": {"default": formatters.formatter_help_inline},
            "response_text": """\
<!-- for: Error_Main -->
<span class="help-inline">%s Nothing submitted.</span>
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_comment": {
            "auto_error_formatter": formatters.formatter_comment,
            "error_formatters": {"default": formatters.formatter_comment},
            "response_text": """\
<!-- for: Error_Main -->
<!-- formatter_comment (%s Nothing submitted.)--><html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_empty_string": {
            "auto_error_formatter": formatters.formatter_empty_string,
            "error_formatters": {"default": formatters.formatter_empty_string},
            "response_text": """\
<!-- for: Error_Main -->
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
        },
        "formatter_hidden": {
            "auto_error_formatter": formatters.formatter_hidden,
            "error_formatters": {"default": formatters.formatter_hidden},
            "response_text": """\
<!-- for: Error_Main -->
<input type="hidden" value="%s Nothing submitted." />
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
    }

    # note: _test_submit__data
    _test_submit__data = {
        "test_formatter_default": {
            # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
            "error_formatters": None,
            "response_text": """\
<!-- for: Error_Main -->
<span class="error-message">%s</span>
<html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- for: email -->
<span class="error-message">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_nobr": {
            "auto_error_formatter": formatters.formatter_nobr,
            "error_formatters": {"default": formatters.formatter_nobr},
            "response_text": """\
<!-- for: Error_Main -->
<span class="error-message">%s</span>
<html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- for: email -->
<span class="error-message">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_is_none": {
            "auto_error_formatter": None,
            "error_formatters": None,
            "response_text": """\
<!-- for: Error_Main -->
<span class="error-message">%s</span><br />
<html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- for: email -->
<span class="error-message">Missing value</span><br />
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span><br />
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_comment": {
            "auto_error_formatter": formatters.formatter_comment,
            "error_formatters": {"default": formatters.formatter_comment},
            "response_text": """\
<!-- for: Error_Main -->
<!-- formatter_comment (%s)--><html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- for: email -->
<!-- formatter_comment (Missing value)--><input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<!-- formatter_comment (Missing value)--><input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_help_inline": {
            "auto_error_formatter": formatters.formatter_help_inline,
            "error_formatters": {"default": formatters.formatter_help_inline},
            "response_text": """\
<!-- for: Error_Main -->
<span class="help-inline">%s</span>
<html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- for: email -->
<span class="help-inline">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="help-inline">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_empty_string": {
            "auto_error_formatter": formatters.formatter_empty_string,
            "error_formatters": {"default": formatters.formatter_empty_string},
            "response_text": """\
<!-- for: Error_Main -->
<html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- for: email -->
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
""",
        },
        "formatter_hidden": {
            "auto_error_formatter": formatters.formatter_hidden,
            "error_formatters": {"default": formatters.formatter_hidden},
            "response_text": """\
<!-- for: Error_Main -->
<input type="hidden" value="%s" />
<html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- for: email -->
<input type="hidden" value="Missing value" />
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<input type="hidden" value="Missing value" />
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
    }


class TestCustomError(_TestHarness, unittest.TestCase):
    """

    python -munittest pyramid_formencode_classic.tests.core.TestCustomError
    """

    error_main_key = None
    template = "fixtures/form_a-html_error_placeholder-default.mako"

    def test_submit(self):
        # set the submit
        self.request.POST["submit"] = "submit"

        # custom formatter
        def main_error_formatter(error):
            TEMPLATE_FORMSTASH_ERRORS = """<div class="alert alert-error"><div class="control-group error"><span class="help-inline"><i class="fa fa-exclamation-triangle"></i> %(error)s</span></div></div>"""
            return (
                TEMPLATE_FORMSTASH_ERRORS
                % {"error": formencode.rewritingparser.html_quote(error)}
            ) + "\n"

        def alt_error_formatter(error):
            ALT_ERROR = """<div class="error-alt">%(error)s</div>"""
            return (
                ALT_ERROR % {"error": formencode.rewritingparser.html_quote(error)}
            ) + "\n"

        tests_completed = []
        tests_fail = []
        for test_name, test_data in self._test_submit__data.items():
            _template = self.template
            _expected_text = test_data["response_text"]
            _reprint_kwargs: Dict = {"error_formatters": {}}
            if "error_formatters_default" in test_data:
                if test_data["error_formatters_default"] == "main_error_formatter":
                    _reprint_kwargs["error_formatters"][
                        "default"
                    ] = main_error_formatter
            if "error_formatters_alt" in test_data:
                if test_data["error_formatters_alt"] == "alt_error_formatter":
                    _reprint_kwargs["error_formatters"]["alt"] = alt_error_formatter

            _validate_kwargs: Dict = {}
            html_error_placeholder_template = test_data.get(
                "html_error_placeholder_template", None
            )

            def _print_form_simple():
                rendered = render_to_response(_template, {"request": self.request})
                return rendered

            try:
                (result, formStash) = pyramid_formencode_classic.form_validate(
                    self.request,
                    schema=Form_EmailUsername,
                    **_validate_kwargs,
                )
                if html_error_placeholder_template:
                    formStash.html_error_placeholder_template = (
                        html_error_placeholder_template
                    )

                if not result:
                    raise pyramid_formencode_classic.FormInvalid(formStash)

                raise ValueError(
                    "`if not result:` should have raised `pyramid_formencode_classic.FormInvalid`"
                )

            except pyramid_formencode_classic.FormInvalid as exc:
                formStash.register_error_main_exception(exc)
                rendered = pyramid_formencode_classic.form_reprint(
                    self.request, _print_form_simple, **_reprint_kwargs
                )
                try:
                    assert rendered.text == _expected_text
                except:
                    if DEBUG_PRINT:
                        print("------------")
                        print("%s.test_submit" % self.__class__)
                        print(test_name)
                        print(rendered.text)
                    tests_fail.append(test_name)
            tests_completed.append(test_name)

        if tests_fail:
            raise ValueError(tests_fail)

    # note: _test_submit__data
    _test_submit__data = {
        "set_a_custom_error": {
            # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
            "error_formatters_default": "main_error_formatter",
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <div class="alert alert-error"><div class="control-group error"><span class="help-inline"><i class="fa fa-exclamation-triangle"></i> %s</span></div></div>

    <!-- for: email -->
<span class="error-message">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "set_a_custom_error_placeholder": {
            # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
            "error_formatters_default": "main_error_formatter",
            "error_formatters_alt": "alt_error_formatter",
            "html_error_placeholder_template": '<form:error name="%s" format="alt"/>',
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <div class="error-alt">%s</div>

    <!-- for: email -->
<span class="error-message">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
    }


class TestMultiForm(_TestHarness, unittest.TestCase):
    """

    python -munittest pyramid_formencode_classic.tests.core.TestMultiForm
    """

    template = "fixtures/form_b-multi.mako"

    def test_render_simple(self):
        _template = self.template
        _expected_text = self._test_data["response_text-test_render_simple"]

        def _print_form_simple():
            rendered = render_to_response(_template, {"request": self.request})
            return rendered

        rendered = _print_form_simple()
        try:
            assert rendered.text == _expected_text
        except:
            if DEBUG_PRINT:
                print("------------")
                print(rendered.text)
                print("------------")
            raise

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def test_parse(self):
        _template = self.template
        _validate_kwargs: Dict = {}
        _reprint_kwargs: Dict = {}
        html_error_placeholder_template = None

        def _print_form_simple():
            rendered = render_to_response(_template, {"request": self.request})
            return rendered

        # render form A
        try:
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_EmailUsername,
                form_stash="a",
                **_validate_kwargs,
            )
            if html_error_placeholder_template:
                formStash.html_error_placeholder_template = (
                    html_error_placeholder_template
                )

            if not result:
                raise pyramid_formencode_classic.FormInvalid(formStash)

            raise ValueError(
                "`if not result:` should have raised `pyramid_formencode_classic.FormInvalid`"
            )

        except pyramid_formencode_classic.FormInvalid as exc:
            formStash.register_error_main_exception(exc)
            rendered = pyramid_formencode_classic.form_reprint(
                self.request, _print_form_simple, form_stash="a", **_reprint_kwargs
            )
            try:
                self.assertEqual(
                    rendered.text, self._test_data["response_text-test_parse-a"]
                )
            except:
                if DEBUG_PRINT:
                    print("----------------")
                    print("%s.test_parse" % self.__class__)
                    print(rendered.text)
                raise

        # render form B
        try:
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_EmailUsername,
                form_stash="b",
                **_validate_kwargs,
            )
            if html_error_placeholder_template:
                formStash.html_error_placeholder_template = (
                    html_error_placeholder_template
                )

            if not result:
                raise pyramid_formencode_classic.FormInvalid(formStash)

            raise ValueError(
                "`if not result:` should have raised `pyramid_formencode_classic.FormInvalid`"
            )

        except pyramid_formencode_classic.FormInvalid as exc:
            formStash.register_error_main_exception(exc)
            rendered = pyramid_formencode_classic.form_reprint(
                self.request, _print_form_simple, form_stash="b", **_reprint_kwargs
            )
            try:
                assert rendered.text == self._test_data["response_text-test_parse-b"]
            except:
                if DEBUG_PRINT:
                    print("----------------")
                    print("%s.test_parse" % self.__class__)
                    print(rendered.text)
                raise

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def test_parse_error(self):
        # set the submit
        self.request.POST["submit"] = "submit"
        self.request.POST["email"] = "failmail"
        self.request.POST["username"] = ""

        _template = self.template
        _validate_kwargs: Dict = {}
        _reprint_kwargs: Dict = {}
        html_error_placeholder_template = None

        def _print_form_simple():
            rendered = render_to_response(_template, {"request": self.request})
            return rendered

        # render form A
        try:
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_EmailUsername,
                form_stash="a",
                **_validate_kwargs,
            )
            if html_error_placeholder_template:
                formStash.html_error_placeholder_template = (
                    html_error_placeholder_template
                )

            if not result:
                raise pyramid_formencode_classic.FormInvalid(formStash)

            raise ValueError(
                "`if not result:` should have raised `pyramid_formencode_classic.FormInvalid`"
            )

        except pyramid_formencode_classic.FormInvalid as exc:
            formStash.register_error_main_exception(exc)
            rendered = pyramid_formencode_classic.form_reprint(
                self.request,
                _print_form_simple,
                form_stash="a",
                data_formencode_form="a",
                **_reprint_kwargs,
            )
            try:
                self.assertEqual(
                    rendered.text, self._test_data["response_text-test_parse_error-a"]
                )
            except:
                if DEBUG_PRINT:
                    print("----------------")
                    print("%s.test_parse_error" % self.__class__)
                    print(rendered.text)
                raise

        # render form B
        try:
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_EmailUsername,
                form_stash="b",
                **_validate_kwargs,
            )
            if html_error_placeholder_template:
                formStash.html_error_placeholder_template = (
                    html_error_placeholder_template
                )

            if not result:
                raise pyramid_formencode_classic.FormInvalid(formStash)

            raise ValueError(
                "`if not result:` should have raised `pyramid_formencode_classic.FormInvalid`"
            )

        except pyramid_formencode_classic.FormInvalid as exc:
            formStash.register_error_main_exception(exc)
            rendered = pyramid_formencode_classic.form_reprint(
                self.request,
                _print_form_simple,
                form_stash="b",
                data_formencode_form="b",
                **_reprint_kwargs,
            )
            try:
                assert (
                    rendered.text == self._test_data["response_text-test_parse_error-b"]
                )
            except:
                if DEBUG_PRINT:
                    print("----------------")
                    print("%s.test_parse_error" % self.__class__)
                    print(rendered.text)
                raise

    _test_data = {
        "response_text-test_render_simple": """\
<html><head></head><body><div>
<form action="/a" method="POST">
    
    
    <input type="text" name="email" value="" data-formencode-form="a"/>
    <input type="text" name="username" value="" data-formencode-form="a"/>
</form>
<form action="/b" method="POST">
    
    
    <input type="text" name="email" value="" data-formencode-form="b"/>
    <input type="text" name="username" value="" data-formencode-form="b"/>
</form>
</div></body></html>
""",
        "response_text-test_parse-a": """\
<html><head></head><body><div>
<form action="/a" method="POST">
    
    <span class="error-message">%s Nothing submitted.</span><br />

    <input type="text" name="email" value="" data-formencode-form="a" />
    <input type="text" name="username" value="" data-formencode-form="a" />
</form>
<form action="/b" method="POST">
    
    
    <input type="text" name="email" value="" data-formencode-form="b" />
    <input type="text" name="username" value="" data-formencode-form="b" />
</form>
</div></body></html>
"""
        % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        "response_text-test_parse-b": """\
<html><head></head><body><div>
<form action="/a" method="POST">
    
    <span class="error-message">%s Nothing submitted.</span><br />

    <input type="text" name="email" value="" data-formencode-form="a" />
    <input type="text" name="username" value="" data-formencode-form="a" />
</form>
<form action="/b" method="POST">
    
    <span class="error-message">%s Nothing submitted.</span><br />

    <input type="text" name="email" value="" data-formencode-form="b" />
    <input type="text" name="username" value="" data-formencode-form="b" />
</form>
</div></body></html>
"""
        % (_defaults.DEFAULT_ERROR_MAIN_TEXT, _defaults.DEFAULT_ERROR_MAIN_TEXT),
        "response_text-test_parse_error-a": """\
<html><head></head><body><div>
<form action="/a" method="POST">
    
    <span class="error-message">%s</span><br />

    <!-- for: email -->
<span class="error-message">An email address must contain a single @</span>
<input type="text" name="email" value="failmail" data-formencode-form="a" class="error" />
    <!-- for: username -->
<span class="error-message">Please enter a value</span>
<input type="text" name="username" value="" data-formencode-form="a" class="error" />
</form>
<form action="/b" method="POST">
    
    
    <input type="text" name="email" value="" data-formencode-form="b"/>
    <input type="text" name="username" value="" data-formencode-form="b"/>
</form>
</div></body></html>
"""
        % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        "response_text-test_parse_error-b": """\
<html><head></head><body><div>
<form action="/a" method="POST">
    
    <form:error name="Error_Main" data-formencode-form="a"/>
    <input type="text" name="email" value="" data-formencode-form="a"/>
    <input type="text" name="username" value="" data-formencode-form="a"/>
</form>
<form action="/b" method="POST">
    
    <span class="error-message">%s</span><br />

    <!-- for: email -->
<span class="error-message">An email address must contain a single @</span>
<input type="text" name="email" value="failmail" data-formencode-form="b" class="error" />
    <!-- for: username -->
<span class="error-message">Please enter a value</span>
<input type="text" name="username" value="" data-formencode-form="b" class="error" />
</form>
</div></body></html>
"""
        % _defaults.DEFAULT_ERROR_MAIN_TEXT,
    }


class _TestParsingApi040(object):
    """

    python -munittest pyramid_formencode_classic.tests.core.TestParsingApi040_FormA_HtmlErrorPlaceholder_Default
    """

    error_main_key = None
    template: str
    request: Request

    _test_manual_error_append__data: Dict  # placeholder
    _test_manual_error_prepend__data: Dict  # placeholder
    _test_manual_error_default__data: Dict  # placeholder
    _test_fatal_form__data: Dict  # placeholder
    _test_fatal_field__data: Dict  # placeholder
    _test_raise_form_aware__data: Dict  # placeholder

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def test_manual_error_default(self):
        # set the submit
        self.request.POST["submit"] = "submit"

        tests_completed = []
        tests_fail = []
        for test_name, test_data in self._test_manual_error_default__data.items():
            _template = self.template
            _expected_text = test_data["response_text"]
            _reprint_kwargs: Dict = {}
            if "auto_error_formatter" in test_data:
                _reprint_kwargs["auto_error_formatter"] = test_data[
                    "auto_error_formatter"
                ]
            if "error_formatters" in test_data:
                if test_data["error_formatters"] is not None:
                    _reprint_kwargs["error_formatters"] = test_data["error_formatters"]
            _validate_kwargs: Dict = {}
            if self.error_main_key is not None:
                _validate_kwargs["error_main_key"] = self.error_main_key

            def _print_form_simple():
                rendered = render_to_response(_template, {"request": self.request})
                return rendered

            try:
                (result, formStash) = pyramid_formencode_classic.form_validate(
                    self.request,
                    schema=Form_EmailUsername,
                    **_validate_kwargs,
                )
                if not result:
                    raise pyramid_formencode_classic.FormInvalid(
                        formStash, "OVERRIDE MESSAGE."
                    )

                raise ValueError(
                    "`if not result:` should have raised `pyramid_formencode_classic.FormInvalid`"
                )

            except pyramid_formencode_classic.FormInvalid as exc:
                formStash.register_error_main_exception(exc)
                formStash.register_error_main_exception(
                    exc
                )  # this can be repeated because we defend against it
                rendered = pyramid_formencode_classic.form_reprint(
                    self.request, _print_form_simple, **_reprint_kwargs
                )
                try:
                    assert rendered.text == _expected_text
                except:
                    if DEBUG_PRINT:
                        print("------------")
                        print("%s.test_manual_error_default" % self.__class__)
                        print(test_name)
                        print(rendered.text)
                    tests_fail.append(test_name)
            tests_completed.append(test_name)

        if tests_fail:
            raise ValueError(tests_fail)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def test_manual_error_append(self):
        # set the submit
        self.request.POST["submit"] = "submit"

        tests_completed = []
        tests_fail = []
        for test_name, test_data in self._test_manual_error_append__data.items():
            _template = self.template
            _expected_text = test_data["response_text"]
            _reprint_kwargs: Dict = {}
            if "auto_error_formatter" in test_data:
                _reprint_kwargs["auto_error_formatter"] = test_data[
                    "auto_error_formatter"
                ]
            if "error_formatters" in test_data:
                if test_data["error_formatters"] is not None:
                    _reprint_kwargs["error_formatters"] = test_data["error_formatters"]
            _validate_kwargs: Dict = {}
            if self.error_main_key is not None:
                _validate_kwargs["error_main_key"] = self.error_main_key

            def _print_form_simple():
                rendered = render_to_response(_template, {"request": self.request})
                return rendered

            try:
                (result, formStash) = pyramid_formencode_classic.form_validate(
                    self.request,
                    schema=Form_EmailUsername,
                    **_validate_kwargs,
                )
                if not result:
                    raise pyramid_formencode_classic.FormInvalid(
                        formStash, "OVERRIDE MESSAGE."
                    )

                raise ValueError(
                    "`if not result:` should have raised `pyramid_formencode_classic.FormInvalid`"
                )

            except pyramid_formencode_classic.FormInvalid as exc:
                formStash.register_error_main_exception(
                    exc, error_main_append=True, error_main_prepend=False
                )
                formStash.register_error_main_exception(
                    exc
                )  # this can be repeated because we defend against it
                rendered = pyramid_formencode_classic.form_reprint(
                    self.request, _print_form_simple, **_reprint_kwargs
                )
                try:
                    assert rendered.text == _expected_text
                except:
                    if DEBUG_PRINT:
                        print("------------")
                        print("%s.test_manual_error_append" % self.__class__)
                        print(test_name)
                        print(rendered.text)
                    tests_fail.append(test_name)
            tests_completed.append(test_name)

        if tests_fail:
            raise ValueError(tests_fail)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def test_manual_error_prepend(self):
        # set the submit
        self.request.POST["submit"] = "submit"

        tests_completed = []
        tests_fail = []
        for test_name, test_data in self._test_manual_error_prepend__data.items():
            _template = self.template
            _expected_text = test_data["response_text"]
            _reprint_kwargs: Dict = {}
            if "auto_error_formatter" in test_data:
                _reprint_kwargs["auto_error_formatter"] = test_data[
                    "auto_error_formatter"
                ]
            if "error_formatters" in test_data:
                if test_data["error_formatters"] is not None:
                    _reprint_kwargs["error_formatters"] = test_data["error_formatters"]
            _validate_kwargs: Dict = {}
            if self.error_main_key is not None:
                _validate_kwargs["error_main_key"] = self.error_main_key

            def _print_form_simple():
                rendered = render_to_response(_template, {"request": self.request})
                return rendered

            try:
                (result, formStash) = pyramid_formencode_classic.form_validate(
                    self.request,
                    schema=Form_EmailUsername,
                    **_validate_kwargs,
                )
                if not result:
                    raise pyramid_formencode_classic.FormInvalid(
                        formStash,
                        "OVERRIDE MESSAGE.",
                        error_main_append=False,
                        error_main_prepend=True,
                    )

                raise ValueError(
                    "`if not result:` should have raised `pyramid_formencode_classic.FormInvalid`"
                )

            except pyramid_formencode_classic.FormInvalid as exc:
                formStash.register_error_main_exception(
                    exc, error_main_append=False, error_main_prepend=True
                )
                formStash.register_error_main_exception(
                    exc
                )  # this can be repeated because we defend against it
                rendered = pyramid_formencode_classic.form_reprint(
                    self.request, _print_form_simple, **_reprint_kwargs
                )
                try:
                    assert rendered.text == _expected_text
                except:
                    if DEBUG_PRINT:
                        print("===========================")
                        print("%s.test_manual_error_prepend" % self.__class__)
                        print("------------")
                        print(test_name)
                        print("------------")
                        print(rendered.text)
                        print("------------")
                        print(_expected_text)
                        print("===========================")
                    tests_fail.append(test_name)
            tests_completed.append(test_name)

        if tests_fail:
            raise ValueError(tests_fail)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def test_fatal_form(self):
        # set the submit
        self.request.POST["submit"] = "submit"

        tests_completed = []
        tests_fail = []
        for test_name, test_data in self._test_fatal_form__data.items():
            _template = self.template
            _expected_text = test_data["response_text"]
            _reprint_kwargs: Dict = {}
            if "auto_error_formatter" in test_data:
                _reprint_kwargs["auto_error_formatter"] = test_data[
                    "auto_error_formatter"
                ]
            if "error_formatters" in test_data:
                if test_data["error_formatters"] is not None:
                    _reprint_kwargs["error_formatters"] = test_data["error_formatters"]
            _validate_kwargs: Dict = {}
            if self.error_main_key is not None:
                _validate_kwargs["error_main_key"] = self.error_main_key

            def _print_form_simple():
                rendered = render_to_response(_template, {"request": self.request})
                return rendered

            try:
                (result, formStash) = pyramid_formencode_classic.form_validate(
                    self.request,
                    schema=Form_EmailUsername,
                    **_validate_kwargs,
                )
                formStash.fatal_form(error_main="FATAL FORM.")

                raise ValueError(
                    "`if not result:` should have raised `pyramid_formencode_classic.FormInvalid`"
                )

            except pyramid_formencode_classic.FormInvalid as exc:
                rendered = pyramid_formencode_classic.form_reprint(
                    self.request, _print_form_simple, **_reprint_kwargs
                )
                try:
                    assert rendered.text == _expected_text
                except:
                    if DEBUG_PRINT:
                        print("====================================")
                        print("%s.test_fatal_form" % self.__class__)
                        print("------------")
                        print(test_name)
                        print("------------")
                        print(rendered.text)
                        print("------------")
                        print(_expected_text)
                        print("====================================")
                    tests_fail.append(test_name)

                # oh hey, do it again after integrating the error
                formStash.register_error_main_exception(
                    exc
                )  # this can be repeated because we defend against it
                rendered_alt = pyramid_formencode_classic.form_reprint(
                    self.request, _print_form_simple, **_reprint_kwargs
                )
                try:
                    assert rendered_alt.text == _expected_text
                except:
                    if DEBUG_PRINT:
                        print("====================================")
                        print("alt, %s.test_fatal_form" % self.__class__)
                        print("------------")
                        print(test_name)
                        print("------------")
                        print(rendered.text)
                        print("------------")
                        print(_expected_text)
                        print("====================================")
                    tests_fail.append("alt, %s" % test_name)

            tests_completed.append(test_name)

        if tests_fail:
            raise ValueError(tests_fail)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def test_fatal_field(self):
        # set the submit
        self.request.POST["submit"] = "submit"

        tests_completed = []
        tests_fail = []
        for test_name, test_data in self._test_fatal_field__data.items():
            _template = self.template
            _expected_text = test_data["response_text"]
            _reprint_kwargs: Dict = {}
            if "auto_error_formatter" in test_data:
                _reprint_kwargs["auto_error_formatter"] = test_data[
                    "auto_error_formatter"
                ]
            if "error_formatters" in test_data:
                if test_data["error_formatters"] is not None:
                    _reprint_kwargs["error_formatters"] = test_data["error_formatters"]
            _validate_kwargs: Dict = {}
            if self.error_main_key is not None:
                _validate_kwargs["error_main_key"] = self.error_main_key

            def _print_form_simple():
                rendered = render_to_response(_template, {"request": self.request})
                return rendered

            try:
                (result, formStash) = pyramid_formencode_classic.form_validate(
                    self.request,
                    schema=Form_EmailUsername,
                    **_validate_kwargs,
                )
                formStash.fatal_field(
                    field="email", error_field="THIS FIELD CAUSED A FATAL ERROR."
                )

                raise ValueError(
                    "`formStash.fatal_field` should have raised `pyramid_formencode_classic.FormInvalid`"
                )

            except pyramid_formencode_classic.FormInvalid as exc:
                rendered = pyramid_formencode_classic.form_reprint(
                    self.request, _print_form_simple, **_reprint_kwargs
                )
                try:
                    assert rendered.text == _expected_text
                except:
                    if DEBUG_PRINT:
                        print("====================================")
                        print("%s.test_fatal_field" % self.__class__)
                        print("------------")
                        print(test_name)
                        print("------------")
                        print(rendered.text)
                        print("------------")
                        print(_expected_text)
                        print("====================================")
                    tests_fail.append(test_name)

                # oh hey, do it again after integrating the error
                formStash.register_error_main_exception(
                    exc
                )  # this can be repeated because we defend against it
                rendered_alt = pyramid_formencode_classic.form_reprint(
                    self.request, _print_form_simple, **_reprint_kwargs
                )
                try:
                    assert rendered_alt.text == _expected_text
                except:
                    if DEBUG_PRINT:
                        print("------------")
                        print("alt, %s.test_fatal_field" % self.__class__)
                        print(test_name)
                        print(rendered.text)
                    tests_fail.append("alt, %s" % test_name)

            tests_completed.append(test_name)

        if tests_fail:
            raise ValueError(tests_fail)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def test_raise_form_aware(self):
        # set the submit
        self.request.POST["submit"] = "submit"

        tests_completed = []
        tests_fail = []
        for test_name, test_data in self._test_raise_form_aware__data.items():
            _template = self.template
            _expected_text = test_data["response_text"]
            _reprint_kwargs: Dict = {}
            if "auto_error_formatter" in test_data:
                _reprint_kwargs["auto_error_formatter"] = test_data[
                    "auto_error_formatter"
                ]
            if "error_formatters" in test_data:
                if test_data["error_formatters"] is not None:
                    _reprint_kwargs["error_formatters"] = test_data["error_formatters"]
            _validate_kwargs: Dict = {}
            if self.error_main_key is not None:
                _validate_kwargs["error_main_key"] = self.error_main_key

            def _print_form_simple():
                rendered = render_to_response(_template, {"request": self.request})
                return rendered

            try:
                (result, formStash) = pyramid_formencode_classic.form_validate(
                    self.request,
                    schema=Form_EmailUsername,
                    **_validate_kwargs,
                )
                if not result:
                    raise pyramid_formencode_classic.FormInvalid(
                        formStash, "OVERRIDE MESSAGE."
                    )

                raise ValueError(
                    "`if not result:` should have raised `pyramid_formencode_classic.FormInvalid`"
                )

            except pyramid_formencode_classic.FormInvalid as exc:  # noqa: F841
                rendered = pyramid_formencode_classic.form_reprint(
                    self.request, _print_form_simple, **_reprint_kwargs
                )
                try:
                    assert rendered.text == _expected_text
                except:
                    if DEBUG_PRINT:
                        print("============")
                        print("%s.test_raise_form_aware" % self.__class__)
                        print(test_name)
                        print("------------")
                        print(rendered.text)
                        print("------------")
                        print(_expected_text)
                        print("============")
                    tests_fail.append(test_name)
            tests_completed.append(test_name)

        if tests_fail:
            raise ValueError(tests_fail)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


class TestParsingApi040_FormA_HtmlErrorPlaceholder_Default(
    _TestParsingApi040, _TestHarness, unittest.TestCase
):
    template = "fixtures/form_a-html_error_placeholder-default.mako"

    # note: _test_manual_error_append__data
    _test_manual_error_append__data = {
        "test_formatter_default": {
            # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
            "error_formatters": None,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s OVERRIDE MESSAGE.</span><br />

    <!-- for: email -->
<span class="error-message">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_nobr": {
            "auto_error_formatter": formatters.formatter_nobr,
            "error_formatters": {"default": formatters.formatter_nobr},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s OVERRIDE MESSAGE.</span>

    <!-- for: email -->
<span class="error-message">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_is_none": {
            "auto_error_formatter": None,
            "error_formatters": None,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s OVERRIDE MESSAGE.</span><br />

    <!-- for: email -->
<span class="error-message">Missing value</span><br />
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span><br />
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_comment": {
            "auto_error_formatter": formatters.formatter_comment,
            "error_formatters": {"default": formatters.formatter_comment},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- formatter_comment (%s OVERRIDE MESSAGE.)-->
    <!-- for: email -->
<!-- formatter_comment (Missing value)--><input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<!-- formatter_comment (Missing value)--><input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_help_inline": {
            "auto_error_formatter": formatters.formatter_help_inline,
            "error_formatters": {"default": formatters.formatter_help_inline},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="help-inline">%s OVERRIDE MESSAGE.</span>

    <!-- for: email -->
<span class="help-inline">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="help-inline">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_empty_string": {
            "auto_error_formatter": formatters.formatter_empty_string,
            "error_formatters": {"default": formatters.formatter_empty_string},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    
    <!-- for: email -->
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
""",
        },
        "formatter_hidden": {
            "auto_error_formatter": formatters.formatter_hidden,
            "error_formatters": {"default": formatters.formatter_hidden},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="hidden" value="%s OVERRIDE MESSAGE." />

    <!-- for: email -->
<input type="hidden" value="Missing value" />
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<input type="hidden" value="Missing value" />
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
    }

    # note: _test_manual_error_prepend__data
    _test_manual_error_prepend__data = {
        "test_formatter_default": {
            # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
            "error_formatters": None,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">OVERRIDE MESSAGE. %s</span><br />

    <!-- for: email -->
<span class="error-message">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_nobr": {
            "auto_error_formatter": formatters.formatter_nobr,
            "error_formatters": {"default": formatters.formatter_nobr},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">OVERRIDE MESSAGE. %s</span>

    <!-- for: email -->
<span class="error-message">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_is_none": {
            "auto_error_formatter": None,
            "error_formatters": None,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">OVERRIDE MESSAGE. %s</span><br />

    <!-- for: email -->
<span class="error-message">Missing value</span><br />
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span><br />
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_comment": {
            "auto_error_formatter": formatters.formatter_comment,
            "error_formatters": {"default": formatters.formatter_comment},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- formatter_comment (OVERRIDE MESSAGE. %s)-->
    <!-- for: email -->
<!-- formatter_comment (Missing value)--><input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<!-- formatter_comment (Missing value)--><input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_help_inline": {
            "auto_error_formatter": formatters.formatter_help_inline,
            "error_formatters": {"default": formatters.formatter_help_inline},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="help-inline">OVERRIDE MESSAGE. %s</span>

    <!-- for: email -->
<span class="help-inline">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="help-inline">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_empty_string": {
            "auto_error_formatter": formatters.formatter_empty_string,
            "error_formatters": {"default": formatters.formatter_empty_string},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    
    <!-- for: email -->
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
""",
        },
        "formatter_hidden": {
            "auto_error_formatter": formatters.formatter_hidden,
            "error_formatters": {"default": formatters.formatter_hidden},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="hidden" value="OVERRIDE MESSAGE. %s" />

    <!-- for: email -->
<input type="hidden" value="Missing value" />
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<input type="hidden" value="Missing value" />
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
    }

    # note: _test_manual_error_default__data
    _test_manual_error_default__data = _test_manual_error_append__data

    # note: _test_fatal_form__data
    _test_fatal_form__data = {
        "test_formatter_default": {
            # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
            "error_formatters": None,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">FATAL FORM.</span><br />

    <!-- for: email -->
<span class="error-message">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
""",
        },
        "test_formatter_nobr": {
            "auto_error_formatter": formatters.formatter_nobr,
            "error_formatters": {"default": formatters.formatter_nobr},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">FATAL FORM.</span>

    <!-- for: email -->
<span class="error-message">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
""",
        },
        "test_formatter_is_none": {
            "auto_error_formatter": None,
            "error_formatters": None,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">FATAL FORM.</span><br />

    <!-- for: email -->
<span class="error-message">Missing value</span><br />
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span><br />
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
""",
        },
        "formatter_comment": {
            "auto_error_formatter": formatters.formatter_comment,
            "error_formatters": {"default": formatters.formatter_comment},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- formatter_comment (FATAL FORM.)-->
    <!-- for: email -->
<!-- formatter_comment (Missing value)--><input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<!-- formatter_comment (Missing value)--><input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
""",
        },
        "formatter_help_inline": {
            "auto_error_formatter": formatters.formatter_help_inline,
            "error_formatters": {"default": formatters.formatter_help_inline},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="help-inline">FATAL FORM.</span>

    <!-- for: email -->
<span class="help-inline">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="help-inline">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
""",
        },
        "formatter_empty_string": {
            "auto_error_formatter": formatters.formatter_empty_string,
            "error_formatters": {"default": formatters.formatter_empty_string},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    
    <!-- for: email -->
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
""",
        },
        "formatter_hidden": {
            "auto_error_formatter": formatters.formatter_hidden,
            "error_formatters": {"default": formatters.formatter_hidden},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="hidden" value="FATAL FORM." />

    <!-- for: email -->
<input type="hidden" value="Missing value" />
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<input type="hidden" value="Missing value" />
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
""",
        },
    }

    # note: _test_fatal_field__data
    _test_fatal_field__data = {
        "test_formatter_default": {
            # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
            "error_formatters": None,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s</span><br />

    <!-- for: email -->
<span class="error-message">Missing value THIS FIELD CAUSED A FATAL ERROR.</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_nobr": {
            "auto_error_formatter": formatters.formatter_nobr,
            "error_formatters": {"default": formatters.formatter_nobr},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s</span>

    <!-- for: email -->
<span class="error-message">Missing value THIS FIELD CAUSED A FATAL ERROR.</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_is_none": {
            "auto_error_formatter": None,
            "error_formatters": None,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s</span><br />

    <!-- for: email -->
<span class="error-message">Missing value THIS FIELD CAUSED A FATAL ERROR.</span><br />
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span><br />
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_comment": {
            "auto_error_formatter": formatters.formatter_comment,
            "error_formatters": {"default": formatters.formatter_comment},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- formatter_comment (%s)-->
    <!-- for: email -->
<!-- formatter_comment (Missing value THIS FIELD CAUSED A FATAL ERROR.)--><input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<!-- formatter_comment (Missing value)--><input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_help_inline": {
            "auto_error_formatter": formatters.formatter_help_inline,
            "error_formatters": {"default": formatters.formatter_help_inline},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="help-inline">%s</span>

    <!-- for: email -->
<span class="help-inline">Missing value THIS FIELD CAUSED A FATAL ERROR.</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="help-inline">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_empty_string": {
            "auto_error_formatter": formatters.formatter_empty_string,
            "error_formatters": {"default": formatters.formatter_empty_string},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    
    <!-- for: email -->
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
""",
        },
        "formatter_hidden": {
            "auto_error_formatter": formatters.formatter_hidden,
            "error_formatters": {"default": formatters.formatter_hidden},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="hidden" value="%s" />

    <!-- for: email -->
<input type="hidden" value="Missing value THIS FIELD CAUSED A FATAL ERROR." />
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<input type="hidden" value="Missing value" />
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
    }

    # note: _test_raise_form_aware__data
    _test_raise_form_aware__data = {
        "test_formatter_default": {
            # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
            "error_formatters": None,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s OVERRIDE MESSAGE.</span><br />

    <!-- for: email -->
<span class="error-message">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_nobr": {
            "auto_error_formatter": formatters.formatter_nobr,
            "error_formatters": {"default": formatters.formatter_nobr},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s OVERRIDE MESSAGE.</span>

    <!-- for: email -->
<span class="error-message">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "test_formatter_is_none": {
            "auto_error_formatter": None,
            "error_formatters": None,
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s OVERRIDE MESSAGE.</span><br />

    <!-- for: email -->
<span class="error-message">Missing value</span><br />
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span><br />
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_comment": {
            "auto_error_formatter": formatters.formatter_comment,
            "error_formatters": {"default": formatters.formatter_comment},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- formatter_comment (%s OVERRIDE MESSAGE.)-->
    <!-- for: email -->
<!-- formatter_comment (Missing value)--><input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<!-- formatter_comment (Missing value)--><input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_help_inline": {
            "auto_error_formatter": formatters.formatter_help_inline,
            "error_formatters": {"default": formatters.formatter_help_inline},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="help-inline">%s OVERRIDE MESSAGE.</span>

    <!-- for: email -->
<span class="help-inline">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="help-inline">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
        "formatter_empty_string": {
            "auto_error_formatter": formatters.formatter_empty_string,
            "error_formatters": {"default": formatters.formatter_empty_string},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    
    <!-- for: email -->
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
""",
        },
        "formatter_hidden": {
            "auto_error_formatter": formatters.formatter_hidden,
            "error_formatters": {"default": formatters.formatter_hidden},
            "response_text": """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="hidden" value="%s OVERRIDE MESSAGE." />

    <!-- for: email -->
<input type="hidden" value="Missing value" />
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<input type="hidden" value="Missing value" />
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
            % _defaults.DEFAULT_ERROR_MAIN_TEXT,
        },
    }


class TestRenderJson(_TestHarness, unittest.TestCase):
    """
    python -munittest pyramid_formencode_classic.tests.core.TestRenderJson
    """

    template = "fixtures/form_a-html_error_placeholder-default.mako"
    rendered = (
        """<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">%s</span><br />

    <!-- for: email -->
<span class="error-message">Missing value</span>
<input type="text" name="email" value="" class="error" />
    <!-- for: username -->
<span class="error-message">Missing value</span>
<input type="text" name="username" value="" class="error" />
</form>
</div></body></html>
"""
        % _defaults.DEFAULT_ERROR_MAIN_TEXT
    )

    def test_submit(self):
        # set the submit
        self.request.POST["submit"] = "submit"

        # _template = self.template
        _rendered = self.rendered
        _reprint_kwargs: Dict = {}
        _validate_kwargs: Dict = {}

        def _print_form__valid():
            rendered = render_to_response(self.template, {"request": self.request})
            return rendered

        def _print_form__fail():
            unrendered = {"request": self.request}
            return unrendered

        # first print this RIGHT
        try:
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_EmailUsername,
                **_validate_kwargs,
            )
            if not result:
                raise pyramid_formencode_classic.FormInvalid(formStash)

            raise ValueError(
                "`if not result:` should have raised `pyramid_formencode_classic.FormInvalid`"
            )

        except pyramid_formencode_classic.FormInvalid as exc:
            formStash.register_error_main_exception(exc)
            rendered = pyramid_formencode_classic.form_reprint(
                self.request, _print_form__valid, **_reprint_kwargs
            )
            self.assertEqual(rendered.text, _rendered)

        # then print this WRONG
        try:
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_EmailUsername,
                **_validate_kwargs,
            )
            if not result:
                raise pyramid_formencode_classic.FormInvalid(formStash)

            raise ValueError(
                "`if not result:` should have raised `pyramid_formencode_classic.FormInvalid`"
            )

        except pyramid_formencode_classic.FormInvalid as exc:
            formStash.register_error_main_exception(exc)
            try:
                rendered = pyramid_formencode_classic.form_reprint(
                    self.request, _print_form__fail, **_reprint_kwargs
                )
                raise ValueError("`form_reprint` should have raised a `ValueError`")
            except ValueError as exc:
                print(exc.args[0])
                assert (
                    exc.args[0]
                    == """`form_reprint` must be invoked with functions which generate a `Pyramid.response.Response` or provides the interface `pyramid.interfaces.IResponse`."""
                )


class Test_ExceptionsApi(_TestHarness, unittest.TestCase):

    def test_valid_manual(self):

        self.request.POST["email"] = "a@example.com"
        self.request.POST["username"] = "abcdefg"
        try:
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_Email,
            )
            if not result:
                raise pyramid_formencode_classic.FormInvalid(formStash)
            assert result
        except Exception:
            raise

    def test_valid_automatic(self):

        self.request.POST["email"] = "a@example.com"
        self.request.POST["username"] = "abcdefg"
        try:
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_Email,
                raise_FormInvalid=True,
            )
            assert result
        except Exception:
            raise

    # ==========================================================================

    def test_raise_FormInvalid_manual(self):
        try:
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_Email,
            )
            if not result:
                raise pyramid_formencode_classic.FormInvalid(formStash)

            raise ValueError(
                "`if not result:` should have raised `pyramid_formencode_classic.FormInvalid`"
            )

        except pyramid_formencode_classic.FormInvalid as exc:
            assert isinstance(exc.formStash, pyramid_formencode_classic.FormStash)
            assert exc.raised_by is None
            self.assertEqual(
                exc.error_main,
                _defaults.DEFAULT_ERROR_MAIN_TEXT,
            )
            assert len(exc.formStash.errors) == 1
            self.assertEqual(
                exc.formStash.errors["Error_Main"],
                ("%s Nothing submitted." % _defaults.DEFAULT_ERROR_MAIN_TEXT),
            )

    def test_raise_FormInvalid_automatic(self):
        try:
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_Email,
                raise_FormInvalid=True,
            )

            raise ValueError(
                "`form_validate[raise_FormInvalid]` should have raised `pyramid_formencode_classic.FormInvalid`"
            )

        except pyramid_formencode_classic.FormInvalid as exc:
            assert isinstance(exc.formStash, pyramid_formencode_classic.FormStash)
            assert exc.raised_by == "_form_validate_core"
            self.assertEqual(
                exc.error_main,
                _defaults.DEFAULT_ERROR_MAIN_TEXT,
            )
            assert len(exc.formStash.errors) == 1
            self.assertEqual(
                exc.formStash.errors["Error_Main"],
                ("%s Nothing submitted." % _defaults.DEFAULT_ERROR_MAIN_TEXT),
            )

    def test_raise_FormInvalid_manual__custom_message(self):
        message = "GarfieldMinusGarfield"
        try:
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_Email,
            )
            if not result:
                raise pyramid_formencode_classic.FormInvalid(
                    formStash, error_main=message
                )

            raise ValueError(
                "`if not result:` should have raised `pyramid_formencode_classic.FormInvalid`"
            )

        except pyramid_formencode_classic.FormInvalid as exc:
            assert isinstance(exc.formStash, pyramid_formencode_classic.FormStash)
            assert exc.raised_by is None
            assert exc.error_main == message
            assert len(exc.formStash.errors) == 1
            self.assertEqual(
                exc.formStash.errors["Error_Main"],
                ("%s Nothing submitted." % message),
            )

    # ==========================================================================

    def test_FormStash_fatalForm_defaultMessage(self):
        self.request.POST["email"] = "a@example.com"
        self.request.POST["username"] = "abcdefg"
        try:
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_Email,
            )
            if not result:
                raise pyramid_formencode_classic.FormInvalid(formStash)

            formStash.fatal_form()

            raise ValueError(
                "`fatal_form` should have raised `pyramid_formencode_classic.FormInvalid`"
            )

        except pyramid_formencode_classic.FormInvalid as exc:
            assert isinstance(exc.formStash, pyramid_formencode_classic.FormStash)
            assert exc.raised_by == "fatal_form"
            self.assertEqual(
                exc.error_main,
                _defaults.DEFAULT_ERROR_MAIN_TEXT,
            )
            assert len(exc.formStash.errors) == 1
            self.assertEqual(
                exc.formStash.errors["Error_Main"],
                _defaults.DEFAULT_ERROR_MAIN_TEXT,
            )

    def test_FormStash_fatalForm_customMessage(self):
        message = "foo"
        self.request.POST["email"] = "a@example.com"
        self.request.POST["username"] = "abcdefg"
        try:
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_Email,
            )
            if not result:
                raise pyramid_formencode_classic.FormInvalid(formStash)

            formStash.fatal_form(message)

            raise ValueError(
                "`fatal_form` should have raised `pyramid_formencode_classic.FormInvalid`"
            )

        except pyramid_formencode_classic.FormInvalid as exc:
            assert isinstance(exc.formStash, pyramid_formencode_classic.FormStash)
            assert exc.raised_by == "fatal_form"
            assert exc.error_main == message
            assert len(exc.formStash.errors) == 1
            self.assertEqual(
                exc.formStash.errors["Error_Main"],
                message,
            )

    def test_FormStash_fatalField(self):
        self.request.POST["email"] = "a@example.com"
        self.request.POST["username"] = "abcdefg"
        message = "THIS FIELD CAUSED A FATAL ERROR"
        field = "email"
        try:
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_Email,
                raise_FormInvalid=True,
            )

            formStash.fatal_field(field=field, error_field=message)

            raise ValueError(
                "`formStash.fatal_field` should have raised `pyramid_formencode_classic.FormInvalid`"
            )

        except pyramid_formencode_classic.FormInvalid as exc:
            assert isinstance(exc.formStash, pyramid_formencode_classic.FormStash)
            assert exc.raised_by == "fatal_field"
            self.assertEqual(exc.error_main, _defaults.DEFAULT_ERROR_MAIN_TEXT)
            assert len(exc.formStash.errors) == 2
            self.assertEqual(exc.formStash.errors[field], message)
            self.assertEqual(
                exc.formStash.errors["Error_Main"],
                _defaults.DEFAULT_ERROR_MAIN_TEXT,
            )

    def test_FormStash_fatalField_manual_noField(self):
        self.request.POST["email"] = "a@example.com"
        self.request.POST["username"] = "abcdefg"
        message = "THIS FIELD CAUSED A FATAL ERROR"
        # field = "email"
        try:
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_Email,
                raise_FormInvalid=True,
            )

            try:
                formStash.fatal_field(error_field=message)  # type:ignore[call-arg]
                raise ValueError(
                    "`formStash.fatal_field` should have raised `TypeError`"
                )
            except TypeError as exc:
                _exc_expected_msg: str
                if sys.version_info < 3.9:
                    # this affects py38
                    _exc_expected_msg = (
                        "fatal_field() missing 1 required positional argument: 'field'"
                    )
                else:
                    _exc_expected_msg = "FormStash.fatal_field() missing 1 required positional argument: 'field'"
                self.assertEqual(exc.args[0], _exc_expected_msg)

            try:
                formStash.fatal_field(field="unknown", error_field=message)
                raise ValueError(
                    "`formStash.fatal_field` should have raised `ValueError`"
                )
            except ValueError as exc:
                assert (
                    exc.args[0]
                    == "field `unknown` is not in schema: `<class 'tests.test_core.Form_Email'>`"
                )

            try:
                formStash.fatal_field(
                    field="unknown", error_field=message, allow_unknown_fields=True
                )
                raise ValueError(
                    "`formStash.fatal_field` should have raised `FormInvalid`"
                )
            except pyramid_formencode_classic.FormInvalid as exc:
                assert isinstance(exc.formStash, pyramid_formencode_classic.FormStash)
                assert exc.raised_by == "fatal_field"
                assert exc.error_main == _defaults.DEFAULT_ERROR_MAIN_TEXT
                assert (
                    exc.formStash.errors["Error_Main"]
                    == _defaults.DEFAULT_ERROR_MAIN_TEXT
                )
                assert exc.formStash.errors["unknown"] == message
        except Exception:
            raise

    def test_FormStash_fatalField_args(self):
        self.request.POST["email"] = "a@example.com"
        self.request.POST["username"] = "abcdefg"
        message = "THIS FIELD CAUSED A FATAL ERROR"
        message_alt = "[[this field caused a fatal error]]"
        error_main = "[{{[CUSTOM_ERROR_MAIN]}}]"

        # note: base
        try:
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_Email,
                raise_FormInvalid=True,
            )
            try:
                formStash.fatal_field(field="email", error_field=message)
                raise ValueError(
                    "`formStash.fatal_field` should have raised `FormInvalid`"
                )
            except pyramid_formencode_classic.FormInvalid as exc:
                assert isinstance(exc.formStash, pyramid_formencode_classic.FormStash)
                assert exc.raised_by == "fatal_field"
                assert exc.error_main == _defaults.DEFAULT_ERROR_MAIN_TEXT
                assert (
                    exc.formStash.errors["Error_Main"]
                    == _defaults.DEFAULT_ERROR_MAIN_TEXT
                )
                assert exc.formStash.errors["email"] == message
        except Exception:
            raise

        # note: error_main
        try:
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_Email,
                raise_FormInvalid=True,
            )
            try:
                formStash.fatal_field(
                    field="email", error_field=message, error_main=error_main
                )
                raise ValueError(
                    "`formStash.fatal_field` should have raised `FormInvalid`"
                )
            except pyramid_formencode_classic.FormInvalid as exc:
                assert isinstance(exc.formStash, pyramid_formencode_classic.FormStash)
                assert exc.raised_by == "fatal_field"
                assert exc.error_main == error_main
                assert exc.formStash.errors["Error_Main"] == error_main
                assert exc.formStash.errors["email"] == message
        except Exception:
            raise

        # note: message_overwrite
        try:
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_Email,
                raise_FormInvalid=True,
            )
            try:
                formStash.set_error(field="email", message=message_alt)
                formStash.fatal_field(
                    field="email",
                    error_field=message,
                    error_main=error_main,
                    message_overwrite=True,
                    message_append=False,
                )
                raise ValueError(
                    "`formStash.fatal_field` should have raised `FormInvalid`"
                )
            except pyramid_formencode_classic.FormInvalid as exc:
                assert isinstance(exc.formStash, pyramid_formencode_classic.FormStash)
                assert exc.raised_by == "fatal_field"
                assert exc.error_main == error_main
                assert exc.formStash.errors["Error_Main"] == error_main
                assert exc.formStash.errors["email"] == message
        except Exception:
            raise

        # note: message_append - implicit
        try:
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_Email,
                raise_FormInvalid=True,
            )
            try:
                formStash.set_error(field="email", message=message_alt)
                formStash.fatal_field(field="email", error_field=message)
                raise ValueError(
                    "`formStash.fatal_field` should have raised `FormInvalid`"
                )
            except pyramid_formencode_classic.FormInvalid as exc:
                assert isinstance(exc.formStash, pyramid_formencode_classic.FormStash)
                assert exc.raised_by == "fatal_field"
                assert exc.error_main == _defaults.DEFAULT_ERROR_MAIN_TEXT
                assert (
                    exc.formStash.errors["Error_Main"]
                    == _defaults.DEFAULT_ERROR_MAIN_TEXT
                )
                assert exc.formStash.errors["email"] == "%s %s" % (message_alt, message)
        except Exception:
            raise

        # note: message_append - explicit
        try:
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_Email,
                raise_FormInvalid=True,
            )
            try:
                formStash.set_error(field="email", message=message_alt)
                formStash.fatal_field(
                    field="email", error_field=message, message_append=True
                )
                raise ValueError(
                    "`formStash.fatal_field` should have raised `FormInvalid`"
                )
            except pyramid_formencode_classic.FormInvalid as exc:
                assert isinstance(exc.formStash, pyramid_formencode_classic.FormStash)
                assert exc.raised_by == "fatal_field"
                assert exc.error_main == _defaults.DEFAULT_ERROR_MAIN_TEXT
                assert (
                    exc.formStash.errors["Error_Main"]
                    == _defaults.DEFAULT_ERROR_MAIN_TEXT
                )
                assert exc.formStash.errors["email"] == "%s %s" % (message_alt, message)
        except Exception:
            raise

        # note: message_prepend
        try:
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_Email,
                raise_FormInvalid=True,
            )
            try:
                formStash.set_error(field="email", message=message_alt)
                formStash.fatal_field(
                    field="email",
                    error_field=message,
                    message_append=False,
                    message_prepend=True,
                )
                raise ValueError(
                    "`formStash.fatal_field` should have raised `FormInvalid`"
                )
            except pyramid_formencode_classic.FormInvalid as exc:
                assert isinstance(exc.formStash, pyramid_formencode_classic.FormStash)
                assert exc.raised_by == "fatal_field"
                assert exc.error_main == _defaults.DEFAULT_ERROR_MAIN_TEXT
                assert (
                    exc.formStash.errors["Error_Main"]
                    == _defaults.DEFAULT_ERROR_MAIN_TEXT
                )
                assert exc.formStash.errors["email"] == "%s %s" % (message, message_alt)
        except Exception:
            raise

        # note: allow_unknown_fields
        try:
            formStash.fatal_field(
                field="unknown", error_field=message, allow_unknown_fields=True
            )
            raise ValueError("`formStash.fatal_field` should have raised `FormInvalid`")
        except pyramid_formencode_classic.FormInvalid as exc:
            assert isinstance(exc.formStash, pyramid_formencode_classic.FormStash)
            assert exc.raised_by == "fatal_field"
            assert exc.error_main == _defaults.DEFAULT_ERROR_MAIN_TEXT
            assert (
                exc.formStash.errors["Error_Main"] == _defaults.DEFAULT_ERROR_MAIN_TEXT
            )
            assert exc.formStash.errors["unknown"] == message

    def test_FormStash_fatalForm_args(self):
        self.request.POST["email"] = "a@example.com"
        self.request.POST["username"] = "abcdefg"
        error_main = "[{{[CUSTOM_ERROR_MAIN]}}]"
        alt_error_main = "(((ALT_CUSTOM_ERROR_MAIN)))"

        # note: base
        try:
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_Email,
                raise_FormInvalid=True,
            )
            try:
                formStash.fatal_form(error_main=error_main)
                raise ValueError(
                    "`formStash.fatal_form` should have raised `FormInvalid`"
                )
            except pyramid_formencode_classic.FormInvalid as exc:
                assert isinstance(exc.formStash, pyramid_formencode_classic.FormStash)
                assert exc.raised_by == "fatal_form"
                assert exc.error_main == error_main
                assert exc.formStash.errors["Error_Main"] == error_main
        except Exception:
            raise

        # note: message_overwrite, implicit
        try:
            # error_main, error_main
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_Email,
                raise_FormInvalid=True,
            )
            try:
                formStash.set_error(message=error_main)
                formStash.fatal_form(error_main=error_main)
                raise ValueError(
                    "`formStash.fatal_form` should have raised `FormInvalid`"
                )
            except pyramid_formencode_classic.FormInvalid as exc:
                assert isinstance(exc.formStash, pyramid_formencode_classic.FormStash)
                assert exc.raised_by == "fatal_form"
                assert exc.error_main == error_main
                assert exc.formStash.errors["Error_Main"] == error_main

            # error_main, alt_error_main
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_Email,
                raise_FormInvalid=True,
            )
            try:
                formStash.set_error(message=error_main)
                formStash.fatal_form(error_main=alt_error_main)
                raise ValueError(
                    "`formStash.fatal_form` should have raised `FormInvalid`"
                )
            except pyramid_formencode_classic.FormInvalid as exc:
                assert isinstance(exc.formStash, pyramid_formencode_classic.FormStash)
                assert exc.raised_by == "fatal_form"
                assert exc.error_main == alt_error_main
                assert exc.formStash.errors["Error_Main"] == alt_error_main
        except Exception:
            raise

        # note: message_overwrite, explicit
        try:
            # error_main, error_main
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_Email,
                raise_FormInvalid=True,
            )
            try:
                formStash.set_error(message=error_main)
                formStash.fatal_form(error_main=error_main, message_overwrite=True)
                raise ValueError(
                    "`formStash.fatal_form` should have raised `FormInvalid`"
                )
            except pyramid_formencode_classic.FormInvalid as exc:
                assert isinstance(exc.formStash, pyramid_formencode_classic.FormStash)
                assert exc.raised_by == "fatal_form"
                assert exc.error_main == error_main
                assert exc.formStash.errors["Error_Main"] == error_main

            # error_main, alt_error_main
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_Email,
                raise_FormInvalid=True,
            )
            try:
                formStash.set_error(message=error_main)
                formStash.fatal_form(error_main=alt_error_main, message_overwrite=True)
                raise ValueError(
                    "`formStash.fatal_form` should have raised `FormInvalid`"
                )
            except pyramid_formencode_classic.FormInvalid as exc:
                assert isinstance(exc.formStash, pyramid_formencode_classic.FormStash)
                assert exc.raised_by == "fatal_form"
                assert exc.error_main == alt_error_main
                assert exc.formStash.errors["Error_Main"] == alt_error_main
        except Exception:
            raise

        # note: message_append
        try:
            # error_main, error_main
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_Email,
                raise_FormInvalid=True,
            )
            try:
                formStash.set_error(message=error_main)
                formStash.fatal_form(
                    error_main=error_main,
                    message_overwrite=False,
                    message_append=True,
                )
                raise ValueError(
                    "`formStash.fatal_form` should have raised `FormInvalid`"
                )
            except pyramid_formencode_classic.FormInvalid as exc:
                assert isinstance(exc.formStash, pyramid_formencode_classic.FormStash)
                assert exc.raised_by == "fatal_form"
                assert exc.error_main == error_main
                assert exc.formStash.errors["Error_Main"] == error_main

            # error_main, alt_error_main
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_Email,
                raise_FormInvalid=True,
            )
            try:
                formStash.set_error(message=error_main)
                formStash.fatal_form(
                    error_main=alt_error_main,
                    message_overwrite=False,
                    message_append=True,
                )
                raise ValueError(
                    "`formStash.fatal_form` should have raised `FormInvalid`"
                )
            except pyramid_formencode_classic.FormInvalid as exc:
                assert isinstance(exc.formStash, pyramid_formencode_classic.FormStash)
                assert exc.raised_by == "fatal_form"
                assert exc.error_main == alt_error_main
                self.assertEqual(
                    exc.formStash.errors["Error_Main"],
                    "%s %s" % (error_main, alt_error_main),
                )
        except Exception:
            raise

        # note: message_prepend
        try:
            # error_main, error_main
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_Email,
                raise_FormInvalid=True,
            )
            try:
                formStash.set_error(message=error_main)
                formStash.fatal_form(
                    error_main=error_main,
                    message_overwrite=False,
                    message_prepend=True,
                )
                raise ValueError(
                    "`formStash.fatal_form` should have raised `FormInvalid`"
                )
            except pyramid_formencode_classic.FormInvalid as exc:
                assert isinstance(exc.formStash, pyramid_formencode_classic.FormStash)
                assert exc.raised_by == "fatal_form"
                assert exc.error_main == error_main
                assert exc.formStash.errors["Error_Main"] == error_main

            # error_main, alt_error_main
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_Email,
                raise_FormInvalid=True,
            )
            try:
                formStash.set_error(message=error_main)
                formStash.fatal_form(
                    error_main=alt_error_main,
                    message_overwrite=False,
                    message_prepend=True,
                )
                raise ValueError(
                    "`formStash.fatal_form` should have raised `FormInvalid`"
                )
            except pyramid_formencode_classic.FormInvalid as exc:
                assert isinstance(exc.formStash, pyramid_formencode_classic.FormStash)
                assert exc.raised_by == "fatal_form"
                assert exc.error_main == alt_error_main
                self.assertEqual(
                    exc.formStash.errors["Error_Main"],
                    "%s %s" % (alt_error_main, error_main),
                )
        except Exception:
            raise
