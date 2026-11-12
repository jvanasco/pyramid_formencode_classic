# stdlib
from typing import Dict
from typing import Optional
from typing import TYPE_CHECKING

# pypi
from pyramid_debugtoolbar.panels import DebugPanel

if TYPE_CHECKING:
    from pyramid.request import Request
    from pyramid.response import Response

# ==============================================================================


class FormencodeClassicDebugPanel(DebugPanel):
    """Show form stashes collected during the current request."""

    name: str = "FormencodeClassic"
    has_content: Optional[bool] = None
    template: str = (
        "pyramid_formencode_classic.debugtoolbar.panels:templates/formencode_classic.dbtmako"
    )

    def __init__(self, request: "Request") -> None:
        self.data: Dict = {}

        # we need to process things AFTER the handler runs
        # so stash the request, then process it under `process_response`
        self.request = request

    def process_response(self, response: "Response") -> None:
        """Collect the request form stashes after the view has run."""
        if "pyramid_formencode_classic" in self.request.__dict__.keys():
            self.has_content = True
            forms: Dict = {}
            for form_stash in self.request.pyramid_formencode_classic.keys():
                forms[form_stash] = self.request.pyramid_formencode_classic[form_stash]
            self.data["forms"] = forms

    @property
    def nav_title(self) -> str:
        """Return the label used in the toolbar navigation."""
        return self.name

    @property
    def title(self) -> str:
        """Return the title displayed in the panel."""
        return self.name
