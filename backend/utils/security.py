import re

def sanitize_html(text: str) -> str:
    """Basic HTML sanitization to prevent XSS."""
    if not text:
        return text
    # Remove HTML tags
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)
