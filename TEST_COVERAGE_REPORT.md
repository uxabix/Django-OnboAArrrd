# Test Coverage Report — OnboAArrrd

**Last updated:** 2026-05-17  
**Branch:** `feature/unit-tests` (at time of report)  
**Test runner:** pytest 8.x + pytest-django + pytest-cov  
**Database:** PostgreSQL (Docker `web` service; required for migrations)

---

## Executive summary

| Metric | Value |
|--------|------:|
| **Tests collected** | 90 |
| **Tests passed** | 90 |
| **Line coverage (statements)** | **55%** (773 / 1971 statements missed) |
| **Branch coverage** | Enabled (`branch = True` in `.coveragerc`) |
| **Partial branches** | 105 partial branches reported |

The suite focuses on **high-value, low-flake** areas: authorization helpers, form validation, model behaviour, middleware, and **targeted HTTP integration** flows. Large view modules (`onboarding/views.py`, `chat/views.py`, parts of `hr_views.py`) are only partially covered by design; infrastructure and seeding are excluded from metrics.

---

## How to run tests

### Recommended (Docker)

```bash
docker compose exec web pytest
docker compose exec web pytest -vv
docker compose exec web pytest --cov --cov-config=.coveragerc --cov-report=term-missing
docker compose exec web pytest --cov --cov-config=.coveragerc --cov-report=html
```

HTML output: `htmlcov/index.html` (git-ignored).

### Local (without Docker)

Requires `POSTGRES_*` and `SECRET_KEY` from `.env` pointing at a reachable PostgreSQL instance. Tests are **not** configured for SQLite because migrations include PostgreSQL-specific SQL.

### Configuration files

| File | Role |
|------|------|
| `pytest.ini` | `DJANGO_SETTINGS_MODULE`, test discovery under `*/tests/` |
| `.coveragerc` | Source roots, omissions, branch coverage |
| `conftest.py` | Shared fixtures (roles, users, catalog task) |

---

## Coverage configuration

### Measured packages

`accounts`, `chat`, `core`, `onboarding`, `OnboAArrrd`

### Intentionally omitted from coverage

These paths are excluded in `.coveragerc` because they are wiring, dev tooling, or empty packages—not application logic under test:

| Pattern | Reason |
|---------|--------|
| `*/__init__.py` | Empty package markers |
| `*/migrations/*` | Generated schema history |
| `*/tests/*` | Test code itself |
| `*/seeds/*` | Demo/local data seeders |
| `*/management/commands/seed.py` | Seeding orchestration |
| `*/management/commands/seed_demo.py` | Demo seed command |
| `*/management/commands/clear_test_data.py` | Dev cleanup command |
| `*/asgi.py`, `*/wsgi.py` | ASGI/WSGI entrypoints |
| `*/urls.py`, `*/routing.py` | URL routing tables |
| `manage.py` | Django CLI entry |

---

## Coverage by module

Snapshot from `pytest --cov` on 2026-05-17 (Linux / Python 3.11 in Docker):

| Module | Stmts | Miss | Cover | Notes |
|--------|------:|-----:|------:|-------|
| **TOTAL** | **1971** | **773** | **55%** | |
| `OnboAArrrd/settings.py` | 31 | 0 | 100% | |
| `accounts/decorators.py` | 29 | 0 | **100%** | Role helpers + `hr_required` |
| `accounts/admin.py` | 20 | 0 | **100%** | |
| `accounts/apps.py` | 4 | 0 | 100% | |
| `chat/admin.py` | 1 | 0 | 100% | |
| `chat/apps.py` | 4 | 0 | 100% | |
| `chat/forms.py` | 7 | 0 | **100%** | |
| `chat/models.py` | 16 | 0 | **100%** | |
| `accounts/middleware.py` | 31 | 2 | **96%** | |
| `accounts/models.py` | 56 | 1 | **98%** | |
| `onboarding/admin.py` | 83 | 1 | **98%** | |
| `onboarding/forms.py` | 42 | 0 | **98%** | |
| `accounts/forms.py` | 117 | 5 | **93%** | |
| `accounts/views.py` | 78 | 2 | **94%** | |
| `onboarding/models.py` | 215 | 10 | **92%** | |
| `accounts/hr_views.py` | 392 | 210 | **44%** | Partial HR HTTP + helpers |
| `chat/views.py` | 245 | 125 | **44%** | Inbox, polling, helpers |
| `onboarding/views.py` | 533 | 354 | **29%** | Student/mentor critical paths only |
| `chat/consumers.py` | 63 | 63 | **0%** | WebSockets—not in scope yet |

