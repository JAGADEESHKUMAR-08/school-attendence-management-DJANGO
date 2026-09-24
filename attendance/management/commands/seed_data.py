import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from attendance.models import AttendanceRecord, ClassRoom, User

TEACHER_USERNAME = 'teacher'
TEACHER_PASSWORD = 'teacher123'
STUDENT_PASSWORD = 'student123'


class Command(BaseCommand):
    help = 'Seed demo data: teacher, students, classrooms and random attendance.'

    def handle(self, *args, **options):
        if User.objects.filter(username=TEACHER_USERNAME).exists():
            self.stdout.write('Demo data already exists. Skip (run: flush).')
            return

        teacher = User.objects.create_user(
            username=TEACHER_USERNAME,
            password=TEACHER_PASSWORD,
            role=User.Role.TEACHER,
            full_name='Alice Johnson',
            is_staff=True,
        )
        self.stdout.write(f'Teacher created: {TEACHER_USERNAME} / {TEACHER_PASSWORD}')

        names = [
            'Emma Watson', 'Liam Smith', 'Olivia Brown', 'Noah Davis',
            'Ava Miller', 'Ethan Wilson', 'Sophia Moore', 'Mason Taylor',
            'Isabella Anderson', 'James Thomas',
        ]
        students = []
        for index, full_name in enumerate(names, start=1):
            username = f'student{index:02d}'
            student = User.objects.create_user(
                username=username,
                password=STUDENT_PASSWORD,
                role=User.Role.STUDENT,
                full_name=full_name,
            )
            students.append(student)
        self.stdout.write(f'Created {len(students)} students (password: {STUDENT_PASSWORD})')

        grade_10a = ClassRoom.objects.create(name='Grade 10A', teacher=teacher)
        grade_10b = ClassRoom.objects.create(name='Grade 10B', teacher=teacher)
        grade_10a.students.set(students[:5])
        grade_10b.students.set(students[5:])
        self.stdout.write('Created Grade 10A and Grade 10B.')

        today = timezone.localdate()
        created = 0
        for offset_days in range(14, 0, -1):
            day = today - timedelta(days=offset_days)
            if day.weekday() >= 5:
                continue
            for classroom in (grade_10a, grade_10b):
                for student in classroom.students.all():
                    status = random.choices(
                        [AttendanceRecord.Status.PRESENT,
                         AttendanceRecord.Status.ABSENT,
                         AttendanceRecord.Status.LATE],
                        weights=[78, 15, 7],
                    )[0]
                    AttendanceRecord.objects.create(
                        student=student,
                        classroom=classroom,
                        date=day,
                        status=status,
                        marked_by=teacher,
                    )
                    created += 1
        self.stdout.write(self.style.SUCCESS(
            f'Done. {created} attendance records over the last 2 school weeks.'
        ))