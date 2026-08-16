"""Custom WTForms field rendering a native color picker for category colors.

sqladmin's ``form_overrides`` maps a model column to a WTForms field class;
``ColorField`` renders an ``<input type="color">`` plus a hex text input
(synced by a few lines of inline JS) so admins can pick a colour visually
instead of typing hex codes.
"""
import re

from markupsafe import Markup
from wtforms.fields import StringField
from wtforms.validators import ValidationError
from wtforms.widgets import TextInput

_HEX_PATTERN = re.compile(r"^#?[0-9A-Fa-f]{6}$")


class ColorPickerWidget(TextInput):
    """Renders the color swatch input + synced hex text field."""

    def __call__(self, field, **kwargs):
        value = field._value()
        kwargs.setdefault("id", field.id)
        kwargs.setdefault("class_", "form-control")
        kwargs.setdefault("placeholder", "#E8F5E9")
        text_input = super().__call__(field, **kwargs)

        swatch_value = (
            value if value and re.match(r"^#[0-9A-Fa-f]{6}$", value) else "#FFFFFF"
        )
        return Markup(
            '<div class="d-flex align-items-center gap-2">'
            f'<input type="color" value="{swatch_value}" '
            f'data-color-target="{field.id}" style="width:38px;height:34px;'
            'border:1px solid #d9dee3;border-radius:6px;padding:2px;cursor:pointer;">'
            f"{text_input}"
            '<button type="button" class="btn btn-outline-secondary btn-sm" '
            f'data-clear-color="{field.id}" title="Clear color">'
            '<i class="fa-solid fa-eraser"></i></button>'
            "</div>"
            "<script>"
            "(function(){"
            f"const text=document.getElementById('{field.id}');"
            f"const picker=document.querySelector('[data-color-target=\"{field.id}\"]');"
            f"const clear=document.querySelector('[data-clear-color=\"{field.id}\"]');"
            "if(!text||!picker)return;"
            "picker.addEventListener('input',()=>{"
            "text.value=picker.value.toUpperCase();"
            "text.dispatchEvent(new Event('input',{bubbles:true}));"
            "});"
            "clear.addEventListener('click',()=>{"
            "text.value='';"
            "text.dispatchEvent(new Event('input',{bubbles:true}));"
            "});"
            "})();"
            "</script>"
        )


class ColorField(StringField):
    """Hex color field (``#RRGGBB``) with a native color picker widget."""

    widget = ColorPickerWidget()

    def process_formdata(self, valuelist):
        if not valuelist:
            self.data = None
            return
        raw = (valuelist[0] or "").strip()
        if not raw:
            self.data = None
            return
        value = raw.upper()
        if not value.startswith("#"):
            value = f"#{value}"
        self.data = value

    def pre_validate(self, form):
        if self.data is None:
            return
        if not _HEX_PATTERN.match(self.data):
            raise ValidationError("Color must be a hex value like #E8F5E9")
