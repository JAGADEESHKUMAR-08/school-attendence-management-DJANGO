from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        TEACHER = 'TEACHER', 'Teacher'
        STUDENT = 'STUDENT', 'Student'

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    full_name = models.CharField(max_length=150, blank=True)

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    def __str__(self):
        return self.full_name or self.username


class ClassRoom(models.Model):
    name = models.CharField(max_length=100, unique=True)
    teacher = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='taught_classes'
    )
    students = models.ManyToManyField(User, related_name='classrooms', blank=True)

    class Meta:
        verbose_name_plural = 'classrooms'
        ordering = ['name']

    def __str__(self):
        return self.name


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'PRESENT', 'Present'
        ABSENT = 'ABSENT', 'Absent'
        LATE = 'LATE', 'Late'

    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='attendance_records'
    )
    classroom = models.ForeignKey(
        ClassRoom, on_delete=models.CASCADE, related_name='attendance_records'
    )
    date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=10, choices=Status.choices)
    marked_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='marked_records'
    )
    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', 'student__full_name']
        unique_together = ('student', 'classroom', 'date')

    def __str__(self):
        return f'{self.student} - {self.date} - {self.get_status_display()}'
