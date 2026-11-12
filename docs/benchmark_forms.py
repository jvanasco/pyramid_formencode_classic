"""Measure the public form validation and reprinting calls."""
import cProfile
import pstats
import statistics
import timeit
from collections.abc import Callable

import formencode
from pyramid.request import Request
from pyramid.response import Response
from webob.multidict import MultiDict

from pyramid_formencode_classic import FormStash, form_reprint, form_validate


class Contact(formencode.Schema):
    email = formencode.validators.Email(not_empty=True)
    username = formencode.validators.UnicodeString(not_empty=True)


class Repeated(formencode.Schema):
    quantities = formencode.ForEach(formencode.validators.Int())


def request_with_stashes() -> Request:
    """Create a Pyramid request with storage for validation results."""
    request = Request.blank("/")
    request.pyramid_formencode_classic = {}
    return request


contact_request = request_with_stashes()
contact_schema = Contact()
contact_params = MultiDict({"email": "person@example.com", "username": "alice"})
repeated_request = request_with_stashes()
repeated_schema = Repeated()
repeated_params = MultiDict(
    [("quantities", value) for value in ("2", "bad", "5", "worse")]
)
render_request = request_with_stashes()
_, render_stash = form_validate(
    render_request,
    contact_schema,
    validate_params=MultiDict({"email": "invalid", "username": "alice"}),
)
markup = (
    '<form><input name="email" type="text" /><form:error name="email"/>'
    '<input name="username" type="text" /></form>'
)


def validate_contact() -> tuple[bool, FormStash]:
    """Validate two scalar fields."""
    return form_validate(contact_request, contact_schema, validate_params=contact_params)


def reject_repeated() -> tuple[bool, FormStash]:
    """Validate four repeated values, including two invalid integers."""
    return form_validate(repeated_request, repeated_schema, validate_params=repeated_params)


def render_form() -> Response:
    """Provide fresh markup for each form reprint."""
    return Response(text=markup, charset="utf-8")


def reprint_errors() -> Response:
    """Repopulate form values and render the email error."""
    response = form_reprint(render_request, render_form)
    render_stash._reprints.clear()
    return response


def measure(label: str, action: Callable[[], object]) -> None:
    """Warm the case, then measure wall time and profile in separate passes."""
    timer = timeit.Timer(action)
    timer.timeit(number=500)
    samples = [seconds * 1_000_000 / 3000 for seconds in timer.repeat(9, 3000)]
    print(
        f"{label}: median {statistics.median(samples):.1f} us, "
        f"range {min(samples):.1f}–{max(samples):.1f} us, "
        f"samples {', '.join(f'{sample:.1f}' for sample in samples)}"
    )
    profiler = cProfile.Profile()
    with profiler:
        for _ in range(3000):
            action()
    stats = pstats.Stats(profiler).strip_dirs()
    stats.sort_stats("cumulative").print_stats(20)
    stats.sort_stats("tottime").print_stats(12)


assert validate_contact()[0]
valid, rejected = reject_repeated()
assert not valid and "integer" in rejected.errors["quantities"]
reprinted = reprint_errors()
assert 'value="alice"' in reprinted.text and render_stash.errors["email"] in reprinted.text

measure("valid submission", validate_contact)
measure("rejected repeated submission", reject_repeated)
measure("HTML reprint with errors", reprint_errors)