---

## Test inventory (90 tests)

Tests live next to each app under `<app>/tests/test_*.py`. Shared fixtures are in the repository root `conftest.py`.

### `accounts` (47 tests)

| Test file | Type | What is covered |
|-----------|------|-----------------|
| `test_decorators.py` | Unit | `user_has_hr_role`, `user_is_administrator_role`, `user_can_access_hr_panel`, `hr_required` (allow HR / deny student) |
| `test_models_unit.py` | Unit | `Roles.__str__` without DB |
| `test_models_db.py` | DB | `CustomUserManager` (email validation, superuser, unusable password), `get_stars_display`, `is_mentor`, persisted `Roles.__str__` |
| `test_forms.py` | Unit + DB | Bootstrap widget helper; HR add/change email/mentor/export/import form validation |
| `test_middleware.py` | Unit + DB | `ForceInitialPasswordChangeMiddleware` redirect, exempt paths (password change, login/logout, static/media) |
| `test_admin.py` | DB | `CustomUserAdmin.get_mentor` |
| `test_views_smoke.py` | HTTP | `home`, `logged` (HR flag in context) |
| `test_views_integration.py` | HTTP | User search JSON API, profile stats, mentor ranking, forced password change GET/POST |
| `test_hr_helpers.py` | Unit + DB | `_hr_can_manage_actor`, `_hr_can_change_role_for_target`, `_parse_hr_list_params`, `_apply_hr_list_filters`, `_preservation_dict` |
| `test_hr_views_integration.py` | HTTP | HR dashboard 200/403, add employee, terminate/reactivate, invalid DB export POST |

### `onboarding` (28 tests)

| Test file | Type | What is covered |
|-----------|------|-----------------|
| `test_view_constants.py` | Unit | `DEADLINE_FILTERS`, `TASK_LIST_SORT_OPTIONS` contract |
| `test_models_str.py` | Unit | `__str__` on badges, paths, tasks, quiz models |
| `test_models_user_tasks_db.py` | DB | `User_tasks` status/deadline properties, mentor stars signal on completion |
| `test_forms.py` | DB | `UserTaskForm` / `UserPathForm` search filtering and labels |
| `test_admin.py` | Unit | `BadgesAdmin.icon_tag` without image |
| `test_views_integration.py` | HTTP | Student task list, task detail ownership, submit task, mentor status change (allow/deny), mentor task management page |

### `chat` (7 tests)

| Test file | Type | What is covered |
|-----------|------|-----------------|
| `test_models_meta.py` | Unit | `Messages` default ordering |
| `test_forms.py` | Unit | `MessageForm` fields and widget attrs |
| `test_views_integration.py` | Unit + HTTP | `_display_name`, `_load_context`, inbox render, `chat_student` alias, `chat_updates` JSON polling |

### Shared fixtures (`conftest.py`)

| Fixture | Purpose |
|---------|---------|
| `mentor_role`, `student_role`, `hr_role` | `Roles` rows for tests |
| `mentor_user`, `student_user`, `hr_user` | Authenticated users with typical relationships |
| `competency_path`, `catalog_task` | Minimal onboarding catalog |
| `assigned_user_task` | `User_tasks` row linking student, mentor, and task |

---

## Logic covered by application area

### Authentication and authorization

- HR panel access rules (`accounts/decorators.py`) — **full**
- HR-only view wrapper returns 403 for students — **tested**
- Forced password change middleware redirect and exemptions — **tested**
- First-login password change flow (GET form + POST success) — **tested**

### User and role management (HR)

- Dashboard list render for HR vs 403 for student — **tested**
- Add employee with temporary password flags — **tested**
- Terminate / reactivate employee — **tested**
- Permission helpers for who can manage whom — **unit tested**
- List filter parsing and search — **unit tested**
- Form-level validation for add employee, email uniqueness, mentor assignment rules, export/import — **mostly tested** (~93% forms)

**Not tested (HR):** successful DB export/import downloads, change role/email/mentor POST handlers, password reset, own-password change, full dashboard filter combinations, serializer round-trips.

