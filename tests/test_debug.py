# stdlib
import re
from typing import Callable
import unittest

# pypi
import formencode

# local
import pyramid_formencode_classic
import pyramid_formencode_classic._defaults
import pyramid_formencode_classic.tools
import pyramid_formencode_classic.validators
from .test_core import _TestHarness

# ==============================================================================

# two notes for GithubActions, which installs into
#    /home/runner/work/pyramid_formencode_classic/pyramid_formencode_classic/.tox/py/lib/python3.10/site-packages/
# 1) note the `/.tox/` - the regex requires a "."
# 2) note installed under "/.tox/py/lib/python3.10/site-packages/" and not using the src version
RE_DEBUG_EXECUTED = re.compile(
    r"""DEBUG:pyramid_formencode_classic:  File """
    r""""/(?:.+)/pyramid_formencode_classic/exceptions\.py", """
    r"""line \d+, in debug\n    stack = traceback.extract_stack\(\)\n"""
)


class Form_Example(formencode.Schema):
    id = formencode.validators.Int(not_empty=True, if_missing=None)


class _TestDebugs(_TestHarness):
    _OG_DEBUG_FAILS: bool
    ENV__PYRAMID_FORMENCODE_CLASSIC__DEBUG_FAILS: bool

    assertFalse: Callable
    assertIn: Callable
    assertLogs: Callable
    assertNotIn: Callable
    assertTrue: Callable

    def setUp(self):
        self._OG_DEBUG_FAILS = pyramid_formencode_classic._defaults.DEBUG_FAILS
        pyramid_formencode_classic._defaults.DEBUG_FAILS = (
            self.ENV__PYRAMID_FORMENCODE_CLASSIC__DEBUG_FAILS
        )
        _TestHarness.setUp(self)

    def tearDown(self):
        _TestHarness.tearDown(self)
        pyramid_formencode_classic._defaults.DEBUG_FAILS = self._OG_DEBUG_FAILS

    def test_explicit_raise(self):
        with self.assertLogs("pyramid_formencode_classic", level="DEBUG") as logged:
            try:
                (result, formStash) = pyramid_formencode_classic.form_validate(
                    self.request,
                    schema=Form_Example,
                )
                if not result:
                    raise pyramid_formencode_classic.FormInvalid(formStash)
                raise ValueError("unreachable")
            except pyramid_formencode_classic.FormInvalid:
                if self.ENV__PYRAMID_FORMENCODE_CLASSIC__DEBUG_FAILS:
                    self.assertIn(
                        """INFO:pyramid_formencode_classic:`FormInvalid()` instantiated.""",
                        logged.output,
                    )
                    self.assertIn(
                        "INFO:pyramid_formencode_classic:`FormInvalid().debug()`; "
                        "stacktrace available via `logging.debug`.",
                        logged.output,
                    )
                    self.assertTrue(
                        bool(RE_DEBUG_EXECUTED.search("\n".join(logged.output)))
                    )
                else:
                    self.assertNotIn(
                        """INFO:pyramid_formencode_classic:`FormInvalid()` instantiated.""",
                        logged.output,
                    )
                    self.assertNotIn(
                        "INFO:pyramid_formencode_classic:`FormInvalid().debug()`; "
                        "stacktrace available via `logging.debug`.",
                        logged.output,
                    )
                    self.assertFalse(
                        bool(RE_DEBUG_EXECUTED.search("\n".join(logged.output)))
                    )

    def test_implicit_raise(self):
        with self.assertLogs("pyramid_formencode_classic", level="DEBUG") as logged:
            try:
                (result, formStash) = pyramid_formencode_classic.form_validate(
                    self.request,
                    schema=Form_Example,
                    raise_FormInvalid=True,
                )
                raise ValueError("unreachable")
            except pyramid_formencode_classic.FormInvalid:
                if self.ENV__PYRAMID_FORMENCODE_CLASSIC__DEBUG_FAILS:
                    self.assertIn(
                        """INFO:pyramid_formencode_classic:`FormInvalid()` instantiated.""",
                        logged.output,
                    )
                    self.assertIn(
                        "INFO:pyramid_formencode_classic:`FormInvalid().debug()`; "
                        "stacktrace available via `logging.debug`.",
                        logged.output,
                    )
                    self.assertTrue(
                        bool(RE_DEBUG_EXECUTED.search("\n".join(logged.output)))
                    )
                else:
                    self.assertNotIn(
                        """INFO:pyramid_formencode_classic:`FormInvalid()` instantiated.""",
                        logged.output,
                    )
                    self.assertNotIn(
                        "INFO:pyramid_formencode_classic:`FormInvalid().debug()`; "
                        "stacktrace available via `logging.debug`.",
                        logged.output,
                    )
                    self.assertFalse(
                        bool(RE_DEBUG_EXECUTED.search("\n".join(logged.output)))
                    )

    def test_fatal_field(self):
        with self.assertLogs("pyramid_formencode_classic", level="DEBUG") as logged:
            try:
                self.request.POST["id"] = "1"
                (result, formStash) = pyramid_formencode_classic.form_validate(
                    self.request,
                    schema=Form_Example,
                )
                formStash.fatal_field(
                    field="id",
                    error_field="invoked `fatal_field`",
                )
                raise ValueError("unreachable")
            except pyramid_formencode_classic.FormInvalid:
                if self.ENV__PYRAMID_FORMENCODE_CLASSIC__DEBUG_FAILS:
                    self.assertIn(
                        """INFO:pyramid_formencode_classic:`FormInvalid()` instantiated.""",
                        logged.output,
                    )
                    self.assertIn(
                        "INFO:pyramid_formencode_classic:`FormInvalid().debug()`; "
                        "stacktrace available via `logging.debug`.",
                        logged.output,
                    )
                    self.assertTrue(
                        bool(RE_DEBUG_EXECUTED.search("\n".join(logged.output)))
                    )
                else:
                    self.assertNotIn(
                        """INFO:pyramid_formencode_classic:`FormInvalid()` instantiated.""",
                        logged.output,
                    )
                    self.assertNotIn(
                        "INFO:pyramid_formencode_classic:`FormInvalid().debug()`; "
                        "stacktrace available via `logging.debug`.",
                        logged.output,
                    )
                    self.assertFalse(
                        bool(RE_DEBUG_EXECUTED.search("\n".join(logged.output)))
                    )

    def test_fatal_form(self):
        with self.assertLogs("pyramid_formencode_classic", level="DEBUG") as logged:
            try:
                self.request.POST["id"] = "1"
                (result, formStash) = pyramid_formencode_classic.form_validate(
                    self.request,
                    schema=Form_Example,
                )
                formStash.fatal_form(
                    error_main="invoked `fatal_form`",
                )
                raise ValueError("unreachable")
            except pyramid_formencode_classic.FormInvalid:
                if self.ENV__PYRAMID_FORMENCODE_CLASSIC__DEBUG_FAILS:
                    self.assertIn(
                        """INFO:pyramid_formencode_classic:`FormInvalid()` instantiated.""",
                        logged.output,
                    )
                    self.assertIn(
                        "INFO:pyramid_formencode_classic:`FormInvalid().debug()`; "
                        "stacktrace available via `logging.debug`.",
                        logged.output,
                    )
                    self.assertTrue(
                        bool(RE_DEBUG_EXECUTED.search("\n".join(logged.output)))
                    )
                else:
                    self.assertNotIn(
                        """INFO:pyramid_formencode_classic:`FormInvalid()` instantiated.""",
                        logged.output,
                    )
                    self.assertNotIn(
                        "INFO:pyramid_formencode_classic:`FormInvalid().debug()`; "
                        "stacktrace available via `logging.debug`.",
                        logged.output,
                    )
                    self.assertFalse(
                        bool(RE_DEBUG_EXECUTED.search("\n".join(logged.output)))
                    )

    def test_explicit_debug(self):
        with self.assertLogs("pyramid_formencode_classic", level="DEBUG") as logged:
            self.request.POST["id"] = "1"
            (result, formStash) = pyramid_formencode_classic.form_validate(
                self.request,
                schema=Form_Example,
            )
            # ensure empty
            self.assertNotIn(
                """INFO:pyramid_formencode_classic:`FormInvalid()` instantiated.""",
                logged.output,
            )
            self.assertNotIn(
                "INFO:pyramid_formencode_classic:`FormInvalid().debug()`; "
                "stacktrace available via `logging.debug`.",
                logged.output,
            )
            self.assertFalse(bool(RE_DEBUG_EXECUTED.search("\n".join(logged.output))))

            # trigger stacktrace info line
            formInvalid = pyramid_formencode_classic.FormInvalid(formStash)

            if self.ENV__PYRAMID_FORMENCODE_CLASSIC__DEBUG_FAILS:
                # these will still log based on global controls
                self.assertIn(
                    """INFO:pyramid_formencode_classic:`FormInvalid()` instantiated.""",
                    logged.output,
                )
                self.assertIn(
                    "INFO:pyramid_formencode_classic:`FormInvalid().debug()`; "
                    "stacktrace available via `logging.debug`.",
                    logged.output,
                )
                # and this IS logged yet...
                self.assertTrue(
                    bool(RE_DEBUG_EXECUTED.search("\n".join(logged.output)))
                )
            else:
                # these will NOT log due to lack of global controls
                self.assertNotIn(
                    """INFO:pyramid_formencode_classic:`FormInvalid()` instantiated.""",
                    logged.output,
                )
                self.assertNotIn(
                    "INFO:pyramid_formencode_classic:`FormInvalid().debug()`; "
                    "stacktrace available via `logging.debug`.",
                    logged.output,
                )
                # and this is not logged yet...
                self.assertFalse(
                    bool(RE_DEBUG_EXECUTED.search("\n".join(logged.output)))
                )

            # now invoke the logging
            formInvalid.debug()

            # ensure logged
            self.assertTrue(bool(RE_DEBUG_EXECUTED.search("\n".join(logged.output))))


class TestDebugs__ON(_TestDebugs, unittest.TestCase):
    ENV__PYRAMID_FORMENCODE_CLASSIC__DEBUG_FAILS = True


class TestDebugs__OFF(_TestDebugs, unittest.TestCase):
    ENV__PYRAMID_FORMENCODE_CLASSIC__DEBUG_FAILS = False
