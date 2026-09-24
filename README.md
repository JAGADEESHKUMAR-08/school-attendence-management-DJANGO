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

## Viewing the database

The project uses SQLite: `db.sqlite3` in the project root. It is excluded from
git (see `.gitignore`); recreate it with `migrate` + `seed_data`.

### Django admin (browser)

1. Create an admin account (once):
   ```bash
   python manage.py createsuperuser
   ```
2. Start the server and open http://127.0.0.1:8000/admin/
3. Browse **Users** (filter by role), **Classrooms** (assign students), and
   **Attendance records** (filter by status/date/class, search by student).

### DB Browser for SQLite (desktop GUI)

1. Install from https://sqlitebrowser.org/dl/
2. **Open Database** → select `db.sqlite3`.
3. Use **Browse Data** to page through `attendance_user`,
   `attendance_classroom`, `attendance_classroom_students`, and
   `attendance_attendancerecord`.
4. **Execute SQL** example:
   ```sql
   SELECT a.date, u.full_name, cl.name, a.status
   FROM attendance_attendancerecord a
   JOIN attendance_user u ON u.id = a.student_id
   JOIN attendance_classroom cl ON cl.id = a.classroom_id
   ORDER BY a.date DESC;
   ```
5. Stop `runserver` before editing/saving data (SQLite file lock). Don't edit
   `password` columns by hand — use the admin.

## Features

- **Sign In / Sign Up**: choose Teacher or Student on a single page; register a new account or sign in.
- **Teacher login**: dashboard, mark attendance (present/absent/late per class per date), history with filters, reports with attendance %, manage students & classes.
- **Student login**: personal dashboard and attendance history with percentage.