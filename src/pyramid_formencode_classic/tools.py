# stdlib
from typing import Any
from typing import Dict
from typing import Union

# pypi
import formencode
from formencode.api import NoDefault
from formencode.validators import FancyValidator
from formencode.validators import FormValidator
from formencode.validators import OneOf

# ==============================================================================


def document_form(form: formencode.schema.Schema) -> Dict:

    def _document_validator(validator: Union[FancyValidator, FormValidator]) -> Dict:
        subdict: Dict[str, Any] = {"type": None}
        if isinstance(validator, FancyValidator):
            if_missing = validator.if_missing
            if if_missing is not NoDefault:
                subdict["if_missing"] = if_missing
            subdict["not_empty"] = validator.not_empty
        for attr in (
            "max",
            "min",
            "missing",
            "only_one_ofs",  # pyramid_formencode_classic.validators.OnlyOneOf
            "present",
            "required",
        ):
            if hasattr(validator, attr):
                subdict[attr] = getattr(validator, attr)

        subdict["type"] = validator.__class__.__name__
        if isinstance(validator, OneOf):
            subdict["options"] = validator.list

        return subdict

    rval: Dict[str, Any] = {}
    for field, validator in form.fields.items():
        rval[field] = _document_validator(validator)

    if hasattr(form, "chained_validators"):
        if form.chained_validators:
            # validator will be a list of FancyValidators
            rval["chained_validators"] = [
                _document_validator(i) for i in form.chained_validators
            ]

    return rval
