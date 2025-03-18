import tkinter as tk
from tkinter import messagebox
import sys
import os
import traceback
import datetime
from mp_rewriter_app import MPStatementRewriter
from error_handler import log_error

def main():
    """Main function to start the application"""
    # Set up exception handler to catch unhandled exceptions
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions"""
        # Log the error
        error_details = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        try:
            # Write to error log
            with open("error_log.txt", "a") as log_file:
                log_file.write(f"\n\n--- Unhandled Error {datetime.datetime.now()} ---\n")
                log_file.write(error_details)
        except:
            pass
        
        # Show error dialog
        messagebox.showerror("Application Error", 
                           "An unexpected error occurred. Please check error_log.txt for details.\n\n" + 
                           str(exc_value))
    
    # Set up exception hook
    sys.excepthook = handle_exception
    
    try:
        # Create and start the main application
        root = tk.Tk()
        app = MPStatementRewriter(root)
        
        # Apply enhanced UI features
        try:
            # Check if the file exists first
            if os.path.exists("application_integrator.py"):
                # Use direct import
                import application_integrator
                # Reload in case it was previously imported
                import importlib
                importlib.reload(application_integrator)
                enhanced_ui = application_integrator.EnhancedUI(app)
                print("Enhanced UI loaded successfully")
            else:
                print("Enhanced UI file not found in current directory")
                messagebox.showinfo("Basic UI Mode", 
                                  "Running with basic UI. Place application_integrator.py in the same folder for enhanced features.")
        except ImportError as e:
            print(f"Import error: {str(e)}")
            messagebox.showwarning("Enhanced UI Unavailable", 
                                  "The EnhancedUI module could not be loaded. The application will run with basic UI.")
            log_error("Enhanced UI Import", e)
        except Exception as e:
            print(f"Enhanced UI error: {str(e)}")
            messagebox.showwarning("Enhanced UI Error", 
                                  "The EnhancedUI could not be initialized. The application will run with basic UI.")
            log_error("Enhanced UI initialization", e)
        
        # Set window icon if available
        try:
            if os.path.exists("icon.ico"):
                root.iconbitmap("icon.ico")
            elif os.path.exists("icon.png"):
                icon_img = tk.PhotoImage(file="icon.png")
                root.iconphoto(True, icon_img)
        except:
            pass  # Ignore icon errors
        
        # Center window on screen
        window_width = root.winfo_reqwidth()
        window_height = root.winfo_reqheight()
        position_right = int(root.winfo_screenwidth()/2 - window_width/2)
        position_down = int(root.winfo_screenheight()/2 - window_height/2)
        root.geometry(f"+{position_right}+{position_down}")
        
        # Add window close confirmation if there are unsaved changes
        def on_closing():
            if app.current_submission_id and messagebox.askyesno("Confirm Exit", 
                                                            "You have unsaved changes. Are you sure you want to exit?"):
                root.destroy()
            elif not app.current_submission_id:
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Start the application
        root.mainloop()
        
    except Exception as e:
        messagebox.showerror("Startup Error", f"Failed to start application: {str(e)}")
        log_error("Application startup", e)


if __name__ == "__main__":
    main()