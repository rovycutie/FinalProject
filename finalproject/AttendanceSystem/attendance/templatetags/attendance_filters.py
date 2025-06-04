from django import template

register = template.Library()

@register.filter(name='filter_by_user')
def filter_by_user(attendance_records, user):
    """Filter attendance records by user"""
    for record in attendance_records:
        if record.user == user:
            return record
    return None 