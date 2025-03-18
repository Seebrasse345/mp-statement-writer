import datetime
import traceback

def log_error(error_context, exception):
    """Log errors to a file with context information"""
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format the error message
        error_message = f"[{timestamp}] ERROR in {error_context}: {str(exception)}\n"
        error_message += "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        error_message += "\n" + "-"*80 + "\n"
        
        # Write to error log file
        with open("error_log.txt", "a") as log_file:
            log_file.write(error_message)
    except:
        # If we can't even log the error, just print it
        print(f"ERROR in {error_context}: {str(exception)}")
        traceback.print_exc()