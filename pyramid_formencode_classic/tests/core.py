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
            print rendered.text
            raise


class TestParsing(object):
    """
    mixin class
    subclass and define a dict of test/values
    """
    error_main_key = None
    template = None

    def test_no_params(self):

        tests_completed = []
        for test_name, test_data in self._test_no_params__data.items():
            _template = self.template
            _response_text = test_data['response_text']
            _reprint_kwargs = {}
            if 'auto_error_formatter' in test_data:
                _reprint_kwargs['auto_error_formatter'] = test_data['auto_error_formatter']
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
                                                              schema=Form_Email,
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
                    print "----------"
                    print self.__class__
                    print test_name
                    print rendered.text
                    raise
            tests_completed.append(test_name)



class TestBasic(TestHarness, unittest.TestCase):

    def test_pyramid_setup(self):
        """test the request property worked"""
        exts = self.config.registry.getUtility(IRequestExtensions)
        self.assertTrue('pyramid_formencode_classic' in exts.descriptors)


class TestRenderSimple_FormAAlt(TestRenderSimple, TestHarness, unittest.TestCase):
    template = 'fixtures/form_email-A-alt.mako'

    _test_render_simple__data = {
        'response_text': """\
<form action="/" method="POST">
    
    
    <input type="text" name="email" value="" />
</form>
""",
    }


class TestRenderSimple_FormADefault(TestRenderSimple, TestHarness, unittest.TestCase):
    template = 'fixtures/form_email-A-default.mako'

    _test_render_simple__data = {
        'response_text': """\
<form action="/" method="POST">
    
    
    <input type="text" name="email" value="" />
</form>
""",
    }


class TestRenderSimple_FormAExplicit(TestRenderSimple, TestHarness, unittest.TestCase):
    template = 'fixtures/form_email-A-explicit.mako'

    _test_render_simple__data = {
        'response_text': """\
<form action="/" method="POST">
    
    
    <input type="text" name="email" value="" />
</form>
""",
    }


class TestRenderSimple_FormB(TestRenderSimple, TestHarness, unittest.TestCase):
    template = 'fixtures/form_email-B.mako'

    _test_render_simple__data = {
        'response_text': """\
<form action="/" method="POST">
    
    
    <input type="text" name="email" value="" />
</form>
""",
    }


class TestParsing_FormADefault(TestParsing, TestHarness, unittest.TestCase):

    template = 'fixtures/form_email-A-default.mako'

    # test_no_params
    # note the whitespace in the lines here!
    _test_no_params__data = {
    'test_formatter_default': {
        # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
        'response_text': """\
<!-- for: ('Error_Main',) -->
<span class="error-message">Nothing submitted.</span>
<form action="/" method="POST">
    
    <div class="alert alert-error"><div class="control-group error"><span class="help-inline"><i class="icon-exclamation-sign"></i> Nothing submitted.</span></div></div>
    <input type="text" name="email" value="" />
</form>
""",
    },
    'test_formatter_is_none': {
        'auto_error_formatter': None,
        'response_text': """\
<!-- for: ('Error_Main',) -->
<span class="error-message">Nothing submitted.</span><br />
<form action="/" method="POST">
    
    <div class="alert alert-error"><div class="control-group error"><span class="help-inline"><i class="icon-exclamation-sign"></i> Nothing submitted.</span></div></div>
    <input type="text" name="email" value="" />
</form>
""",
    },
    'test_formatter_nobr': {
        'auto_error_formatter': formatters.formatter_nobr,
        'response_text': """\
<!-- for: ('Error_Main',) -->
<span class="error-message">Nothing submitted.</span>
<form action="/" method="POST">
    
    <div class="alert alert-error"><div class="control-group error"><span class="help-inline"><i class="icon-exclamation-sign"></i> Nothing submitted.</span></div></div>
    <input type="text" name="email" value="" />
</form>
""",
    },
    'formatter_help_inline': {
        'auto_error_formatter': formatters.formatter_help_inline,
        'response_text': """\
<!-- for: ('Error_Main',) -->
<span class="help-inline">Nothing submitted.</span>
<form action="/" method="POST">
    
    <div class="alert alert-error"><div class="control-group error"><span class="help-inline"><i class="icon-exclamation-sign"></i> Nothing submitted.</span></div></div>
    <input type="text" name="email" value="" />
</form>
""",
    },
    'formatter_none': {
        'auto_error_formatter': formatters.formatter_none,
        'response_text': """\
<!-- for: ('Error_Main',) -->
<!-- formatter_none (Nothing submitted.)--><form action="/" method="POST">
    
    <div class="alert alert-error"><div class="control-group error"><span class="help-inline"><i class="icon-exclamation-sign"></i> Nothing submitted.</span></div></div>
    <input type="text" name="email" value="" />
</form>
""",
    },
    'formatter_hidden': {
        'auto_error_formatter': formatters.formatter_hidden,
        'response_text': """\
<!-- for: ('Error_Main',) -->
<input type="hidden" name="Nothing submitted." /><form action="/" method="POST">
    
    <div class="alert alert-error"><div class="control-group error"><span class="help-inline"><i class="icon-exclamation-sign"></i> Nothing submitted.</span></div></div>
    <input type="text" name="email" value="" />
</form>
""",
    }
}


