from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('mark/', views.mark_attendance, name='mark_attendance'),
    path('history/', views.history, name='history'),
    path('reports/', views.reports, name='reports'),
    path('students/', views.manage_students, name='students'),
    path('students/<int:student_id>/delete/', views.student_delete, name='student_delete'),
    path('classes/', views.manage_classes, name='classes'),
    path('classes/<int:class_id>/edit/', views.class_edit, name='class_edit'),
    path('classes/<int:class_id>/delete/', views.class_delete, name='class_delete'),
    path('my-attendance/', views.my_attendance, name='my_attendance'),
]
