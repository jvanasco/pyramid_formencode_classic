"""Tests for response charset and FormEncode error encoding helpers."""

import sys
import unittest

from pyramid.response import Response

from pyramid_formencode_classic.utils import determine_response_charset
from pyramid_formencode_classic.utils import encode_formencode_errors


class TestResponseUtilities(unittest.TestCase):
    """Verify charset fallback and the supported error shapes."""

    def test_determine_response_charset_without_charset(self) -> None:
        """Use the interpreter default when the response has no charset."""
        response = Response(body=b"", content_type="application/octet-stream")

        assert response.charset is None
        assert determine_response_charset(response) == sys.getdefaultencoding()

    def test_encode_formencode_errors(self) -> None:
        """Encode strings recursively and retain empty error slots."""
        message = "Déjà utilisé"
        encoded = message.encode("utf-8")
        for errors, expected in (
            (message, encoded),
            (None, None),
            ({"email": message}, {"email": encoded}),
            ([message, None, {"email": message}], [encoded, None, {"email": encoded}]),
        ):
            with self.subTest(errors=errors):
                assert encode_formencode_errors(errors, "utf-8") == expected
