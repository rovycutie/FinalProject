from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Attendance, Subject, SubjectAttendance, ClassPeriod
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden, HttpResponse
from datetime import datetime, timedelta
from django.urls import reverse
import csv
import json
from django.db.models import Count

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        return redirect('login')

def user_register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validation checks
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, 'attendance/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return render(request, 'attendance/register.html')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already in use")
            return render(request, 'attendance/register.html')
            
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        messages.success(request, "Account created successfully. Please login.")
        return redirect('login')
        
    return render(request, 'attendance/register.html')

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            print("User authenticated successfully, redirecting to dashboard")
            # First try direct URL, then fall back to reverse lookup
            try:
                return redirect(reverse('dashboard'))
            except Exception as e:
                print(f"Error in reverse lookup: {e}")
                return redirect('/dashboard/')
        else:
            messages.error(request, "Invalid username or password")
            print("Authentication failed for user:", username)

    return render(request, 'attendance/login.html')

def user_logout(request):
    logout(request)
    return redirect('login')

# @login_required(login_url='login')
def dashboard(request):
    # Check if user is authenticated manually
    if not request.user.is_authenticated:
        print("User not authenticated, redirecting to login page")
        return redirect('login')
    
    print("Dashboard view accessed by user:", request.user.username)
    today = timezone.now().date()
    today_attendance = Attendance.objects.filter(user=request.user, date=today).first()
    
    # Get all subjects for the dropdown
    subjects = Subject.objects.all()
    
    # Get subject attendance for today
    subject_attendances = SubjectAttendance.objects.filter(
        user=request.user, 
        date=today
    ).select_related('subject', 'period').order_by('created_at')
    
    # Get class periods
    periods = ClassPeriod.objects.all().select_related('subject')
    
    # Prepare subject statistics
    subject_stats = []
    for subject in subjects:
        stats = subject.get_attendance_stats(user=request.user)
        subject_stats.append({
            'subject': subject,
            'stats': stats
        })
    
    context = {
        'today_attendance': today_attendance,
        'today': today,
        'subjects': subjects,
        'subject_attendances': subject_attendances,
        'periods': periods,
        'subject_stats': subject_stats
    }
    
    print("Rendering dashboard with context:", context)
    return render(request, 'attendance/dashboard.html', context)

@login_required(login_url='login')
def mark_attendance(request):
    """Function to mark attendance for a user"""
    today = timezone.now().date()
    current_time = timezone.now().time()
    
    # Check if attendance already exists for today
    attendance, created = Attendance.objects.get_or_create(
        user=request.user,
        date=today,
        defaults={
            'time_in': current_time,
            'status': 'present'
        }
    )
    
    if not created:
        # If already marked time_in, now mark time_out
        if not attendance.time_out:
            attendance.time_out = current_time
            attendance.save()
            messages.success(request, "Time out marked successfully")
        else:
            messages.info(request, "Attendance already marked for today")
    else:
        messages.success(request, "Time in marked successfully")
    
    return redirect('dashboard')

@login_required(login_url='login')
def mark_subject_attendance(request):
    """Function to mark attendance for a specific subject"""
    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        period_id = request.POST.get('period')
        status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        today = timezone.now().date()
        
        try:
            subject = Subject.objects.get(id=subject_id)
            period = None
            if period_id:
                period = ClassPeriod.objects.get(id=period_id)
            
            # Create or update subject attendance
            subject_attendance, created = SubjectAttendance.objects.get_or_create(
                user=request.user,
                subject=subject,
                date=today,
                period=period,
                defaults={
                    'status': status,
                    'created_at': timezone.now(),
                    'notes': notes
                }
            )
            
            if not created:
                # Update existing attendance
                subject_attendance.status = status
                subject_attendance.created_at = timezone.now()
                subject_attendance.notes = notes
                subject_attendance.save()
                messages.success(request, f"Attendance updated for {subject.name}")
            else:
                messages.success(request, f"Attendance recorded for {subject.name}")
                
        except Subject.DoesNotExist:
            messages.error(request, "Subject not found")
        except ClassPeriod.DoesNotExist:
            messages.error(request, "Class period not found")
    
    return redirect('dashboard')

