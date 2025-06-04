from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count, Q

# Create your models here.
class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    time_in = models.TimeField(default=timezone.now)
    time_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ], default='present')
    
    class Meta:
        unique_together = ['user', 'date']
    
    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.status}"

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    def get_attendance_stats(self, user=None):
        """Get attendance statistics for this subject"""
        query = self.subjectattendance_set
        
        if user:
            query = query.filter(user=user)
            
        total = query.count()
        present = query.filter(status='present').count()
        absent = query.filter(status='absent').count()
        late = query.filter(status='late').count()
        
        if total > 0:
            present_rate = (present / total) * 100
            absent_rate = (absent / total) * 100
            late_rate = (late / total) * 100
        else:
            present_rate = absent_rate = late_rate = 0
            
        return {
            'total': total,
            'present': present,
            'absent': absent,
            'late': late,
            'present_rate': present_rate,
            'absent_rate': absent_rate,
            'late_rate': late_rate
        }

class ClassPeriod(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, help_text="e.g. 'Period 1', 'Morning Class'")
    start_time = models.TimeField()
    end_time = models.TimeField()
    days_of_week = models.CharField(max_length=20, help_text="e.g. 'MWF' for Monday, Wednesday, Friday")
    
    def __str__(self):
        return f"{self.subject.name} - {self.name} ({self.days_of_week})"

class SubjectAttendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    period = models.ForeignKey(ClassPeriod, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=[
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ], default='present')
    notes = models.TextField(blank=True, null=True, help_text="Any additional notes about this attendance record")
    
    class Meta:
        unique_together = ['user', 'subject', 'date', 'period']
        
    def __str__(self):
        return f"{self.user.username} - {self.subject.name} - {self.date} - {self.status}"
