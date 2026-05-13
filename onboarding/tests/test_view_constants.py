"""Sanity checks for onboarding view module constants (no ORM access)."""

from onboarding.views import DEADLINE_FILTERS, TASK_LIST_SORT_OPTIONS


def test_deadline_filters_define_expected_keys():
    """Deadline filter keys drive query parsing; keep the baseline contract stable."""
    assert set(DEADLINE_FILTERS.keys()) >= {"all", "active", "overdue", "completed"}


def test_task_list_sort_options_include_deadline_variants():
    """Task list sorting should always expose ascending and descending deadlines."""
    assert "deadline" in TASK_LIST_SORT_OPTIONS
    assert "-deadline" in TASK_LIST_SORT_OPTIONS
