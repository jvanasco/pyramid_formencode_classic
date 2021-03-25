from .panels.formencode_classic import FormencodeClassicDebugPanel


def includeme(config):
    """
    Pyramid API hook
    """
    config.add_debugtoolbar_panel(FormencodeClassicDebugPanel)
