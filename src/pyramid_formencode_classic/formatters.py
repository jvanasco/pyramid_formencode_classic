# pypi
import formencode

import six

six.add_move(six.MovedAttribute("html_escape", "cgi", "html", "escape", "escape"))
from six.moves import html_escape

"""
collection of common formatters to use
"""


def formatter_help_inline(error):
    """
    Formatter that escapes the error, wraps the error in a span with
    class ``help-inline``, and doesn't add a ``<br>`` ; somewhat compatible with twitter's bootstrap
    """
    return (
        '<span class="help-inline">%s</span>\n'
        % formencode.rewritingparser.html_quote(error)
    )


def formatter_hidden(error):
    """
    returns a hidden field with the error in the name
    """
    return '<input type="hidden" name="%s" />\n' % html_escape(error)


def formatter_nobr(error):
    """
    This is a variant of the htmlfill `default_formatter`, in which a trailing <br/> is not included

    Formatter that escapes the error, wraps the error in a span with
    class ``error-message``, and doesn't add a ``<br>``
    """
    return (
        '<span class="error-message">%s</span>\n'
        % formencode.rewritingparser.html_quote(error)
    )


def formatter_comment(error):
    """
    Formatter that ignores the error and hides it in a comment
    This is useful / necessary when handling custom css/html
    It outputs an html comment just so you don't go insane debugging.
    """
    return "<!-- formatter_comment (%s)-->" % html_escape(error)


def formatter_empty_string(error):
    """
    Formatting that returns an empty string
    """
    return ""


__all__ = (
    "formatter_comment",
    "formatter_empty_string",
    "formatter_help_inline",
    "formatter_hidden",
    "formatter_nobr",
)
