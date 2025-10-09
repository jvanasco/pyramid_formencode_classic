# stdlib
from typing import Any
from typing import Dict
from typing import List

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

    def _convert_to_python(self, value_dict: Dict, state: Any):
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
