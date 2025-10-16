from django import template

register = template.Library()

@register.filter
def number_to_words(value):
    """Convert number to words"""
    try:
        num = int(float(value))
    except (ValueError, TypeError):
        return str(value)
    
    if num == 0:
        return "zero"
    
    ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
            "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
            "seventeen", "eighteen", "nineteen"]
    
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    
    def convert_hundreds(n):
        result = ""
        if n >= 100:
            result += ones[n // 100] + " hundred "
            n %= 100
        if n >= 20:
            result += tens[n // 10] + " "
            n %= 10
        if n > 0:
            result += ones[n] + " "
        return result.strip()
    
    if num < 0:
        return "minus " + number_to_words(-num)
    
    if num < 1000:
        return convert_hundreds(num)
    elif num < 100000:
        thousands = num // 1000
        remainder = num % 1000
        result = convert_hundreds(thousands) + " thousand"
        if remainder > 0:
            result += " " + convert_hundreds(remainder)
        return result
    elif num < 10000000:
        lakhs = num // 100000
        remainder = num % 100000
        result = convert_hundreds(lakhs) + " lakh"
        if remainder > 0:
            if remainder >= 1000:
                result += " " + convert_hundreds(remainder // 1000) + " thousand"
                remainder %= 1000
            if remainder > 0:
                result += " " + convert_hundreds(remainder)
        return result
    else:
        crores = num // 10000000
        remainder = num % 10000000
        result = convert_hundreds(crores) + " crore"
        if remainder > 0:
            if remainder >= 100000:
                result += " " + convert_hundreds(remainder // 100000) + " lakh"
                remainder %= 100000
            if remainder >= 1000:
                result += " " + convert_hundreds(remainder // 1000) + " thousand"
                remainder %= 1000
            if remainder > 0:
                result += " " + convert_hundreds(remainder)
        return result