import re
from error_handler import log_error
import tkinter as tk

def update_word_count(text_widget, count_var):
    """Update the word count for a text widget"""
    try:
        text = text_widget.get("1.0", tk.END).strip()
        word_count = len(re.findall(r'\b\w+\b', text))
        count_var.set(f"Words: {word_count}")
    except Exception as e:
        log_error("Word count update error", e)

def copy_to_clipboard(root, text_widget):
    """Copy the text from a text widget to clipboard"""
    try:
        text = text_widget.get("1.0", tk.END).strip()
        root.clipboard_clear()
        root.clipboard_append(text)
        return True
    except Exception as e:
        log_error("Copy to clipboard error", e)
        return False

def get_tone_options():
    """Get the list of available tone options"""
    return [
        "Neutral/Balanced",
        "Empathetic/Caring",
        "Authoritative/Confident",
        "Optimistic/Positive",
        "Concerned/Serious",
        "Conversational/Friendly",
        "Formal/Professional",
        "Urgent/Call to Action"
    ]

def format_timestamp(timestamp, format_str="%d %b %Y, %H:%M"):
    """Format a timestamp string to a more readable format"""
    try:
        import datetime
        dt = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        return dt.strftime(format_str)
    except Exception as e:
        log_error("Format timestamp error", e)
        return timestamp

def truncate_text(text, max_length=50):
    """Truncate text with ellipsis for display purposes"""
    if not text:
        return ""
    return text[:max_length] + "..." if len(text) > max_length else text