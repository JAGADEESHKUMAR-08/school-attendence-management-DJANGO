# School Attendance Management

Django app for marking and reporting school attendance.

## Setup

```bash
python manage.py migrate
python manage.py seed_data      # optional demo data
python manage.py runserver
```

Open http://127.0.0.1:8000/

> **Troubleshooting (CSRF / "site can't be reached"):** use a single host
> (`127.0.0.1`, not mixed with `localhost`). If another Django project already
> uses port 8000, run this one on a different port, e.g.
> `python manage.py runserver 127.0.0.1:8001`. This project uses its own cookie
> names (`sa_csrftoken`, `sa_sessionid`) so it won't clash with other projects on
> the same host. If you ever see a CSRF error, you are automatically redirected
> back to the sign-in page with a fresh token — just sign in again.

## Demo accounts (after seed_data)

| Role    | Username   | Password   |
|---------|------------|------------|
| Teacher | `teacher`  | `teacher123` |
| Student | `student01` | `student123` |

Admin panel: `/admin/` (create a superuser: `python manage.py createsuperuser`).

## Features

- **Sign In / Sign Up**: choose Teacher or Student on a single page; register a new account or sign in.
- **Teacher login**: dashboard, mark attendance (present/absent/late per class per date), history with filters, reports with attendance %, manage students & classes.
- **Student login**: personal dashboard and attendance history with percentage.