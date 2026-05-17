"""Tests for ``chat.forms``."""

from chat.forms import MessageForm


def test_message_form_meta_fields():
    form = MessageForm()
    assert list(form.fields.keys()) == ["text"]
    assert form.fields["text"].widget.attrs.get("rows") == 3
