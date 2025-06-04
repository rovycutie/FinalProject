from django.contrib import admin
from .models import Attendance

# Register your models here.
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'time_in', 'time_out', 'status')
    list_filter = ('date', 'status')
    search_fields = ('user__username',)
    date_hierarchy = 'date'