### Public accounts views

- Landing and post-login hub — **smoke tested**
- JSON user autocomplete — **tested**
- Own profile task aggregates — **tested**
- Mentor ranking page — **tested**
- Viewing another user's profile with search — **partially covered** (missing line ~83 branch)

### Onboarding — domain model

- Task workflow properties (`current_status`, `is_overdue`, `deadline_state`, submission timestamps) — **tested on DB**
- Post-save mentor `stars` increment when status updated to completed — **tested**
- Model `__str__` methods — **tested**

### Onboarding — HTTP (student & mentor)

- Task list with assigned work — **tested**
- Task detail enforces owner — **tested**
- Submit task → `do weryfikacji` status — **tested**
- Duplicate submit does not create extra status row — **tested**
- Mentor changes task status; foreign mentor denied — **tested**
- Mentor management page for a mentee — **tested**

**Not tested (onboarding views):** calendar views, path list/detail, competency path assignment, task CRUD (create/edit/delete), inline create, JSON path-tasks API, most filter/sort branches in task list.

### Chat

- Message form metadata — **tested**
- Inbox render (empty state) — **tested**; fixed `selected_query is None` bug during test development
- Polling endpoint returns new messages — **tested**
- Task-scoped context resolution — **tested**

**Not tested (chat):** POST new message, dual-pane secondary user, thread filters (`show`, `relation`, `sort`), task/path thread building loops, `chat_mentor` with `student_id`.

### WebSockets

- `chat/consumers.py` — **0%**; requires Channels test utilities (`WebsocketCommunicator`), not Django test client.

---

## What was consciously not covered

| Area | Rationale |
|------|-----------|
| **Database seeders** (`*/seeds/*`, `seed`, `seed_demo`) | Dev/demo tooling; idempotency better checked manually or via smoke scripts |
| **`clear_test_data` management command** | Destructive dev utility |
| **URLConf / ASGI / WSGI / routing** | Declarative wiring; low regression value per line |
| **`__init__.py` files** | Empty |
| **Full `hr_views.py`** | Large surface; import/export and every POST variant need heavy fixtures; core permissions and lifecycle paths covered first |
| **Full `onboarding/views.py`** | ~1300 lines; UI-heavy; prefer scenario tests over line coverage |
| **Full `chat/views.py`** | Complex inbox UI; polling and helpers covered first |
| **`chat/consumers.py`** | Different test stack (async WebSocket) |
| **Templates / CSS / JS** | Not unit-tested (would be E2E or visual regression) |
| **Sphinx docs build** | Out of scope for pytest |

---

## Known gaps and recommended next steps

Priority order for future tests:

1. **HR POST flows** — `hr_change_role`, `hr_change_email`, `hr_change_mentor` (happy path + permission denied).
2. **Onboarding mentor flows** — `mentor_assign_task`, `mentor_assign_path` (minimal catalog + redirect).
3. **Chat** — POST a message through `chat_inbox`; assert DB row and redirect.
4. **WebSockets** — 2–3 tests with `channels.testing` for connect/disconnect and message broadcast.
5. **HR export** — valid JSON export returns `200` and `Content-Disposition` (mock or small fixture DB).

Avoid chasing **80%+ line coverage** on `onboarding/views.py` without extracting query/filter logic into testable functions (pattern already used for `DEADLINE_FILTERS` / `TASK_LIST_SORT_OPTIONS`).

---

## Production bug found by tests

While adding chat integration tests, `chat_inbox` crashed when no conversation partner was selected and the thread list was empty: `urlencode(selected_query)` received `None`. Fixed by normalizing `selected_query` to `{}` when unresolved.

---

## CI and artifacts

Generated artifacts (git-ignored per `.gitignore`):

- `.coverage`
- `coverage.xml`
- `htmlcov/`

No GitHub Actions workflow was verified for this report; run the Docker commands above in CI for consistent numbers.

---

## Related documentation

- `README.md` — “Automated tests (pytest)” section (commands and practices)
- `.coveragerc` — authoritative omit list and source roots
- `pytest.ini` — discovery paths and markers

---

*Regenerate the metrics section after significant test changes by running:*

```bash
docker compose exec web pytest --cov --cov-config=.coveragerc --cov-report=term-missing
```

*Then update **Last updated** and the tables in this file.*
