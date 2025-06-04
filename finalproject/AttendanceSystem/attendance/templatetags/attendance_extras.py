from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter to get an item from a dictionary using a variable key
    Usage: {{ mydict|get_item:key_variable }}
    """
    if not dictionary:
        return None
    
    # Convert key to string if it's not already (Django template might pass it as string)
    key = str(key)
    
    if key in dictionary:
        return dictionary[key]
    return None 