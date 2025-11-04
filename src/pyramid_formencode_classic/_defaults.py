import os

# ==============================================================================

DEBUG_FAILS = bool(int(os.getenv("PYRAMID_FORMENCODE_CLASSIC__DEBUG_FAILS", "0")))
DEFAULT_FORM_STASH = "_default"
DEFAULT_ERROR_MAIN_KEY = "Error_Main"
DEFAULT_ERROR_MAIN_TEXT = "There was an error with your form."
DEFAULT_ERROR_FIELD_TEXT = "This field has an error."
DEFAULT_ERROR_NOTHING_SUBMITTED = "Nothing submitted."
