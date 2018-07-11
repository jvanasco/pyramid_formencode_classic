from .panels.formencode_classic import FormencodeClassicDebugPanel

def includeme(config):
    """
    Pyramid API hook
    """
    config.registry.settings['debugtoolbar.panels'].append(FormencodeClassicDebugPanel)

    if 'mako.directories' not in config.registry.settings:
        config.registry.settings['mako.directories'] = []
