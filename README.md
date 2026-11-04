# Homework 10 — Task manager ORM queries

The implementation is in `core/homework10.py` and uses
the existing `Task` and `SubTask` models. Status values are taken from
`Task.Status`: `new`, `in_progress`, `done` (labels: New, In progress, Done).

Use Python 3.14+ because the existing models use `uuid.uuid7`.

```sh
make install
make migrate
.venv/bin/python manage.py shell -c "from core.homework10 import run; run()"
```

Run against a separate homework database. The command creates the required
task and two subtasks, reads New tasks and overdue Done subtasks, updates
the three requested fields, and deletes the created task. Django cascades
the deletion to its subtasks. It prints the records and verifies deletion.
Everything runs in one transaction; a failure rolls back the changes.
It never deletes pre-existing tasks to make room for duplicate titles.

The overdue Done query may return an empty list: all records created by the
assignment initially have status New. No extra records or status changes
are required to execute this query.

## Lesson materials

Checked against the two notes linked from Python Adv 19 (Django lessons 19 and 20):
https://lms.itcareerhub.de/course/section.php?id=6475

The solution uses Django Shell and the existing Django ORM, as in the notes:
`objects.create()`, `filter()`, `values()`, `update()`, `delete()`, `exists()`,
`count()`, the `deadline__lt` lookup and `on_delete=models.CASCADE`.
Dates use Python `datetime.timedelta` and Django `timezone.now()` for the
existing timezone-aware DateTimeFields. No additional third-party dependency
is needed. Q, F and bulk operations are covered in the notes but are not
needed for these assignment queries.

The management command `python manage.py homework10` is an alternative launcher
for the same queries. The transaction is a safeguard for repeatable execution.

## Homework 11 — Admin inlines and actions

Implemented using the lesson's built-in Django admin tools in `core/admin.py`:

- `SubTaskInline(admin.StackedInline)` with `extra = 1`, registered in `TaskAdmin.inlines`.
- `short_title` in the task list: first 10 characters plus `...` only for longer titles.
  `Task.__str__()` still returns the complete title used in the subtask task selector.
- `SubTaskAdmin.mark_done` registered in `actions`, with `short_description` and
  `queryset.update(status=Task.Status.DONE)` for selected subtasks only.

No new dependency or model migration is required.

Validation: `python manage.py check`, `python manage.py test` (6 tests pass),
`python manage.py makemigrations --check --dry-run` (no changes).
Admin integration tests cover saving a task with its inline child, full choice labels,
truncation at the 10-character boundary and updating only selected records.

## Homework 12 — Task API (Django REST Framework)

Uses the lesson's `ModelSerializer`, `@api_view`, `Response`, `status`,
`aggregate`, `Count` and `values().annotate()`.

- `POST /api/tasks/create/`: create from title, description, status, deadline; returns 201.
- `GET /api/tasks/`: list tasks; returns 200.
- `GET /api/tasks/<uuid>/`: retrieve by the existing UUID primary key; returns 200 or 404.
- `GET /api/tasks/statistics/`: total, counts for every status (including zeros), overdue count.

Status values: `new`, `in_progress`, `pending`, `blocked`, `done`.
Overdue means `deadline < timezone.now()`, regardless of status.
The tutorial API uses DRF's default permissions; authentication is outside this assignment.

Full endpoint code: `core/api_views.py`, `core/api_urls.py`, `core/serializers.py`;
root URL inclusion: `config/urls.py`. DRF is installed in `config/settings.py`
and pinned with hashes in `requirements.txt`.

Validation: 11 passing tests, Django system check passes, no model migration.
`evidence/homework12-http.json` contains actual curl commands and responses for all
four endpoints, executed against the local Django WSGI application.

## Homework 13 — Serializers and APIView

Continues homework 12 with the lesson's DRF tools:

- `SubTaskCreateSerializer.created_at = serializers.DateTimeField(read_only=True)`.
- `CategoryCreateSerializer.create/update` explicitly reject duplicate category names;
  updating the same category without changing its name is allowed.
- `TaskDetailSerializer` returns every related subtask through a nested, read-only
  `SubTaskSerializer`. The task detail endpoint now uses this serializer.
- `TaskCreateSerializer.validate_deadline` rejects past deadlines; the existing task
  creation endpoint now uses this serializer.
- `SubTaskListCreateView(APIView)`: GET and POST `/api/subtasks/`.
- `SubTaskDetailUpdateDeleteView(APIView)`: GET, PUT, PATCH, DELETE
  `/api/subtasks/<uuid>/` (the existing model uses UUID primary keys).

A category endpoint is not required by this assignment; its serializer is verified
through direct create/update tests. All task/subtask statuses use model choice values.
No new dependency or migration is needed.

Validation: 15 tests pass, including full subtask CRUD, nested child data,
read-only timestamps, past-deadline rejection, invalid relations and statuses,
404 responses, duplicate categories, unchanged names and successful renames.
Django system checks pass; `makemigrations --check --dry-run` reports no changes.

## Homework 14 — Query parameters and pagination

Uses `request.query_params`, `ExtractWeekDay` and DRF `PageNumberPagination`
from the lesson notes. No new dependencies or model migrations.

- `GET /api/tasks/`: all tasks when `weekday` is absent or empty.
- `GET /api/tasks/?weekday=tuesday`: tasks whose **deadline** falls on Tuesday.
  English and Russian weekday names are case-insensitive. Numbers follow Django's
  `ExtractWeekDay`: Sunday=1, Monday=2, Tuesday=3, ..., Saturday=7. Invalid values return 400.
  Date extraction follows the configured Django timezone (UTC in this project).
- `GET /api/subtasks/`: newest first (`-created_at`, `-pk`), five per page.
  The response contains `count`, `next`, `previous`, `results`.
  `?page=2` selects another page; `page_size` can reduce the size but never exceed 5.
- `?task_title=Tuesday%20task`: exact parent task title match.
- `?status=done`: subtask status filter (model values, e.g. new, in_progress, done).
- Both filters combine with AND; omitted/empty filters do not narrow results.
  Filtering happens before pagination. Invalid status returns 400.

Validation: all 18 tests pass. Tests cover weekdays (including Sunday numbering),
no filter, each filter separately, combined filters, empty results, ordering,
page transitions and the hard five-object page limit. The earlier subtask CRUD test
was updated to read the paginated `results` array.
