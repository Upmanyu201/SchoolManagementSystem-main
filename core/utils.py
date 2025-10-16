import re

def extract_class_number(class_name):
    """Extract numeric class value for proper sorting"""
    if not class_name:
        return 999
    
    class_str = str(class_name).lower().strip()
    
    # Handle pre-primary classes
    if 'nursery' in class_str or 'nursary' in class_str:
        return 0
    elif 'lkg' in class_str:
        return 1
    elif 'ukg' in class_str:
        return 2
    
    # Extract numeric part - handle "Class 10", "10", etc.
    match = re.search(r'(\d+)', class_str)
    if match:
        return int(match.group(1))
    
    return 999

def natural_sort_key(class_name):
    """Generate sort key for natural class ordering"""
    return extract_class_number(class_name)