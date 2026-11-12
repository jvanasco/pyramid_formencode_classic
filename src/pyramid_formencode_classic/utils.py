# stdlib
import logging
import sys
from typing import TYPE_CHECKING

# local
from ._utils import EncodedErrors
from ._utils import TYPES_ERRORS

if TYPE_CHECKING:
    from pyramid.response import Response

# ==============================================================================

log = logging.getLogger("pyramid_formencode_classic")

# ------------------------------------------------------------------------------


def determine_response_charset(response: "Response") -> str:
    """FROM PYLONS -- Determine the charset of the specified Response object,
    returning the default system encoding when none is set"""
    charset = response.charset
    if charset is None:
        charset = sys.getdefaultencoding()
    if __debug__:
        log.debug("Determined result charset to be: %s", charset)
    return charset


def encode_formencode_errors(
    errors: TYPES_ERRORS,
    encoding: str,
    encoding_errors: str = "strict",
) -> EncodedErrors:
    """Encode error strings to bytes and preserve empty slots.

    Update dictionaries in place and return other iterables as lists.
    ``encoding_errors`` controls how the codec handles encoding errors.
    """
    if errors is None:
        return None
    if isinstance(errors, str):
        return errors.encode(encoding, encoding_errors)
    if isinstance(errors, dict):
        for key, value in list(errors.items()):
            errors[key] = encode_formencode_errors(value, encoding, encoding_errors)
        return errors
    return [
        encode_formencode_errors(error, encoding, encoding_errors) for error in errors
    ]
