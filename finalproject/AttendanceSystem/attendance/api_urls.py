from django.urls import path
from . import api

urlpatterns = [
    # Authentication endpoints
    path('register/', api.api_register, name='api_register'),
    path('login/', api.api_login, name='api_login'),
    path('profile/', api.api_get_user_profile, name='api_get_user_profile'),
    
    # Dashboard and data endpoints
    path('dashboard/', api.api_get_dashboard_data, name='api_get_dashboard_data'),
    path('subjects/', api.api_list_subjects, name='api_list_subjects'),
    path('periods/', api.api_list_class_periods, name='api_list_class_periods'),
    
    # Attendance management endpoints
    path('mark-attendance/', api.api_mark_attendance, name='api_mark_attendance'),
    path('mark-subject-attendance/', api.api_mark_subject_attendance, name='api_mark_subject_attendance'),
    path('attendance-history/', api.api_attendance_history, name='api_attendance_history'),
    path('subject-attendance-history/', api.api_subject_attendance_history, name='api_subject_attendance_history'),
] 