import pyramid_formencode_classic
import formencode
from pyramid_formencode_classic import formatters

# core testing facility
import unittest

# pyramid testing requirements
from pyramid import testing
from pyramid.renderers import render
from pyramid.renderers import render_to_response
from pyramid.interfaces import IRequestExtensions


# testing needs
from webob.multidict import MultiDict


class _Schema_Base(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True


class Form_Email(_Schema_Base):
    email_address = formencode.validators.Email(not_empty=True)


class Form_EmailUsername(_Schema_Base):
    email_address = formencode.validators.Email(not_empty=True)
    username = formencode.validators.UnicodeString(not_empty=True)


class DummyRequest(testing.DummyRequest):
    """
    extend `testing.DummyRequest` with a closer represtantion
    """

    def __init__(self):
        super(DummyRequest, self).__init__()
        self.GET = MultiDict()
        self.POST = MultiDict()


class TestHarness(object):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_formencode_classic')
        self.config.include('pyramid_mako')
        self.settings = {'mako.directories': 'pyramid_formencode_classic.tests:fixtures', }
        self.context = testing.DummyResource()

        # use our version of DummyRequest
        self.request = DummyRequest()

        # copy the item over...
        self.request.pyramid_formencode_classic = pyramid_formencode_classic._new_request_FormStashList(self.request)

    def tearDown(self):
        testing.tearDown()


class TestRenderSimple(object):
    """
    mixin class
    subclass and define a dict of test/values

    python -munittest pyramid_formencode_classic.tests.core.TestRenderSimple_FormA_HtmlErrorMain_Default \
                      pyramid_formencode_classic.tests.core.TestRenderSimple_FormA_HtmlErrorMain_Explicit \
                      pyramid_formencode_classic.tests.core.TestRenderSimple_FormA_HtmlErrorMain_Alt \
                      pyramid_formencode_classic.tests.core.TestRenderSimple_FormA_HtmlErrorPlaceholder
    """

    template = None

    def test_render_simple(self):

        _template = self.template
        _response_text = self._test_render_simple__data['response_text']

        def _print_form_simple():
            rendered = render_to_response(_template, {'request': self.request})
            return rendered

        rendered = _print_form_simple()
        try:
            assert rendered.text == _response_text
        except:
            print "------------"
            print rendered.text
            print "------------"
            raise


class TestParsing(object):
    """
    mixin class
    subclass and define a dict of test/values

    python -munittest pyramid_formencode_classic.tests.core.TestParsing_FormA_HtmlErrorMain_Default \
                      pyramid_formencode_classic.tests.core.TestParsing_FormA_HtmlErrorMain_Explicit \
                      pyramid_formencode_classic.tests.core.TestParsing_FormA_HtmlErrorMain_Alt \
                      pyramid_formencode_classic.tests.core.TestParsing_FormA_HtmlErrorPlaceholder
    """
    error_main_key = None
    template = None

    def test_no_params(self):

        tests_completed = []
        tests_fail = []
        for test_name, test_data in self._test_no_params__data.items():
            if False:
                print "================"
                print "================"
                print self.__class__.__name__, test_name
            _template = self.template
            _response_text = test_data['response_text']
            _reprint_kwargs = {}
            if 'auto_error_formatter' in test_data:
                _reprint_kwargs['auto_error_formatter'] = test_data['auto_error_formatter']
            if 'error_formatters' in test_data:
                if test_data['error_formatters'] is not None:
                    _reprint_kwargs['error_formatters'] = test_data['error_formatters']
            _validate_kwargs = {}
            if self.error_main_key is not None:
                _validate_kwargs['error_main_key'] = self.error_main_key

            def _print_form_simple():
                rendered = render_to_response(_template, {'request': self.request})
                return rendered

            try:
                (result,
                 formStash
                 ) = pyramid_formencode_classic.form_validate(self.request,
                                                              schema=Form_EmailUsername,
                                                              error_main="There was an error with your form.",
                                                              **_validate_kwargs
                                                              )
                if not result:
                    raise pyramid_formencode_classic.FormInvalid("Invalid Form")
                raise ValueError("`form_validate` should have raised `pyramid_formencode_classic.FormInvalid`")
            except pyramid_formencode_classic.FormInvalid:
                rendered = pyramid_formencode_classic.form_reprint(self.request,
                                                                   _print_form_simple,
                                                                   **_reprint_kwargs
                                                                   )
                try:
                    assert rendered.text == _response_text
                except:
                    if False:
                        print "----------------"
                        print self.__class__
                        print test_name
                        print rendered.text
                    tests_fail.append(test_name)
            tests_completed.append(test_name)

        if tests_fail:
            raise ValueError(tests_fail)



class TestBasic(TestHarness, unittest.TestCase):

    def test_pyramid_setup(self):
        """test the request property worked"""
        exts = self.config.registry.getUtility(IRequestExtensions)
        self.assertTrue('pyramid_formencode_classic' in exts.descriptors)


class TestRenderSimple_FormA_HtmlErrorMain_Alt(TestRenderSimple, TestHarness, unittest.TestCase):
    template = 'fixtures/form_a-html_error_main-alt.mako'

    _test_render_simple__data = {
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    }


class TestRenderSimple_FormA_HtmlErrorMain_Default(TestRenderSimple, TestHarness, unittest.TestCase):
    template = 'fixtures/form_a-html_error_main-default.mako'

    _test_render_simple__data = {
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    }


class TestRenderSimple_FormA_HtmlErrorMain_Explicit(TestRenderSimple, TestHarness, unittest.TestCase):
    template = 'fixtures/form_a-html_error_main-explicit.mako'

    _test_render_simple__data = {
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    }


class TestRenderSimple_FormA_HtmlErrorPlaceholder(TestRenderSimple, TestHarness, unittest.TestCase):
    template = 'fixtures/form_a-html_error_placeholder.mako'

    _test_render_simple__data = {
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    }


class TestParsing_FormA_HtmlErrorMain_Default(TestParsing, TestHarness, unittest.TestCase):

    template = 'fixtures/form_a-html_error_main-default.mako'

    # test_no_params
    # note the whitespace in the lines here!
    _test_no_params__data = {
    'test_formatter_default': {
        # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    },
    'test_formatter_is_none': {
        'auto_error_formatter': None,
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    },
    'test_formatter_nobr': {
        'auto_error_formatter': formatters.formatter_nobr,
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    },
    'formatter_help_inline': {
        'auto_error_formatter': formatters.formatter_help_inline,
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    },
    'formatter_none': {
        'auto_error_formatter': formatters.formatter_none,
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    },
    'formatter_hidden': {
        'auto_error_formatter': formatters.formatter_hidden,
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    }
}


class TestParsing_FormA_HtmlErrorMain_Explicit(TestParsing_FormA_HtmlErrorMain_Default, TestParsing, TestHarness, unittest.TestCase):
    """
    inherit from TestParsing_FormA_HtmlErrorMain_Default
    this should have the same exact output, but with a different template
    """
    template = 'fixtures/form_a-html_error_main-explicit.mako'


class TestParsing_FormA_HtmlErrorMain_Alt(TestParsing, TestHarness, unittest.TestCase):
    """
    this behaves slightly differently than TestParsing_FormA_HtmlErrorMain_Explicit
    """
    template = 'fixtures/form_a-html_error_main-alt.mako'
    error_main_key = 'Error_Alt'

    # test_no_params
    # note the whitespace in the lines here!
    _test_no_params__data = {
    'test_formatter_default': {
        # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    },
    'test_formatter_is_none': {
        'auto_error_formatter': None,
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    },
    'test_formatter_nobr': {
        'auto_error_formatter': formatters.formatter_nobr,
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    },
    'formatter_help_inline': {
        'auto_error_formatter': formatters.formatter_help_inline,
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    },
    'formatter_none': {
        'auto_error_formatter': formatters.formatter_none,
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    },
    'formatter_hidden': {
        'auto_error_formatter': formatters.formatter_hidden,
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    }
}


class TestParsing_FormA_HtmlErrorMain_Alt_ErrorFormatters(TestParsing, TestHarness, unittest.TestCase):
    """
    this behaves slightly differently than TestParsing_FormA_HtmlErrorMain_Alt
    """
    template = 'fixtures/form_a-html_error_main-alt.mako'
    error_main_key = 'Error_Alt'

    # test_no_params
    # note the whitespace in the lines here!
    _test_no_params__data = {
    'test_formatter_default': {
        # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
        'error_formatters': None,
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    },
    'test_formatter_is_none': {
        'auto_error_formatter': None,
        'error_formatters': None,
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    },
    'test_formatter_nobr': {
        'auto_error_formatter': formatters.formatter_nobr,
        'error_formatters': {'default': formatters.formatter_nobr, },
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">Nothing submitted.</span>

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    },
    'formatter_help_inline': {
        'auto_error_formatter': formatters.formatter_help_inline,
        'error_formatters': {'default': formatters.formatter_help_inline, },
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="help-inline">Nothing submitted.</span>

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    },
    'formatter_none': {
        'auto_error_formatter': formatters.formatter_none,
        'error_formatters': {'default': formatters.formatter_none, },
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- formatter_none (Nothing submitted.)-->
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    },
    'formatter_hidden': {
        'auto_error_formatter': formatters.formatter_hidden,
        'error_formatters': {'default': formatters.formatter_hidden, },
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="hidden" name="Nothing submitted." />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    }
}



class TestParsing_FormA_HtmlErrorPlaceholder(TestParsing, TestHarness, unittest.TestCase):
    template = 'fixtures/form_a-html_error_placeholder.mako'

    # test_no_params
    # note the whitespace in the lines here!
    _test_no_params__data = {
    'test_formatter_default': {
        # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    },
    'test_formatter_is_none': {
        'auto_error_formatter': None,
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    },
    'test_formatter_nobr': {
        'auto_error_formatter': formatters.formatter_nobr,
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    },
    'formatter_help_inline': {
        'auto_error_formatter': formatters.formatter_help_inline,
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    },
    'formatter_none': {
        'auto_error_formatter': formatters.formatter_none,
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    },
    'formatter_hidden': {
        'auto_error_formatter': formatters.formatter_hidden,
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    }
}


class TestParsing_FormA_HtmlErrorPlaceholder_ErrorFormatters(TestParsing, TestHarness, unittest.TestCase):
    template = 'fixtures/form_a-html_error_placeholder.mako'

    # test_no_params
    # note the whitespace in the lines here!
    _test_no_params__data = {
    'test_formatter_default': {
        # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
        'error_formatters': None,
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    },
    'test_formatter_is_none': {
        'auto_error_formatter': None,
        'error_formatters': None,
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">Nothing submitted.</span><br />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    },
    'test_formatter_nobr': {
        'auto_error_formatter': formatters.formatter_nobr,
        'error_formatters': {'default': formatters.formatter_nobr, },
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="error-message">Nothing submitted.</span>

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    },
    'formatter_help_inline': {
        'auto_error_formatter': formatters.formatter_help_inline,
        'error_formatters': {'default': formatters.formatter_help_inline, },
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <span class="help-inline">Nothing submitted.</span>

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    },
    'formatter_none': {
        'auto_error_formatter': formatters.formatter_none,
        'error_formatters': {'default': formatters.formatter_none, },
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <!-- formatter_none (Nothing submitted.)-->
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    },
    'formatter_hidden': {
        'auto_error_formatter': formatters.formatter_hidden,
        'error_formatters': {'default': formatters.formatter_hidden, },
        'response_text': """\
<html><head></head><body><div>
<form action="/" method="POST">
    
    <input type="hidden" name="Nothing submitted." />

    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>
""",
    }
}



"""

    results = formStash.results
    email_address = results['email_address']

    formStash.set_error(field="email_address",
                        message="Wrong password",
                        raise_FormInvalid=True,
                        )
"""