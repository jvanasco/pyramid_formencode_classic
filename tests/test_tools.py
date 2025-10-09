# stdlib
from typing import Any
from typing import Dict
import unittest

# pypi
import formencode

# local
import pyramid_formencode_classic
import pyramid_formencode_classic.tools
import pyramid_formencode_classic.validators

# ==============================================================================


class Form_Example(formencode.Schema):
    email = formencode.validators.Email(not_empty=True)
    email_alt = formencode.validators.Email(not_empty=False, if_missing=None)

    one_of = formencode.validators.OneOf(
        ("a", "b", "c", "d"),
        not_empty=True,
    )
    one_of_alt = formencode.validators.OneOf(
        ("e", "f", "g", "h"),
        not_empty=False,
        if_missing=None,
    )

    unicode_string = formencode.validators.UnicodeString(not_empty=True, max=64, min=2)
    unicode_string_alt = formencode.validators.UnicodeString(
        not_empty=False, if_missing=None, max=64
    )

    id = formencode.validators.Int(not_empty=True)
    id_alt = formencode.validators.Int(not_empty=False, if_missing=None)

    file = formencode.validators.FieldStorageUploadConverter(not_empty=True)
    file_alt = formencode.validators.FieldStorageUploadConverter(
        not_empty=False, if_missing=None
    )

    chained_validators = [
        # these are bonded
        formencode.validators.RequireIfPresent("email", present="email_alt"),
        # these are opposed
        pyramid_formencode_classic.validators.OnlyOneOf(
            ("id", "unicode_string"), not_empty=True
        ),
    ]


Form_Example__as_dict: Dict[str, Any] = {
    "chained_validators": [
        {
            "missing": None,
            "not_empty": False,
            "present": "email_alt",
            "required": "email",
            "type": "RequireIfMissing",
        },
        {
            "not_empty": True,
            "only_one_ofs": ("id", "unicode_string"),
            "type": "OnlyOneOf",
        },
    ],
    "email": {"not_empty": True, "type": "Email"},
    "email_alt": {"if_missing": None, "not_empty": False, "type": "Email"},
    "file": {"not_empty": True, "type": "FieldStorageUploadConverter"},
    "file_alt": {
        "if_missing": None,
        "not_empty": False,
        "type": "FieldStorageUploadConverter",
    },
    "id": {"max": None, "min": None, "not_empty": True, "type": "Int"},
    "id_alt": {
        "if_missing": None,
        "max": None,
        "min": None,
        "not_empty": False,
        "type": "Int",
    },
    "one_of": {"not_empty": True, "options": ("a", "b", "c", "d"), "type": "OneOf"},
    "one_of_alt": {
        "if_missing": None,
        "not_empty": False,
        "options": ("e", "f", "g", "h"),
        "type": "OneOf",
    },
    "unicode_string": {"max": 64, "min": 2, "not_empty": True, "type": "UnicodeString"},
    "unicode_string_alt": {
        "if_missing": None,
        "max": 64,
        "min": None,
        "not_empty": False,
        "type": "UnicodeString",
    },
}


class TestDocumentForm(unittest.TestCase):
    def test_basic(self):
        documented = pyramid_formencode_classic.tools.document_form(Form_Example)
        # import pprint
        # pprint.pprint(documented)
        self.assertEqual(documented, Form_Example__as_dict)
