# stdlib
import logging
from typing import TYPE_CHECKING

# pypi
import webob.compat

# local
from .api import form_reprint  # noqa: F401 ; maintain API
from .api import form_validate  # noqa: F401 ; maintain API
from .exceptions import FormInvalid  # noqa: F401 ; maintain API
from .objects import FormStash
from .objects import FormStashList

if TYPE_CHECKING:
    from pyramid.config import Configurator
    from pyramid.request import Request

# ==============================================================================

# no warnings in > 0.3.0
"""
import warnings

# define warnings
def warn_future(message):
    warnings.warn(message, FutureWarning, stacklevel=2)


def warn_user(message):
    warnings.warn(message, UserWarning, stacklevel=2)
"""


# defaults
__VERSION__ = "0.5.1"

AUTOMATIC_CLEANUP = True

log = logging.getLogger(__name__)


# ------------------------------------------------------------------------------


def _form_cleanup(request: "Request") -> None:
    """
    make sure we close all fieldstorage objects
    """
    for _form in set(request.pyramid_formencode_classic.values()):
        for k, v in list(_form.results.items()):
            try:
                # don't compare to Boolean, as some Form objects can't handle that
                if isinstance(v, webob.compat.cgi_FieldStorage):
                    v.fp.close()
            except Exception as exc:  # noqa: F841
                pass


def _new_request_FormStashList(request: "Request") -> FormStashList:
    """
    This is a modern version of `init_request` from the .1 branch
    It is a memoized property via the pyramid `includeme` configuration hook
    This merely creates a new FormStashList object
    """
    if AUTOMATIC_CLEANUP:
        request.add_finished_callback(_form_cleanup)
    return FormStashList()


def includeme(config: "Configurator") -> None:
    """
    pyramid hook for setting up a form method via the configurator
    """
    config.add_request_method(
        _new_request_FormStashList, "pyramid_formencode_classic", reify=True
    )