class TestParsing_FormAExplicit(TestParsing, TestHarness, unittest.TestCase):
    template = 'fixtures/form_email-A-explicit.mako'

    # test_no_params
    # note the whitespace in the lines here!
    _test_no_params__data = {
    'test_formatter_default': {
        # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
        'response_text': """\
<!-- for: ('Error_Main',) -->
<span class="error-message">Nothing submitted.</span>
<form action="/" method="POST">
    
    <div class="alert alert-error"><div class="control-group error"><span class="help-inline"><i class="icon-exclamation-sign"></i> There was an error with your submission.</span></div></div>
    <input type="text" name="email" value="" />
</form>
""",
    },
    'test_formatter_is_none': {
        'auto_error_formatter': None,
        'response_text': """\
<!-- for: ('Error_Main',) -->
<span class="error-message">Nothing submitted.</span><br />
<form action="/" method="POST">
    
    <div class="alert alert-error"><div class="control-group error"><span class="help-inline"><i class="icon-exclamation-sign"></i> There was an error with your submission.</span></div></div>
    <input type="text" name="email" value="" />
</form>
""",
    },
    'test_formatter_nobr': {
        'auto_error_formatter': formatters.formatter_nobr,
        'response_text': """\
<!-- for: ('Error_Main',) -->
<span class="error-message">Nothing submitted.</span>
<form action="/" method="POST">
    
    <div class="alert alert-error"><div class="control-group error"><span class="help-inline"><i class="icon-exclamation-sign"></i> There was an error with your submission.</span></div></div>
    <input type="text" name="email" value="" />
</form>
""",
    },
    'formatter_help_inline': {
        'auto_error_formatter': formatters.formatter_help_inline,
        'response_text': """\
<!-- for: ('Error_Main',) -->
<span class="help-inline">Nothing submitted.</span>
<form action="/" method="POST">
    
    <div class="alert alert-error"><div class="control-group error"><span class="help-inline"><i class="icon-exclamation-sign"></i> There was an error with your submission.</span></div></div>
    <input type="text" name="email" value="" />
</form>
""",
    },
    'formatter_none': {
        'auto_error_formatter': formatters.formatter_none,
        'response_text': """\
<!-- for: ('Error_Main',) -->
<!-- formatter_none (Nothing submitted.)--><form action="/" method="POST">
    
    <div class="alert alert-error"><div class="control-group error"><span class="help-inline"><i class="icon-exclamation-sign"></i> There was an error with your submission.</span></div></div>
    <input type="text" name="email" value="" />
</form>
""",
    },
    'formatter_hidden': {
        'auto_error_formatter': formatters.formatter_hidden,
        'response_text': """\
<!-- for: ('Error_Main',) -->
<input type="hidden" name="Nothing submitted." /><form action="/" method="POST">
    
    <div class="alert alert-error"><div class="control-group error"><span class="help-inline"><i class="icon-exclamation-sign"></i> There was an error with your submission.</span></div></div>
    <input type="text" name="email" value="" />
</form>
""",
    }
}


