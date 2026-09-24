from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AttendanceRecord, ClassRoom, User


@admin.register(User)
class SchoolUserAdmin(UserAdmin):
    list_display = ('username', 'full_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('School Info', {'fields': ('role', 'full_name')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('School Info', {'fields': ('role', 'full_name')}),
    )


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'student_count')
    filter_horizontal = ('students',)

    @admin.display(description='Students')
    def student_count(self, obj):
        return obj.students.count()


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'classroom', 'date', 'status', 'marked_by')
    list_filter = ('status', 'date', 'classroom')
    search_fields = ('student__username', 'student__full_name')
