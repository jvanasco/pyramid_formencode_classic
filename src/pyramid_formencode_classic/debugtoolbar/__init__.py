# stdlib
from typing import TYPE_CHECKING

# local
from .panels.formencode_classic import FormencodeClassicDebugPanel

if TYPE_CHECKING:
    from pyramid.config import Configurator


# ==============================================================================


def includeme(config: "Configurator") -> None:
    """
    Pyramid API hook
    """
    config.add_debugtoolbar_panel(FormencodeClassicDebugPanel)
