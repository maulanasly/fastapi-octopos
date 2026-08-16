"""Custom WTForms field rendering a curated palette + native color picker.

sqladmin's ``form_overrides`` maps a model column to a WTForms field class;
``ColorField`` renders a curated swatch palette (so category colours keep a
similar tone) plus a native ``<input type="color">`` and a hex text input
(synced by a few lines of inline JS) for custom values.
"""

import re

from markupsafe import Markup
from wtforms.fields import StringField
from wtforms.validators import ValidationError
from wtforms.widgets import TextInput

_HEX_PATTERN = re.compile(r"^#?[0-9A-Fa-f]{6}$")

# Curated pastel tones shared by the admin picker, the palette endpoint,
# and (via that endpoint) the client's category dialogs. Keep the tones
# harmonious so category colours never clash.
CATEGORY_COLOR_PALETTE: list[str] = [
    "#FFE4E6",  # red
    "#FCE7F3",  # pink
    "#F3E8FF",  # purple
    "#E0E7FF",  # indigo
    "#DBEAFE",  # blue
    "#CFFAFE",  # cyan
    "#D1FAE5",  # green
    "#CCFBF1",  # teal
    "#FEF9C3",  # yellow
    "#FEF3C7",  # amber
    "#FFEDD5",  # orange
    "#F5F5F4",  # stone
]


def _swatch_html(field_id: str, value: str, active: bool) -> str:
    border = "2px solid #2563eb" if active else "1px solid #d9dee3"
    check = (
        '<i class="fa-solid fa-check" style="font-size:12px;color:#1e293b"></i>'
        if active
        else ""
    )
    return (
        f'<button type="button" class="btn p-1 me-1 mb-1" data-palette-color="{field_id}" '
        f'data-value="{value}" title="{value}" '
        f'style="width:26px;height:26px;border-radius:50%;background:{value};border:{border};'
        f'padding:0!important;display:inline-flex;align-items:center;justify-content:center;">'
        f"{check}</button>"
    )


class ColorPickerWidget(TextInput):
    """Renders the palette swatch grid + native color input + hex text field."""

    def __call__(self, field, **kwargs):
        value = field._value()
        kwargs.setdefault("id", field.id)
        kwargs.setdefault("class_", "form-control")
        kwargs.setdefault("placeholder", "#E8F5E9")
        text_input = super().__call__(field, **kwargs)

        normalized = value if value and re.match(r"^#[0-9A-Fa-f]{6}$", value) else None
        swatch_value = normalized or "#FFFFFF"
        palette = "".join(
            _swatch_html(field.id, tone, normalized == tone.upper())
            for tone in CATEGORY_COLOR_PALETTE
        )
        return Markup(
            '<div class="mb-2">'
            f'<div data-palette="{field.id}">{palette}</div>'
            "</div>"
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
            f"const swatches=document.querySelectorAll('[data-palette-color=\"{field.id}\"]');"
            "if(!text||!picker)return;"
            "function refreshActive(){"
            "const v=(text.value||'').toUpperCase();"
            "swatches.forEach(function(s){"
            "const active=s.dataset.value===v;"
            "s.style.border=active?'2px solid #2563eb':'1px solid #d9dee3';"
            "s.innerHTML=active?'<i class=\"fa-solid fa-check\" style=\"font-size:12px;color:#1e293b\"></i>':'';"
            "});"
            "}"
            "swatches.forEach(function(s){"
            "s.addEventListener('click',function(){"
            "text.value=s.dataset.value;"
            "picker.value=s.dataset.value;"
            "text.dispatchEvent(new Event('input',{bubbles:true}));"
            "refreshActive();"
            "});"
            "});"
            "picker.addEventListener('input',function(){"
            "text.value=picker.value.toUpperCase();"
            "text.dispatchEvent(new Event('input',{bubbles:true}));"
            "refreshActive();"
            "});"
            "clear.addEventListener('click',function(){"
            "text.value='';"
            "text.dispatchEvent(new Event('input',{bubbles:true}));"
            "refreshActive();"
            "});"
            "})();"
            "</script>"
        )


class ColorField(StringField):
    """Hex color field (``#RRGGBB``) with a curated palette picker widget."""

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
