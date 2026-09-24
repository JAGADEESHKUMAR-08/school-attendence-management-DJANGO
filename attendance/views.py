from datetime import datetime, timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie

from .decorators import role_required
from .forms import ClassRoomForm, LoginForm, RegisterForm, StudentForm
from .models import AttendanceRecord, ClassRoom, User

PRESENT = AttendanceRecord.Status.PRESENT
ABSENT = AttendanceRecord.Status.ABSENT
LATE = AttendanceRecord.Status.LATE
ALL_STATUSES = (PRESENT, ABSENT, LATE)


def _parse_date(value, default=None):
    default = default or timezone.localdate()
    if not value:
        return default
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return default


# ---------------------------------------------------------------- auth

@never_cache
@ensure_csrf_cookie
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password'],
        )
        if user is None:
            form.add_error(None, 'Invalid username or password.')
        elif user.role != form.cleaned_data['role']:
            form.add_error(
                None,
                f'This account is registered as a {user.get_role_display()}. '
                'Please select the correct option above.',
            )
        else:
            login(request, user)
            return redirect('dashboard')
    return render(request, 'login.html', {'form': form})


@never_cache
@ensure_csrf_cookie
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f'Welcome, {user}! Your account has been created.')
        return redirect('dashboard')
    return render(request, 'register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


def csrf_failure(request, reason=''):
    """Self-heal a stale/foreign CSRF cookie and send the user back to sign in."""
    response = redirect('login')
    response.delete_cookie(settings.CSRF_COOKIE_NAME)
    messages.warning(request, 'Your sign-in session expired. Please sign in again.')
    return response


# ---------------------------------------------------------------- dashboards

@login_required
def dashboard(request):
    if request.user.is_teacher:
        return render(request, 'dashboard.html', _teacher_dashboard_context(request))
    return render(request, 'student_dashboard.html', _student_dashboard_context(request))


def _teacher_dashboard_context(request):
    today = timezone.localdate()
    today_records = AttendanceRecord.objects.filter(date=today)
    today_counts = {
        status: today_records.filter(status=status).count() for status in ALL_STATUSES
    }
    today_counts['marked'] = today_records.count()

    class_rows = []
    for classroom in ClassRoom.objects.all():
        class_today = classroom.attendance_records.filter(date=today)
        class_rows.append({
            'classroom': classroom,
            'students': classroom.students.count(),
            'present': class_today.filter(status=PRESENT).count(),
            'absent': class_today.filter(status=ABSENT).count(),
            'late': class_today.filter(status=LATE).count(),
            'marked': class_today.count(),
        })

    recent = AttendanceRecord.objects.select_related('student', 'classroom')[:10]
    return {
        'today': today,
        'total_students': User.objects.filter(role=User.Role.STUDENT).count(),
        'total_classes': ClassRoom.objects.count(),
        'today_counts': today_counts,
        'class_rows': class_rows,
        'recent': recent,
    }


def _student_dashboard_context(request):
    today = timezone.localdate()
    records = AttendanceRecord.objects.filter(student=request.user)
    today_record = records.filter(date=today).first()
    total = records.count()
    attended = records.filter(status__in=[PRESENT, LATE]).count()
    return {
        'today': today,
        'today_record': today_record,
        'total': total,
        'attended': attended,
        'percentage': round(100 * attended / total, 1) if total else 0,
        'recent': records.select_related('classroom')[:5],
    }


# ---------------------------------------------------------------- teacher: mark

@role_required(User.Role.TEACHER)
def mark_attendance(request):
    classrooms = ClassRoom.objects.all()
    if not classrooms.exists():
        messages.info(request, 'Create a classroom before marking attendance.')
        return redirect('classes')

    classroom_id = request.POST.get('classroom') or request.GET.get('classroom')
    date_str = request.POST.get('date') or request.GET.get('date')
    classroom = get_object_or_404(ClassRoom, pk=classroom_id) if classroom_id else classrooms.first()
    selected_date = _parse_date(date_str)

    students = list(classroom.students.all().order_by('full_name', 'username'))
    existing = {
        record.student_id: record.status
        for record in AttendanceRecord.objects.filter(classroom=classroom, date=selected_date)
    }

    if request.method == 'POST':
        if not students:
            messages.warning(request, f'{classroom.name} has no students enrolled.')
            return redirect('classes')
        saved = 0
        for student in students:
            status = request.POST.get(f'status_{student.pk}')
            if status in ALL_STATUSES:
                AttendanceRecord.objects.update_or_create(
                    student=student,
                    classroom=classroom,
                    date=selected_date,
                    defaults={'status': status, 'marked_by': request.user},
                )
                saved += 1
        messages.success(request, f'Saved {saved} record(s) for {classroom.name} on {selected_date}.')
        query = urlencode({'classroom': classroom.pk, 'date': selected_date.isoformat()})
        return redirect(f"{reverse('mark_attendance')}?{query}")

    rows = [{'student': student, 'status': existing.get(student.pk)} for student in students]
    return render(request, 'mark_attendance.html', {
        'classrooms': classrooms,
        'classroom': classroom,
        'selected_date': selected_date,
        'today': timezone.localdate(),
        'rows': rows,
        'statuses': AttendanceRecord.Status.choices,
    })


# ---------------------------------------------------------------- teacher: history

@role_required(User.Role.TEACHER)
def history(request):
    today = timezone.localdate()
    start = _parse_date(request.GET.get('start'), today - timedelta(days=30))
    end = _parse_date(request.GET.get('end'), today)
    classroom_id = request.GET.get('classroom')

    records = AttendanceRecord.objects.select_related('student', 'classroom', 'marked_by')
    if classroom_id:
        records = records.filter(classroom_id=classroom_id)
    if start > end:
        start, end = end, start
    records = records.filter(date__range=(start, end))[:500]

    params = request.GET.copy()
    params.pop('page', None)
    return render(request, 'history.html', {
        'records': records,
        'classrooms': ClassRoom.objects.all(),
        'selected_classroom': classroom_id,
        'start': start.isoformat(),
        'end': end.isoformat(),
        'query_string': params.urlencode(),
    })


# ---------------------------------------------------------------- teacher: reports

@role_required(User.Role.TEACHER)
def reports(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)
    start = _parse_date(request.GET.get('start'), month_start)
    end = _parse_date(request.GET.get('end'), today)
    classroom_id = request.GET.get('classroom')
    if start > end:
        start, end = end, start

    records = AttendanceRecord.objects.filter(date__range=(start, end))
    if classroom_id:
        records = records.filter(classroom_id=classroom_id)

    rows = list(records.values(
        'classroom_id', 'classroom__name',
        'student_id', 'student__full_name', 'student__username',
    ).annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status=PRESENT)),
        absent=Count('id', filter=Q(status=ABSENT)),
        late=Count('id', filter=Q(status=LATE)),
    ).order_by('classroom__name', 'student__full_name', 'student__username'))

    for row in rows:
        attended = row['present'] + row['late']
        row['percentage'] = round(100 * attended / row['total'], 1) if row['total'] else 0.0

    totals = {
        'total': sum(r['total'] for r in rows),
        'present': sum(r['present'] for r in rows),
        'absent': sum(r['absent'] for r in rows),
        'late': sum(r['late'] for r in rows),
    }
    totals['percentage'] = (
        round(100 * (totals['present'] + totals['late']) / totals['total'], 1)
        if totals['total'] else 0.0
    )

    return render(request, 'reports.html', {
        'rows': rows,
        'totals': totals,
        'classrooms': ClassRoom.objects.all(),
        'selected_classroom': classroom_id,
        'start': start.isoformat(),
        'end': end.isoformat(),
    })


