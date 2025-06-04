from django.urls import path
from . import views
from django.views.generic import RedirectView

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.user_register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('mark-attendance/', views.mark_attendance, name='mark_attendance'),
    path('mark-subject-attendance/', views.mark_subject_attendance, name='mark_subject_attendance'),
    path('history/', views.attendance_history, name='attendance_history'),
    path('subject-history/', views.subject_attendance_history, name='subject_attendance_history'),
    path('export-subject-attendance/', views.export_subject_attendance, name='export_subject_attendance'),
    path('analytics/', views.subject_analytics, name='subject_analytics'),
    path('admin-view/', views.admin_attendance_view, name='admin_attendance_view'),
    path('admin-subject-view/', views.admin_subject_attendance, name='admin_subject_attendance'),
    path('edit-attendance/<int:attendance_id>/', views.edit_attendance, name='edit_attendance'),
    path('edit-subject-attendance/<int:attendance_id>/', views.edit_subject_attendance, name='edit_subject_attendance'),
    path('create-attendance/<int:user_id>/', views.create_attendance, name='create_attendance'),
]
