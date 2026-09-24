from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import AttendanceRecord, ClassRoom, User


class AttendanceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = User.objects.create_user(
            username='t1', password='pass1234', role=User.Role.TEACHER, full_name='Teacher One'
        )
        cls.student = User.objects.create_user(
            username='s1', password='pass1234', role=User.Role.STUDENT, full_name='Student One'
        )
        cls.student2 = User.objects.create_user(
            username='s2', password='pass1234', role=User.Role.STUDENT, full_name='Student Two'
        )
        cls.classroom = ClassRoom.objects.create(name='Grade 1A', teacher=cls.teacher)
        cls.classroom.students.set([cls.student, cls.student2])

    def test_login_redirects_to_dashboard(self):
        self.client.login(username='t1', password='pass1234')
        response = self.client.get(reverse('login'))
        self.assertRedirects(response, reverse('dashboard'))

    def test_student_cannot_open_mark_page(self):
        self.client.login(username='s1', password='pass1234')
        response = self.client.get(reverse('mark_attendance'))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_mark_attendance_saves_records(self):
        self.client.login(username='t1', password='pass1234')
        today = timezone.localdate()
        post_data = {
            'classroom': self.classroom.pk,
            'date': today.isoformat(),
            f'status_{self.student.pk}': 'PRESENT',
            f'status_{self.student2.pk}': 'ABSENT',
        }
        response = self.client.post(
            reverse('mark_attendance') + f'?classroom={self.classroom.pk}&date={today.isoformat()}',
            post_data,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            AttendanceRecord.objects.get(student=self.student).status, 'PRESENT'
        )
        self.assertEqual(
            AttendanceRecord.objects.get(student=self.student2).status, 'ABSENT'
        )

    def test_student_sees_own_percentage(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        AttendanceRecord.objects.create(
            student=self.student,
            classroom=self.classroom,
            date=yesterday,
            status='PRESENT',
            marked_by=self.teacher,
        )
        self.client.login(username='s1', password='pass1234')
        response = self.client.get(reverse('my_attendance'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '100.0%')

    def test_register_page_loads(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign Up')

    def test_register_creates_account_and_logs_in(self):
        response = self.client.post(reverse('register'), {
            'role': 'STUDENT',
            'username': 'newkid',
            'full_name': 'New Kid',
            'email': 'new@example.com',
            'password1': 'strongpass123',
            'password2': 'strongpass123',
        })
        self.assertRedirects(response, reverse('dashboard'))
        user = User.objects.get(username='newkid')
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertTrue(user.check_password('strongpass123'))

    def test_login_rejects_wrong_role(self):
        response = self.client.post(reverse('login'), {
            'role': 'STUDENT',
            'username': 't1',
            'password': 'pass1234',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'registered as a Teacher')

    def test_unique_attendance_per_day(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        AttendanceRecord.objects.create(
            student=self.student, classroom=self.classroom, date=yesterday, status='PRESENT'
        )
        with self.assertRaises(Exception):
            AttendanceRecord.objects.create(
                student=self.student, classroom=self.classroom, date=yesterday, status='ABSENT'
            )