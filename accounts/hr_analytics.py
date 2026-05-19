"""Period-based onboarding statistics for the HR dashboard."""

from collections import defaultdict
from datetime import timedelta

from django.utils import timezone
from django.utils.dateparse import parse_date

from onboarding.models import User_paths, User_tasks

# Default analytics window when the HR panel is opened without explicit dates.
_DEFAULT_STATS_DAYS = 30
_MIN_RANKING_TASKS = 1

# Weighted outcome scale (0–1) used for student/mentor leaderboards.
_OUTCOME_WEIGHTS = {
    "on_time": 1.0,
    "late": 0.35,
    "on_track": 0.75,
    "approaching": 0.5,
    "overdue": 0.0,
}


def _avg(values):
    """Return arithmetic mean rounded to one decimal, or ``None`` when empty."""
    if not values:
        return None
    return round(sum(values) / len(values), 1)


def _pct(part, whole):
    """Return percentage rounded to one decimal, or ``0`` when ``whole`` is zero."""
    if not whole:
        return 0.0
    return round(100 * part / whole, 1)


def _days_from_assignment_to_submission(user_task, submission_date):
    """Calendar days from assignment to first submission, never negative.

    ``Task_status.change_date`` is date-only and may precede ``created_at`` in
    imported or seeded data; negative deltas are treated as same-day completion.
    """
    assigned_on = timezone.localdate(user_task.created_at)
    return max(0, (submission_date - assigned_on).days)


def _new_person_stats():
    """Mutable accumulator for per-user task/path counters."""
    return {
        "user": None,
        "tasks_total": 0,
        "on_time": 0,
        "late": 0,
        "overdue": 0,
        "on_track": 0,
        "approaching": 0,
        "paths_total": 0,
        "student_ids": set(),
    }


def _role_name_lower(user):
    """Normalize ``Roles.name`` for mentor/student filtering."""
    if not user:
        return ""
    role = getattr(user, "role", None)
    if not role or not role.name:
        return ""
    return role.name.strip().lower()


def _person_display_name(user):
    """Prefer full name; fall back to email."""
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    return full_name or user.email


def _performance_index(stats):
    """Score task outcomes on a 0–100 scale (higher is better)."""
    total = stats["tasks_total"]
    if total < _MIN_RANKING_TASKS:
        return None
    weighted = sum(stats[state] * _OUTCOME_WEIGHTS[state] for state in _OUTCOME_WEIGHTS)
    return round(100 * weighted / total, 1)


def _mentor_index(stats):
    """Extend performance index with breadth, volume, paths, and stars bonuses."""
    base = _performance_index(stats)
    if base is None:
        return None
    user = stats.get("user")
    stars = max(0, getattr(user, "stars", 0) or 0)
    students = len(stats["student_ids"])
    breadth = min(1.15, 1.0 + 0.04 * max(0, students - 1))
    volume = min(1.10, 1.0 + 0.015 * max(0, min(stats["tasks_total"] - 1, 10)))
    paths_bonus = min(1.05, 1.0 + 0.01 * min(stats["paths_total"], 5))
    stars_bonus = min(1.08, 1.0 + 0.02 * min(stars, 4))
    return round(min(100.0, base * breadth * volume * paths_bonus * stars_bonus), 1)


def _serialize_leader(user, score, stats, *, students_count=None):
    """Build a template-friendly dict for the best student/mentor cards."""
    payload = {
        "user_id": user.pk,
        "display_name": _person_display_name(user),
        "email": user.email,
        "score": score,
        "tasks_total": stats["tasks_total"],
        "on_time_count": stats["on_time"],
        "on_time_pct": _pct(stats["on_time"], stats["tasks_total"]),
        "paths_total": stats["paths_total"],
    }
    if students_count is not None:
        payload["students_count"] = students_count
        payload["stars"] = max(0, getattr(user, "stars", 0) or 0)
    return payload


def _pick_best(candidates, score_field, tiebreaker_field=None):
    """Return the highest-scoring candidate with deterministic tie-breakers."""
    if not candidates:
        return None

    def sort_key(row):
        key = [-row[score_field]]
        if tiebreaker_field:
            key.append(-(row.get(tiebreaker_field) or 0))
        key.extend([-row["on_time_count"], -row["tasks_total"], row["display_name"].lower()])
        return tuple(key)

    candidates.sort(key=sort_key)
    return candidates[0]


def _accumulate_task_for_person(stats, state):
    """Increment counters for a single ``User_tasks`` row."""
    stats["tasks_total"] += 1
    stats[state] += 1


def _compute_leaderboards(task_qs, path_qs):
    """Derive best student/mentor for assignments in the filtered queryset."""
    student_stats = defaultdict(_new_person_stats)
    mentor_stats = defaultdict(_new_person_stats)

    for user_task in task_qs:
        state = user_task.deadline_state

        student = user_task.user_id
        if student and student.pk:
            bucket = student_stats[student.pk]
            bucket["user"] = student
            _accumulate_task_for_person(bucket, state)

        mentor = user_task.assigned_by
        if mentor and mentor.pk:
            bucket = mentor_stats[mentor.pk]
            bucket["user"] = mentor
            _accumulate_task_for_person(bucket, state)
            if student and student.pk:
                bucket["student_ids"].add(student.pk)

    for user_path in path_qs:
        mentor = user_path.assigned_by
        if mentor and mentor.pk:
            mentor_stats[mentor.pk]["user"] = mentor
            mentor_stats[mentor.pk]["paths_total"] += 1

    student_candidates = []
    for stats in student_stats.values():
        user = stats["user"]
        if _role_name_lower(user) != "student":
            continue
        score = _performance_index(stats)
        if score is None:
            continue
        student_candidates.append(_serialize_leader(user, score, stats))

    mentor_candidates = []
    for stats in mentor_stats.values():
        user = stats["user"]
        if _role_name_lower(user) != "mentor":
            continue
        score = _mentor_index(stats)
        if score is None:
            continue
        mentor_candidates.append(
            _serialize_leader(user, score, stats, students_count=len(stats["student_ids"]))
        )

    return {
        "best_student": _pick_best(student_candidates, "score"),
        "best_mentor": _pick_best(mentor_candidates, "score", tiebreaker_field="stars"),
    }


