"""Unit tests for the admin category color picker field."""

import re

import pytest
from wtforms import Form

from app.admin.color_field import CATEGORY_COLOR_PALETTE, ColorField

pytestmark = pytest.mark.no_db


class _MultiDict:
    """Minimal formdata stand-in matching wtforms' MultiDict contract:
    iterable of keys, contains, and getlist."""

    def __init__(self, values=None):
        self._values = values or {}

    def __iter__(self):
        return iter(self._values.keys())

    def __contains__(self, key):
        return key in self._values

    def __len__(self):
        return sum(len(items) for items in self._values.values())

    def getlist(self, key, type=None):
        raw = self._values.get(key, [])
        if type is None:
            return list(raw)
        return [type(v) for v in raw]


class _ColorForm(Form):
    color = ColorField()


def test_widget_renders_color_input_and_sync_script():
    form = _ColorForm(data={"color": "#E8F5E9"})
    html = form.color()
    assert 'type="color"' in html
    assert 'value="#E8F5E9"' in html
    assert f'id="{form.color.id}"' in html
    assert "data-clear-color" in html
    assert "addEventListener" in html


def test_widget_renders_palette_swatches():
    form = _ColorForm(data={"color": "#D1FAE5"})
    html = form.color()
    assert f'data-palette-color="{form.color.id}"' in html
    assert 'data-value="#D1FAE5"' in html
    for tone in CATEGORY_COLOR_PALETTE:
        assert f'data-value="{tone}"' in html


def test_palette_is_valid_hex_and_large_enough():
    assert len(CATEGORY_COLOR_PALETTE) >= 8
    for tone in CATEGORY_COLOR_PALETTE:
        assert re.match(r"^#[0-9A-Fa-f]{6}$", tone), tone


def test_process_formdata_normalizes_hex():
    form = _ColorForm(formdata=_MultiDict({"color": ["e8f5e9"]}))
    assert form.color.data == "#E8F5E9"

    form = _ColorForm(formdata=_MultiDict({"color": ["#ff8800"]}))
    assert form.color.data == "#FF8800"


def test_process_formdata_empty_is_none():
    form = _ColorForm(formdata=_MultiDict({"color": [""]}))
    assert form.color.data is None

    form = _ColorForm(formdata=_MultiDict())
    assert form.color.data is None


def test_pre_validate_rejects_bad_hex():
    for bad in ("green", "#GGGGGG", "#FFF"):
        form = _ColorForm(formdata=_MultiDict({"color": [bad]}))
        assert form.validate() is False
        assert form.color.errors

    form = _ColorForm(formdata=_MultiDict({"color": ["#E8F5E9"]}))
    assert form.validate() is True
    assert not form.color.errors
