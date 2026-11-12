# stdlib
import unittest

# pypi
import formencode

# local
import pyramid_formencode_classic
import pyramid_formencode_classic.validators
from .test_core import _TestHarness

# ==============================================================================


class Form_OnlyOneOf(formencode.Schema):

    id = formencode.validators.Int(not_empty=False, if_missing=None)
    unicode_string = formencode.validators.UnicodeString(
        not_empty=False, if_missing=None, max=64, min=2
    )

    chained_validators = [
        pyramid_formencode_classic.validators.OnlyOneOf(
            ("id", "unicode_string"), not_empty=True
        ),
    ]


class Form_RequireEmptyIfMissing(formencode.Schema):

    id = formencode.validators.Int(not_empty=False, if_missing=None)
    unicode_string = formencode.validators.UnicodeString(
        not_empty=False, if_missing=None, max=64, min=2
    )

    chained_validators = [
        pyramid_formencode_classic.validators.RequireEmptyIfMissing(
            "id", missing="unicode_string"
        ),
    ]


class Form_RequireEmptyIfPresent(formencode.Schema):

    id = formencode.validators.Int(not_empty=False, if_missing=None)
    unicode_string = formencode.validators.UnicodeString(
        not_empty=False, if_missing=None, max=64, min=2
    )

    chained_validators = [
        pyramid_formencode_classic.validators.RequireEmptyIfPresent(
            "id", present="unicode_string"
        ),
    ]


class Test_OnlyOneOf(_TestHarness, unittest.TestCase):

    def _test_actual(self):
        result, formStash = pyramid_formencode_classic.form_validate(
            self.request,
            schema=Form_OnlyOneOf,
        )
        if not result:
            raise pyramid_formencode_classic.FormInvalid(formStash)
        return True

    def test_none(self):
        with self.assertRaises(pyramid_formencode_classic.exceptions.FormInvalid) as cm:
            self._test_actual()

        exc = cm.exception
        self.assertEqual(
            exc.formStash.errors,
            {
                "Error_Main": (
                    "[[There was an error with your FORM submission.]] "
                    "[[NOTHING SUBMITTED.]]"
                )
            },
        )

    def test_submitted_linked_fields_are_empty(self) -> None:
        """Reject a submitted form when neither linked field has a value."""
        self.request.POST.update({"id": "", "unicode_string": ""})
        valid, stash = pyramid_formencode_classic.form_validate(
            self.request, schema=Form_OnlyOneOf
        )

        assert not valid
        assert stash.is_submitted_vars
        message = "You must submit one and only one of these linked fields."
        assert stash.get_error("id") == message
        assert stash.get_error("unicode_string") == message

    def test_one(self):
        # first id
        self.request.POST["id"] = "1"
        self._test_actual()

        # then unicode_string
        del self.request.POST["id"]
        self.request.POST["unicode_string"] = "unicode_string"
        self._test_actual()

    def test_both(self):
        self.request.POST["id"] = "1"
        self.request.POST["unicode_string"] = "unicode_string"

        with self.assertRaises(pyramid_formencode_classic.exceptions.FormInvalid) as cm:
            self._test_actual()

        exc = cm.exception
        self.assertEqual(
            exc.formStash.errors,
            {
                "Error_Main": "[[There was an error with your FORM submission.]]",
                "id": "You may submit only one of these linked fields.",
                "unicode_string": "You may submit only one of these linked fields.",
            },
        )


class Test_RequireEmptyIfMissing(_TestHarness, unittest.TestCase):

    def _test_actual(self):
        result, formStash = pyramid_formencode_classic.form_validate(
            self.request,
            schema=Form_RequireEmptyIfMissing,
        )
        if not result:
            raise pyramid_formencode_classic.FormInvalid(formStash)
        return True

    def test_none(self):
        with self.assertRaises(pyramid_formencode_classic.exceptions.FormInvalid) as cm:
            self._test_actual()

        exc = cm.exception
        self.assertEqual(
            exc.formStash.errors,
            {
                "Error_Main": (
                    "[[There was an error with your FORM submission.]] "
                    "[[NOTHING SUBMITTED.]]"
                )
            },
        )

    def test_one(self):
        # first id
        self.request.POST["id"] = "1"
        with self.assertRaises(pyramid_formencode_classic.exceptions.FormInvalid) as cm:
            self._test_actual()
        exc = cm.exception
        self.assertEqual(
            exc.formStash.errors,
            {
                "Error_Main": "[[There was an error with your FORM submission.]]",
                "id": "Please do not enter a value in this field unless you enter a value in the linked field.",
            },
        )

        # then unicode_string
        del self.request.POST["id"]
        self.request.POST["unicode_string"] = "unicode_string"
        self._test_actual()

    def test_both(self):
        self.request.POST["id"] = "1"
        self.request.POST["unicode_string"] = "unicode_string"

        self._test_actual()


class Test_RequireEmptyIfPresent(_TestHarness, unittest.TestCase):

    def _test_actual(self):
        result, formStash = pyramid_formencode_classic.form_validate(
            self.request,
            schema=Form_RequireEmptyIfPresent,
        )
        if not result:
            raise pyramid_formencode_classic.FormInvalid(formStash)
        return True

    def test_none(self):
        with self.assertRaises(pyramid_formencode_classic.exceptions.FormInvalid) as cm:
            self._test_actual()

        exc = cm.exception
        self.assertEqual(
            exc.formStash.errors,
            {
                "Error_Main": (
                    "[[There was an error with your FORM submission.]] "
                    "[[NOTHING SUBMITTED.]]"
                )
            },
        )

    def test_one(self):
        # first id
        self.request.POST["id"] = "1"
        self._test_actual()

        # then unicode_string
        del self.request.POST["id"]
        self.request.POST["unicode_string"] = "unicode_string"
        self._test_actual()

    def test_both(self):
        self.request.POST["id"] = "1"
        self.request.POST["unicode_string"] = "unicode_string"

        with self.assertRaises(pyramid_formencode_classic.exceptions.FormInvalid) as cm:
            self._test_actual()

        exc = cm.exception
        self.assertEqual(
            exc.formStash.errors,
            {
                "Error_Main": "[[There was an error with your FORM submission.]]",
                "id": "Please do not enter a value in this field when you enter a value in the linked field.",
            },
        )
