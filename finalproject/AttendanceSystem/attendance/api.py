from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Attendance, Subject, SubjectAttendance, ClassPeriod
from datetime import datetime


@api_view(['POST'])
@permission_classes([AllowAny])
def api_register(request):
    """API endpoint for user registration"""
    username = request.data.get('username')
    email = request.data.get('email')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')
    password = request.data.get('password')
    confirm_password = request.data.get('confirm_password')
    
    # Validation
    if not all([username, email, password, confirm_password]):
        return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
    
    if password != confirm_password:
        return Response({"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
    if User.objects.filter(email=email).exists():
        return Response({"error": "Email already in use"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Create user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name
    )
    
    # Create token
    token, created = Token.objects.get_or_create(user=user)
    
    return Response({
        "message": "Account created successfully",
        "token": token.key,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """API endpoint for user login"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not all([username, password]):
        return Response({"error": "Missing username or password"}, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(username=username, password=password)
    
    if user is not None:
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            "message": "Login successful",
            "token": token.key,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        })
    else:
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_get_user_profile(request):
    """Get user profile information"""
    user = request.user
    return Response({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_get_dashboard_data(request):
    """Get dashboard data for the authenticated user"""
    user = request.user
    today = timezone.now().date()
    
    # Get today's attendance
    today_attendance = Attendance.objects.filter(user=user, date=today).first()
    
    # Get all subjects
    subjects = Subject.objects.all()
    subject_list = []
    
    for subject in subjects:
        stats = subject.get_attendance_stats(user=user)
        subject_list.append({
            'id': subject.id,
            'name': subject.name,
            'code': subject.code,
            'description': subject.description,
            'stats': stats
        })
    
    # Get subject attendance for today
    subject_attendances = SubjectAttendance.objects.filter(
        user=user, 
        date=today
    ).select_related('subject', 'period')
    
    subject_attendance_list = []
    for att in subject_attendances:
        subject_attendance_list.append({
            'id': att.id,
            'subject_id': att.subject.id,
            'subject_name': att.subject.name,
            'period_id': att.period.id if att.period else None,
            'period_name': att.period.name if att.period else None,
            'status': att.status,
            'date': att.date,
            'created_at': att.created_at,
            'notes': att.notes
        })
    
    attendance_data = None
    if today_attendance:
        attendance_data = {
            'id': today_attendance.id,
            'date': today_attendance.date,
            'time_in': today_attendance.time_in,
            'time_out': today_attendance.time_out,
            'status': today_attendance.status
        }
    
    return Response({
        'today': today,
        'attendance': attendance_data,
        'subjects': subject_list,
        'subject_attendances': subject_attendance_list
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_mark_attendance(request):
    """Mark attendance for the authenticated user"""
    user = request.user
    today = timezone.now().date()
    current_time = timezone.now().time()
    
    # Check if attendance already exists for today
    attendance, created = Attendance.objects.get_or_create(
        user=user,
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
            return Response({"message": "Time out marked successfully"})
        else:
            return Response({"message": "Attendance already marked for today"})
    else:
        return Response({"message": "Time in marked successfully"})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_mark_subject_attendance(request):
    """Mark subject attendance for the authenticated user"""
    user = request.user
    subject_id = request.data.get('subject_id')
    period_id = request.data.get('period_id')
    status = request.data.get('status')
    notes = request.data.get('notes', '')
    
    if not all([subject_id, status]):
        return Response({"error": "Subject ID and status are required"}, status=status.HTTP_400_BAD_REQUEST)
    
    if status not in ['present', 'absent', 'late']:
        return Response({"error": "Invalid status. Must be 'present', 'absent', or 'late'"}, status=status.HTTP_400_BAD_REQUEST)
    
    today = timezone.now().date()
    
    try:
        subject = Subject.objects.get(id=subject_id)
        period = None
        if period_id:
            period = ClassPeriod.objects.get(id=period_id)
        
        # Create or update subject attendance
        subject_attendance, created = SubjectAttendance.objects.get_or_create(
            user=user,
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
            
        return Response({
            "message": f"Attendance {'recorded' if created else 'updated'} for {subject.name}",
            "attendance_id": subject_attendance.id,
            "created": created
        })
            
    except Subject.DoesNotExist:
        return Response({"error": "Subject not found"}, status=status.HTTP_404_NOT_FOUND)
    except ClassPeriod.DoesNotExist:
        return Response({"error": "Class period not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_attendance_history(request):
    """Get attendance history for the authenticated user"""
    user = request.user
    attendance_records = Attendance.objects.filter(user=user).order_by('-date')
    
    history = []
    for record in attendance_records:
        history.append({
            'id': record.id,
            'date': record.date,
            'time_in': record.time_in,
            'time_out': record.time_out,
            'status': record.status
        })
    
    return Response(history)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_subject_attendance_history(request):
    """Get subject attendance history for the authenticated user"""
    user = request.user
    subject_id = request.query_params.get('subject_id')
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    
    attendance_records = SubjectAttendance.objects.filter(user=user)
    
    # Apply filters
    if subject_id:
        attendance_records = attendance_records.filter(subject_id=subject_id)
    
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
    
    history = []
    for record in attendance_records:
        history.append({
            'id': record.id,
            'subject': {
                'id': record.subject.id,
                'name': record.subject.name,
                'code': record.subject.code
            },
            'period': {
                'id': record.period.id,
                'name': record.period.name
            } if record.period else None,
            'date': record.date,
            'status': record.status,
            'created_at': record.created_at,
            'notes': record.notes
        })
    
    return Response(history)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_list_subjects(request):
    """Get list of all subjects"""
    subjects = Subject.objects.all()
    
    subject_list = []
    for subject in subjects:
        subject_list.append({
            'id': subject.id,
            'name': subject.name,
            'code': subject.code,
            'description': subject.description
        })
    
    return Response(subject_list)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_list_class_periods(request):
    """Get list of all class periods"""
    periods = ClassPeriod.objects.all().select_related('subject')
    
    period_list = []
    for period in periods:
        period_list.append({
            'id': period.id,
            'name': period.name,
            'subject': {
                'id': period.subject.id,
                'name': period.subject.name
            },
            'start_time': period.start_time,
            'end_time': period.end_time,
            'days_of_week': period.days_of_week
        })
    
    return Response(period_list) 