class TestParsing_FormAAlt(TestParsing, TestHarness, unittest.TestCase):
    template = 'fixtures/form_email-A-alt.mako'
    error_main_key = 'Error_Alt'

    # test_no_params
    # note the whitespace in the lines here!
    _test_no_params__data = {
    'test_formatter_default': {
        # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
        'response_text': """\
<!-- for: Error_Alt -->
<span class="error-message">Nothing submitted.</span>
<form action="/" method="POST">
    
    <div class="alert alert-error"><div class="control-group error"><span class="help-inline"><i class="icon-exclamation-sign"></i> Nothing submitted.</span></div></div>
    <input type="text" name="email" value="" />
</form>
""",
    },
    'test_formatter_is_none': {
        'auto_error_formatter': None,
        'response_text': """\
<!-- for: Error_Alt -->
<span class="error-message">Nothing submitted.</span><br />
<form action="/" method="POST">
    
    <div class="alert alert-error"><div class="control-group error"><span class="help-inline"><i class="icon-exclamation-sign"></i> Nothing submitted.</span></div></div>
    <input type="text" name="email" value="" />
</form>
""",
    },
    'test_formatter_nobr': {
        'auto_error_formatter': formatters.formatter_nobr,
        'response_text': """\
<!-- for: Error_Alt -->
<span class="error-message">Nothing submitted.</span>
<form action="/" method="POST">
    
    <div class="alert alert-error"><div class="control-group error"><span class="help-inline"><i class="icon-exclamation-sign"></i> Nothing submitted.</span></div></div>
    <input type="text" name="email" value="" />
</form>
""",
    },
    'formatter_help_inline': {
        'auto_error_formatter': formatters.formatter_help_inline,
        'response_text': """\
<!-- for: Error_Alt -->
<span class="help-inline">Nothing submitted.</span>
<form action="/" method="POST">
    
    <div class="alert alert-error"><div class="control-group error"><span class="help-inline"><i class="icon-exclamation-sign"></i> Nothing submitted.</span></div></div>
    <input type="text" name="email" value="" />
</form>
""",
    },
    'formatter_none': {
        'auto_error_formatter': formatters.formatter_none,
        'response_text': """\
<!-- for: Error_Alt -->
<!-- formatter_none (Nothing submitted.)--><form action="/" method="POST">
    
    <div class="alert alert-error"><div class="control-group error"><span class="help-inline"><i class="icon-exclamation-sign"></i> Nothing submitted.</span></div></div>
    <input type="text" name="email" value="" />
</form>
""",
    },
    'formatter_hidden': {
        'auto_error_formatter': formatters.formatter_hidden,
        'response_text': """\
<!-- for: Error_Alt -->
<input type="hidden" name="Nothing submitted." /><form action="/" method="POST">
    
    <div class="alert alert-error"><div class="control-group error"><span class="help-inline"><i class="icon-exclamation-sign"></i> Nothing submitted.</span></div></div>
    <input type="text" name="email" value="" />
</form>
""",
    }
}


class TestParsing_FormB(TestParsing, TestHarness, unittest.TestCase):
    template = 'fixtures/form_email-B.mako'

    # test_no_params
    # note the whitespace in the lines here!
    _test_no_params__data = {
    'test_formatter_default': {
        # 'auto_error_formatter': None,  # don't supply in this test, this should default to formatter_nobr
        'response_text': """\
<!-- for: ('Error_Main',) -->
<span class="error-message">Nothing submitted.</span>
<form action="/" method="POST">
    
    <input type="hidden" name="Error_Main" value="" />
    <input type="text" name="email" value="" />
</form>
""",
    },
    'test_formatter_is_none': {
        'auto_error_formatter': None,
        'response_text': """\
<!-- for: ('Error_Main',) -->
<span class="error-message">Nothing submitted.</span><br />
<form action="/" method="POST">
    
    <input type="hidden" name="Error_Main" value="" />
    <input type="text" name="email" value="" />
</form>
""",
    },
    'test_formatter_nobr': {
        'auto_error_formatter': formatters.formatter_nobr,
        'response_text': """\
<!-- for: ('Error_Main',) -->
<span class="error-message">Nothing submitted.</span>
<form action="/" method="POST">
    
    <input type="hidden" name="Error_Main" value="" />
    <input type="text" name="email" value="" />
</form>
""",
    },
    'formatter_help_inline': {
        'auto_error_formatter': formatters.formatter_help_inline,
        'response_text': """\
<!-- for: ('Error_Main',) -->
<span class="help-inline">Nothing submitted.</span>
<form action="/" method="POST">
    
    <input type="hidden" name="Error_Main" value="" />
    <input type="text" name="email" value="" />
</form>
""",
    },
    'formatter_none': {
        'auto_error_formatter': formatters.formatter_none,
        'response_text': """\
<!-- for: ('Error_Main',) -->
<!-- formatter_none (Nothing submitted.)--><form action="/" method="POST">
    
    <input type="hidden" name="Error_Main" value="" />
    <input type="text" name="email" value="" />
</form>
""",
    },
    'formatter_hidden': {
        'auto_error_formatter': formatters.formatter_hidden,
        'response_text': """\
<!-- for: ('Error_Main',) -->
<input type="hidden" name="Nothing submitted." /><form action="/" method="POST">
    
    <input type="hidden" name="Error_Main" value="" />
    <input type="text" name="email" value="" />
</form>
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