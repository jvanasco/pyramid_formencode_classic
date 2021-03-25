from pyramid_debugtoolbar.panels import DebugPanel


_ = lambda x: x


# ==============================================================================


class FormencodeClassicDebugPanel(DebugPanel):
    """"""

    name = "FormencodeClassic"
    has_content = None
    template = "pyramid_formencode_classic.debugtoolbar.panels:templates/formencode_classic.dbtmako"

    def __init__(self, request):
        self.data = {}

        # we need to process things AFTER the handler runs
        # so stash the request, then process it under `process_response`
        self.request = request

    def process_response(self, response):
        if "pyramid_formencode_classic" in self.request.__dict__.keys():
            self.has_content = True
            forms = {}
            for form_stash in self.request.pyramid_formencode_classic.keys():
                forms[form_stash] = self.request.pyramid_formencode_classic[form_stash]
            self.data["forms"] = forms

    @property
    def nav_title(self):
        return _(self.name)

    @property
    def title(self):
        return _(self.name)
