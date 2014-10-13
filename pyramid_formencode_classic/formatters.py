"""formatters we use
"""
# stdlib
import cgi

# pypi
import formencode


def formatter_help_inline(error):
    """
    Formatter that escapes the error, wraps the error in a span with
    class ``help-inline``, and doesn't add a ``<br>`` ; somewhat compatible with twitter's bootstrap
    """
    return '<span class="help-inline">%s</span>\n' % formencode.rewritingparser.html_quote(error)


def formatter_nobr(error):
    """
    Formatter that escapes the error, wraps the error in a span with
    class ``error-message``, and doesn't add a ``<br>``
    """
    return '<span class="error-message">%s</span>\n' % formencode.rewritingparser.html_quote(error)


def formatter_none(error):
    """
    Formatter that ignores the error.
    This is useful / necessary when handling custom css/html
    It outputs an html comment just so you don't go insane debugging.
    """
    return '<!-- formatter_none (%s)-->' % cgi.escape(error)