@login_required(login_url='login')
def attendance_history(request):
    """View attendance history for the logged-in user"""
    attendance_records = Attendance.objects.filter(user=request.user).order_by('-date')
    return render(request, 'attendance/history.html', {'attendance_records': attendance_records})

@login_required(login_url='login')
def subject_attendance_history(request):
    """View subject attendance history for the logged-in user"""
    subject_filter = request.GET.get('subject', None)
    date_from = request.GET.get('date_from', None)
    date_to = request.GET.get('date_to', None)
    
    attendance_records = SubjectAttendance.objects.filter(user=request.user)
    
    # Apply filters
    if subject_filter:
        attendance_records = attendance_records.filter(subject_id=subject_filter)
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            attendance_records = attendance_records.filter(date__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            attendance_records = attendance_records.filter(date__lte=date_to)
        except ValueError:
            pass
    
    attendance_records = attendance_records.select_related('subject', 'period').order_by('-date')
    
    subjects = Subject.objects.all()
    
    # Calculate attendance statistics
    stats = {}
    for subject in subjects:
        stats[subject.id] = subject.get_attendance_stats(user=request.user)
    
    context = {
        'attendance_records': attendance_records,
        'subjects': subjects,
        'selected_subject': subject_filter,
        'date_from': date_from,
        'date_to': date_to,
        'stats': stats,
    }
    
    return render(request, 'attendance/subject_history.html', context)

@login_required(login_url='login')
def export_subject_attendance(request):
    """Export subject attendance data to CSV"""
    subject_filter = request.GET.get('subject', None)
    date_from = request.GET.get('date_from', None)
    date_to = request.GET.get('date_to', None)
    
    attendance_records = SubjectAttendance.objects.filter(user=request.user)
    
    # Apply filters
    if subject_filter:
        attendance_records = attendance_records.filter(subject_id=subject_filter)
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            attendance_records = attendance_records.filter(date__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            attendance_records = attendance_records.filter(date__lte=date_to)
        except ValueError:
            pass
    
    attendance_records = attendance_records.select_related('subject', 'period').order_by('-date')
    
    # Create HTTP response with CSV content
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Subject', 'Period', 'Status', 'Time', 'Notes'])
    
    for record in attendance_records:
        period_name = record.period.name if record.period else 'N/A'
        writer.writerow([
            record.date,
            record.subject.name,
            period_name,
            record.status,
            record.created_at.strftime('%H:%M:%S'),
            record.notes or ''
        ])
    
    return response

@login_required(login_url='login')
def subject_analytics(request):
    """View analytics for subject attendance"""
    user = request.user
    subjects = Subject.objects.all()
    
    # Get date range (default: last 30 days)
    date_from = request.GET.get('date_from', None)
    date_to = request.GET.get('date_to', None)
    
    if not date_from:
        date_from = (timezone.now().date() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    if not date_to:
        date_to = timezone.now().date().strftime('%Y-%m-%d')
    
    try:
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
    except ValueError:
        date_from_obj = timezone.now().date() - timedelta(days=30)
        date_to_obj = timezone.now().date()
    
    # Prepare statistics for each subject
    subject_stats = []
    for subject in subjects:
        records = SubjectAttendance.objects.filter(
            user=user,
            subject=subject,
            date__gte=date_from_obj,
            date__lte=date_to_obj
        )
        
        total = records.count()
        present = records.filter(status='present').count()
        absent = records.filter(status='absent').count()
        late = records.filter(status='late').count()
        
        if total > 0:
            present_rate = (present / total) * 100
            absent_rate = (absent / total) * 100
            late_rate = (late / total) * 100
        else:
            present_rate = absent_rate = late_rate = 0
            
        subject_stats.append({
            'subject': subject,
            'total': total,
            'present': present,
            'absent': absent,
            'late': late,
            'present_rate': present_rate,
            'absent_rate': absent_rate,
            'late_rate': late_rate
        })
    
    context = {
        'subject_stats': subject_stats,
        'date_from': date_from,
        'date_to': date_to
    }
    
    return render(request, 'attendance/analytics.html', context)

@login_required(login_url='login')
def admin_attendance_view(request):
    """Admin view to see all users' attendance (restricted to staff)"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page")
        return redirect('dashboard')
        
    date_filter = request.GET.get('date', timezone.now().date().strftime('%Y-%m-%d'))
    users = User.objects.filter(is_staff=False)
    attendance_records = Attendance.objects.filter(date=date_filter)
    
    context = {
        'users': users,
        'attendance_records': attendance_records,
        'selected_date': date_filter,
    }
    return render(request, 'attendance/admin_view.html', context)

@login_required(login_url='login')
def admin_subject_attendance(request):
    """Admin view for subject attendance (restricted to staff)"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page")
        return redirect('dashboard')
    
    date_filter = request.GET.get('date', timezone.now().date().strftime('%Y-%m-%d'))
    subject_filter = request.GET.get('subject', None)
    
    # Get all non-staff users
    users = User.objects.filter(is_staff=False)
    
    # Get subjects
    subjects = Subject.objects.all()
    
    # Filter attendance records
    attendance_query = SubjectAttendance.objects.all()
    
    if date_filter:
        try:
            date_obj = datetime.strptime(date_filter, '%Y-%m-%d').date()
            attendance_query = attendance_query.filter(date=date_obj)
        except ValueError:
            pass
    
    if subject_filter:
        attendance_query = attendance_query.filter(subject_id=subject_filter)
    
    attendance_records = attendance_query.select_related('user', 'subject', 'period')
    
    context = {
        'users': users,
        'subjects': subjects,
        'attendance_records': attendance_records,
        'selected_date': date_filter,
        'selected_subject': subject_filter
    }
    
    return render(request, 'attendance/admin_subject_view.html', context)

@login_required(login_url='login')
def edit_attendance(request, attendance_id):
    """Admin function to edit an attendance record"""
    if not request.user.is_staff:
        return HttpResponseForbidden("You don't have permission to access this page")
    
    attendance = get_object_or_404(Attendance, id=attendance_id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        time_in_str = request.POST.get('time_in')
        time_out_str = request.POST.get('time_out')
        
        attendance.status = status
        
        if time_in_str:
            time_in = datetime.strptime(time_in_str, '%H:%M').time()
            attendance.time_in = time_in
        
        if time_out_str:
            time_out = datetime.strptime(time_out_str, '%H:%M').time()
            attendance.time_out = time_out
        else:
            attendance.time_out = None
            
        attendance.save()
        messages.success(request, "Attendance record updated successfully")
        return redirect('admin_attendance_view')
    
    context = {
        'attendance': attendance,
    }
    return render(request, 'attendance/edit_attendance.html', context)

@login_required(login_url='login')
def edit_subject_attendance(request, attendance_id):
    """Admin function to edit a subject attendance record"""
    if not request.user.is_staff:
        return HttpResponseForbidden("You don't have permission to access this page")
    
    attendance = get_object_or_404(SubjectAttendance, id=attendance_id)
    periods = ClassPeriod.objects.filter(subject=attendance.subject)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        period_id = request.POST.get('period')
        notes = request.POST.get('notes')
        
        attendance.status = status
        attendance.notes = notes
        
        if period_id:
            try:
                period = ClassPeriod.objects.get(id=period_id)
                attendance.period = period
            except ClassPeriod.DoesNotExist:
                pass
        else:
            attendance.period = None
            
        attendance.save()
        messages.success(request, "Subject attendance record updated successfully")
        return redirect('admin_subject_attendance')
    
    context = {
        'attendance': attendance,
        'periods': periods
    }
    return render(request, 'attendance/edit_subject_attendance.html', context)

@login_required(login_url='login')
def create_attendance(request, user_id):
    """Admin function to create an attendance record for a user"""
    if not request.user.is_staff:
        return HttpResponseForbidden("You don't have permission to access this page")
        
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        date_str = request.POST.get('date')
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date = timezone.now().date()
            
        # Create a new attendance record
        attendance = Attendance(
            user=user,
            date=date,
            time_in=timezone.now().time(),
            status='present'
        )
        attendance.save()
        
        messages.success(request, f"Attendance record created for {user.username}")
        return redirect('admin_attendance_view')
        
    # If not POST, redirect back to admin view
    return redirect('admin_attendance_view')
