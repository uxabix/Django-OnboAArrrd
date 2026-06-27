"""Tests for ``chat`` model configuration that do not touch the database."""

from chat.models import Messages


def test_messages_meta_orders_by_sent_at():
    """Conversation listings should default to chronological order."""
    assert list(Messages._meta.ordering) == ["sent_at"]
