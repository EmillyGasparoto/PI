import re
from datetime import datetime, date

def validate_email(email):
    """
    Validate email format
    
    Args:
        email (str): Email to validate
        
    Returns:
        bool: True if email is valid, False otherwise
    """
    if not email:
        return False
    
    # Simple regex for email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone):
    """
    Validate phone number format
    
    Args:
        phone (str): Phone number to validate
        
    Returns:
        bool: True if phone is valid, False otherwise
    """
    if not phone:
        return False
    
    # Remove spaces, dashes, and parentheses
    clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Check if it's a valid phone number (at least 10 digits)
    return bool(re.match(r'^\+?[0-9]{10,15}$', clean_phone))

def validate_date(date_str, format_str='%Y-%m-%d'):
    """
    Validate date format
    
    Args:
        date_str (str): Date string to validate
        format_str (str): Expected date format
        
    Returns:
        bool: True if date is valid, False otherwise
    """
    if not date_str:
        return False
    
    try:
        datetime.strptime(date_str, format_str)
        return True
    except ValueError:
        return False

def validate_time(time_str, format_str='%H:%M'):
    """
    Validate time format
    
    Args:
        time_str (str): Time string to validate
        format_str (str): Expected time format
        
    Returns:
        bool: True if time is valid, False otherwise
    """
    if not time_str:
        return False
    
    try:
        datetime.strptime(time_str, format_str)
        return True
    except ValueError:
        return False

def validate_future_date(date_str, format_str='%Y-%m-%d'):
    """
    Validate that the date is in the future
    
    Args:
        date_str (str): Date string to validate
        format_str (str): Expected date format
        
    Returns:
        bool: True if date is valid and in the future, False otherwise
    """
    if not validate_date(date_str, format_str):
        return False
    
    try:
        date_obj = datetime.strptime(date_str, format_str).date()
        return date_obj >= date.today()
    except ValueError:
        return False

def validate_password_strength(password):
    """
    Validate password strength
    
    Args:
        password (str): Password to validate
        
    Returns:
        bool: True if password meets strength requirements, False otherwise
    """
    if not password or len(password) < 8:
        return False
    
    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False
    
    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False
    
    # Check for at least one digit
    if not re.search(r'[0-9]', password):
        return False
    
    return True

def sanitize_input(input_str):
    """
    Sanitize input to prevent XSS attacks
    
    Args:
        input_str (str): Input string to sanitize
        
    Returns:
        str: Sanitized input string
    """
    if not input_str:
        return ''
    
    # Replace potentially harmful characters
    return (input_str
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#x27;')
            .replace('/', '&#x2F;'))
