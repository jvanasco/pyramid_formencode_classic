# stdlib
import logging
import sys
from typing import TYPE_CHECKING

# local
from ._utils import TYPES_ERRORS

if TYPE_CHECKING:
    from pyramid.response import Response

# ==============================================================================

log = logging.getLogger(__name__)

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
    encoding_errors="strict",
) -> TYPES_ERRORS:
    """FROM PYLONS -- Encode any unicode values contained in a FormEncode errors dict
    to raw strings of the specified encoding"""
    if errors is None:
        return errors
    elif isinstance(errors, str):
        errors = errors.encode(encoding, encoding_errors)
    elif isinstance(errors, dict):
        for key, value in list(errors.items()):
            errors[key] = encode_formencode_errors(value, encoding, encoding_errors)
    else:
        # Fallback to an iterable (a list)
        errors = [
            encode_formencode_errors(error, encoding, encoding_errors)
            for error in errors
        ]
    return errors