def parse_hr_stats_period(stats_from="", stats_to="", *, apply_default=True, all_time=False):
    """Parse optional ``stats_from`` / ``stats_to`` date strings (``YYYY-MM-DD``).

    When both are empty, ``all_time`` is false, and ``apply_default`` is true,
    returns the last ``_DEFAULT_STATS_DAYS`` ending today. When ``all_time`` is
    true, both bounds are ``None`` (no date filter).

    Returns:
        tuple[date | None, date | None, str, str]: Parsed bounds and the
        normalized string values for form fields.
    """
    if all_time:
        return None, None, "", ""

    raw_from = (stats_from or "").strip()
    raw_to = (stats_to or "").strip()
    date_from = parse_date(raw_from) if raw_from else None
    date_to = parse_date(raw_to) if raw_to else None

    if apply_default and date_from is None and date_to is None:
        today = timezone.now().date()
        date_to = today
        date_from = today - timedelta(days=_DEFAULT_STATS_DAYS)
        return date_from, date_to, date_from.isoformat(), date_to.isoformat()

    display_from = date_from.isoformat() if date_from else ""
    display_to = date_to.isoformat() if date_to else ""
    return date_from, date_to, display_from, display_to


def compute_hr_analytics(date_from=None, date_to=None):
    """Aggregate onboarding metrics for assignments created in ``[date_from, date_to]``.

    Task metrics use ``User_tasks.created_at``; path metrics use
    ``User_paths.assigned_at``. Timeliness reuses ``User_tasks.deadline_state``.

    Returns:
        dict: Counts, percentages, and average day deltas for the HR template.
    """
    task_qs = (
        User_tasks.objects.select_related(
            "user_id",
            "user_id__role",
            "task_id",
            "assigned_by",
            "assigned_by__role",
        )
        .prefetch_related("statuses")
        .all()
    )
    path_qs = User_paths.objects.select_related(
        "user", "path", "assigned_by", "assigned_by__role"
    ).all()

    if date_from:
        task_qs = task_qs.filter(created_at__date__gte=date_from)
        path_qs = path_qs.filter(assigned_at__date__gte=date_from)
    if date_to:
        task_qs = task_qs.filter(created_at__date__lte=date_to)
        path_qs = path_qs.filter(assigned_at__date__lte=date_to)

    today = timezone.now().date()

    state_counts = {
        "on_time": 0,
        "late": 0,
        "overdue": 0,
        "on_track": 0,
        "approaching": 0,
    }
    completion_days = []
    late_days = []
    overdue_days = []
    remaining_days = []
    users_with_tasks = set()

    for user_task in task_qs:
        if user_task.user_id_id:
            users_with_tasks.add(user_task.user_id_id)
        state = user_task.deadline_state
        state_counts[state] += 1

        if state in ("on_time", "late"):
            submission = user_task.submission_date
            if submission is not None:
                completion_days.append(
                    _days_from_assignment_to_submission(user_task, submission)
                )
            if state == "late" and submission is not None:
                late_days.append(max(0, (submission - user_task.deadline).days))
        elif state == "overdue":
            overdue_days.append((today - user_task.deadline).days)
        else:
            remaining_days.append((user_task.deadline - today).days)

    tasks_total = sum(state_counts.values())
    paths_total = path_qs.count()
    users_with_paths = {
        row for row in path_qs.exclude(user_id__isnull=True).values_list("user_id", flat=True)
    }

    submitted_count = state_counts["on_time"] + state_counts["late"]
    open_count = state_counts["on_track"] + state_counts["approaching"]
    not_on_time_count = state_counts["late"] + state_counts["overdue"]
    leaderboards = _compute_leaderboards(task_qs, path_qs)

    return {
        "tasks_total": tasks_total,
        "paths_total": paths_total,
        "users_with_tasks": len(users_with_tasks),
        "users_with_paths": len(users_with_paths),
        "avg_tasks_per_user": round(tasks_total / len(users_with_tasks), 1)
        if users_with_tasks
        else None,
        "avg_paths_per_user": round(paths_total / len(users_with_paths), 1)
        if users_with_paths
        else None,
        "submitted_count": submitted_count,
        "on_time_count": state_counts["on_time"],
        "on_time_pct": _pct(state_counts["on_time"], tasks_total),
        "late_count": state_counts["late"],
        "late_pct": _pct(state_counts["late"], tasks_total),
        "overdue_count": state_counts["overdue"],
        "overdue_pct": _pct(state_counts["overdue"], tasks_total),
        "not_on_time_count": not_on_time_count,
        "not_on_time_pct": _pct(not_on_time_count, tasks_total),
        "open_count": open_count,
        "on_track_count": state_counts["on_track"],
        "approaching_count": state_counts["approaching"],
        "avg_completion_days": _avg(completion_days),
        "avg_days_late": _avg(late_days),
        "avg_days_overdue": _avg(overdue_days),
        "avg_days_remaining": _avg(remaining_days),
        "period_from": date_from,
        "period_to": date_to,
        "best_student": leaderboards["best_student"],
        "best_mentor": leaderboards["best_mentor"],
    }