# ---------------------------------------------------------------- teacher: manage students

@role_required(User.Role.TEACHER)
def manage_students(request):
    form = StudentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Student {form.cleaned_data["username"]} created.')
        return redirect('students')
    students = User.objects.filter(role=User.Role.STUDENT).prefetch_related('classrooms')
    return render(request, 'students.html', {'form': form, 'students': students})


@role_required(User.Role.TEACHER)
def student_delete(request, student_id):
    student = get_object_or_404(User, pk=student_id, role=User.Role.STUDENT)
    if request.method == 'POST':
        student.delete()
        messages.success(request, f'Student {student} deleted.')
    return redirect('students')


# ---------------------------------------------------------------- teacher: manage classes

@role_required(User.Role.TEACHER)
def manage_classes(request):
    form = ClassRoomForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        classroom = form.save()
        classroom.students.set(form.cleaned_data['students'])
        messages.success(request, f'Classroom {classroom.name} created.')
        return redirect('classes')
    classrooms = ClassRoom.objects.select_related('teacher').prefetch_related('students')
    return render(request, 'classes.html', {'form': form, 'classrooms': classrooms})


@role_required(User.Role.TEACHER)
def class_edit(request, class_id):
    classroom = get_object_or_404(ClassRoom, pk=class_id)
    form = ClassRoomForm(request.POST or None, instance=classroom)
    if request.method == 'POST' and form.is_valid():
        classroom = form.save()
        classroom.students.set(form.cleaned_data['students'])
        messages.success(request, f'Classroom {classroom.name} updated.')
        return redirect('classes')
    return render(request, 'class_edit.html', {'form': form, 'classroom': classroom})


@role_required(User.Role.TEACHER)
def class_delete(request, class_id):
    classroom = get_object_or_404(ClassRoom, pk=class_id)
    if request.method == 'POST':
        classroom.delete()
        messages.success(request, f'Classroom {classroom.name} deleted.')
    return redirect('classes')


# ---------------------------------------------------------------- student

@role_required(User.Role.STUDENT)
def my_attendance(request):
    records = AttendanceRecord.objects.filter(student=request.user).select_related('classroom')
    total = records.count()
    present = records.filter(status=PRESENT).count()
    absent = records.filter(status=ABSENT).count()
    late = records.filter(status=LATE).count()
    attended = present + late
    return render(request, 'my_attendance.html', {
        'records': records[:500],
        'total': total,
        'present': present,
        'absent': absent,
        'late': late,
        'percentage': round(100 * attended / total, 1) if total else 0,
    })
