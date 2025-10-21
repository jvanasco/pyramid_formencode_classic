# stdlib
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

# pypi
from formencode.validators import _
from formencode.validators import FormValidator
from formencode.validators import Invalid

# ==============================================================================


class OnlyOneOf(FormValidator):
    # Field that only one of is allowed
    only_one_ofs: List[str]
    not_empty: bool = False
    __unpackargs__ = ("only_one_ofs",)

    messages = {
        "empty": _("You must submit one and only one of these linked fields."),
        "invalid": _("You may submit only one of these linked fields."),
    }

    def _convert_to_python(self, value_dict: Dict, state: Any) -> Dict:
        is_empty = self.field_is_empty
        presence = [not is_empty(value_dict.get(field)) for field in self.only_one_ofs]
        total_present = presence.count(True)
        if not total_present and self.not_empty:
            raise Invalid(
                _("You must provide a value for one of the fields: %s")
                % ", ".join(["`%s`" % field for field in self.only_one_ofs]),
                value_dict,
                state,
                error_dict=dict(
                    [
                        (
                            field,
                            Invalid(
                                self.message("empty", state),
                                value_dict.get(field),
                                state,
                            ),
                        )
                        for field in self.only_one_ofs
                    ]
                ),
            )
        if total_present > 1:
            raise Invalid(
                _("You may only provide a value for one of the fields: %s")
                % ", ".join(["`%s`" % field for field in self.only_one_ofs]),
                value_dict,
                state,
                error_dict=dict(
                    [
                        (
                            field,
                            Invalid(
                                self.message("invalid", state),
                                value_dict.get(field),
                                state,
                            ),
                        )
                        for field in self.only_one_ofs
                    ]
                ),
            )
        return value_dict


class RequireEmptyIfMissing(FormValidator):
    """
    Require one field to be empty based on another field being present or
    missing.

    This validator is applied to a form, not an individual field (usually
    using a Schema's ``pre_validators`` or ``chained_validators``) and is
    available under both names ``RequireEmptyIfMissing`` and
    ``RequireEmptyIfPresent``.

    If you provide a ``missing`` value (a string key name) then
    if that field is missing the field must not be entered.
    This gives you an either/or situation when used in conjunction with
    ``RequireIfMissing`` or ``RequireIfPresent``

    If you provide a ``present`` value (another string key name) then
    if that field is present, the required field must not be present.

    Note that if you have a validator on the optionally-required
    field, you should probably use ``if_missing=None``.  This way you
    won't get an error from the Schema about a missing value.  For example::

        class PhoneInput(Schema):
            phone_mobile = PhoneNumber()
            phone_work = PhoneNumber()
            chained_validators = [
                # RequireIfMissing
                RequireIfMissing('phone_mobile', present='phone_work'),
                RequireIfMissing('phone_work', present='phone_mobile'),
                # RequireIfPresent
                RequireEmptyIfPresent('phone_mobile', present='phone_mobile'),
                RequireEmptyIfPresent('phone_work', present='phone_mobile'),
            ]
    """

    # Field that potentially is required:
    required: Optional[str] = None
    # If this field is missing, then it is required:
    missing: Optional[str] = None
    # If this field is present, then it is required:
    present: Optional[str] = None

    __unpackargs__ = ("required",)

    messages = {
        "notEmpty": _(
            "Please do not enter a value in this field unless you enter "
            "a value in the linked field."
        )
    }

    def _convert_to_python(self, value_dict: Dict, state: Any) -> Dict:
        is_empty = self.field_is_empty
        if not is_empty(value_dict.get(self.required)) and (
            (self.missing and is_empty(value_dict.get(self.missing)))
            or (self.present and not is_empty(value_dict.get(self.present)))
        ):
            raise Invalid(
                _("You must not give a value for %s") % self.required,
                value_dict,
                state,
                error_dict={
                    self.required: Invalid(
                        self.message("notEmpty", state),
                        value_dict.get(self.required),
                        state,
                    )
                },
            )
        return value_dict


class RequireEmptyIfPresent(RequireEmptyIfMissing):

    messages = {
        "notEmpty": _(
            "Please do not enter a value in this field when you enter "
            "a value in the linked field."
        )
    }
