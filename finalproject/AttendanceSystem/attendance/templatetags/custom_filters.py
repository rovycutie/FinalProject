from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Get an item from a dictionary using the key.
    Handles both string and integer keys.
    """
    if dictionary is None:
        return None
        
    # Try the key as is
    if key in dictionary:
        return dictionary[key]
    
    # Try converting string to int
    try:
        if isinstance(key, str) and key.isdigit():
            int_key = int(key)
            if int_key in dictionary:
                return dictionary[int_key]
    except (ValueError, TypeError):
        pass
    
    return dictionary.get(key) 