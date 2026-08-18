"""WTForms field for the admin user form's password.

Renders a masked password input that is always blank (the existing bcrypt
hash is never shown). ``on_model_change`` in UserAdmin hashes any
non-empty submission before sqladmin applies the form data, so a raw
password is never persisted.
"""

from wtforms.fields import StringField
from wtforms.widgets import PasswordInput


class AdminPasswordField(StringField):
    """Password input for the admin panel (always renders blank)."""

    widget = PasswordInput()

    def _value(self):
        # Never pre-fill with the stored hash.
        return ""

    def __call__(self, **kwargs):
        kwargs.setdefault("placeholder", "Leave blank to keep current")
        kwargs.setdefault("autocomplete", "new-password")
        return super().__call__(**kwargs)
