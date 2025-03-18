# application_integrator.py
# Enhanced UI integration module for MP Statement Rewriter

import tkinter as tk
from tkinter import ttk, messagebox
import re
import os
import threading
import sqlite3
import difflib
import traceback

class EnhancedUI:
    """Class to integrate enhanced UI features into the main application"""
    
    def __init__(self, app):
        """Initialize with reference to the main application"""
        self.app = app
        try:
            self.integrate_enhanced_features()
        except Exception as e:
            self.handle_initialization_error(e)
    
    def handle_initialization_error(self, exception):
        """Handle any errors during initialization"""
        try:
            error_message = f"Error initializing enhanced UI: {str(exception)}"
            with open("error_log.txt", "a") as log_file:
                log_file.write(f"\n[{self.get_timestamp()}] ERROR in EnhancedUI initialization: {str(exception)}\n")
                log_file.write("".join(traceback.format_exception(type(exception), exception, exception.__traceback__)))
                log_file.write("\n" + "-"*80 + "\n")
            
            messagebox.showwarning("Enhanced UI Error", 
                                 "Some advanced UI features could not be initialized. The application will use basic UI.")
        except:
            # Silent failure if even the error handler fails
            pass
    
    def get_timestamp(self):
        """Get current timestamp string"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def integrate_enhanced_features(self):
        """Add all enhanced features to the main application"""
        # First check if all required attributes exist
        self.verify_required_attributes()
        
        # Add tooltips
        self.add_tooltips()
        
        # Set up context suggestions
        self.setup_context_suggestions()
        
        # Add word count validation
        self.setup_word_count_validation()
        
        # Setup highlight changes functionality
        self.setup_highlighting()
        
        # Add audience suggestions dropdown
        self.setup_audience_suggestions()
        
        # Enhanced progress indicator
        self.enhance_progress_indicator()
        
        # Theme improvements
        self.apply_theme_improvements()
    
    def verify_required_attributes(self):
        """Verify all required attributes exist in the main app"""
        # Check for required attributes
        required_attrs = [
            'raw_statement', 'context', 'target_audience', 'tone_dropdown',
            'notes', 'generated_statement', 'accept_button', 'refresh_button',
            'edit_button', 'copy_button', 'progress'
        ]
        
        missing = []
        for attr in required_attrs:
            if not hasattr(self.app, attr) or getattr(self.app, attr) is None:
                missing.append(attr)
        
        if missing:
            raise AttributeError(f"Missing required attributes in main app: {', '.join(missing)}")
    
    def add_tooltips(self):
        """Add helpful tooltips to UI elements"""
        tooltips = {
            self.app.raw_statement: "Enter the original government statement that needs to be transformed into the MP's voice.",
            self.app.context: "Add local issues, constituency history, or specific concerns relevant to this statement.",
            self.app.target_audience: "Specify who will read this message (e.g., 'parents of school children', 'local business owners').",
            self.app.tone_dropdown: "Select the tone that best matches your communication needs.",
            self.app.notes: "Add any additional comments or tags to help categorize or remember this statement.",
            self.app.generated_statement: "The AI-generated response in the MP's voice. You can edit this after clicking the Edit button.",
            self.app.accept_button: "Save this statement and add it to your approved statements library.",
            self.app.refresh_button: "Generate a new version with a different approach.",
            self.app.edit_button: "Make manual edits to the generated statement.",
            self.app.copy_button: "Copy the statement to your clipboard."
        }
        
        for widget, text in tooltips.items():
            self.create_tooltip(widget, text)
    
    def setup_context_suggestions(self):
        """Set up context field with common suggestions"""
        common_contexts = [
            "Our constituency has been waiting for this funding for years.",
            "Local residents have repeatedly raised this issue in my surgeries.",
            "This builds on my campaign promise to improve local services.",
            "The recent problems with local services make this particularly relevant.",
            "I've been lobbying ministers about this issue for months.",
            "This follows our community consultation last month.",
            "After visiting affected areas in our constituency last week,"
        ]
        
        self.add_dropdown_suggestions(self.app.context, common_contexts)
    
    def setup_audience_suggestions(self):
        """Set up audience field with common suggestions"""
        common_audiences = [
            "Local residents",
            "Parents of school children",
            "Elderly constituents",
            "Small business owners",
            "Healthcare workers",
            "Young people and students",
            "Commuters and transport users",
            "Rural community members",
            "Urban residents",
            "Environmental campaigners",
            "Job seekers",
            "Homeowners"
        ]
        
        self.add_dropdown_suggestions(self.app.target_audience, common_audiences)
    
    def setup_word_count_validation(self):
        """Set up word count validation for text fields"""
        # Add word limit indicators
        self.app.raw_word_limit = tk.StringVar()
        self.app.raw_word_limit.set("Words: 0/500")
        ttk.Label(self.app.raw_statement.master, textvariable=self.app.raw_word_limit).grid(row=3, column=0, sticky=tk.E, pady=(0, 10))
        
        self.app.generated_word_limit = tk.StringVar()
        self.app.generated_word_limit.set("Words: 0/500")
        ttk.Label(self.app.generated_statement.master, textvariable=self.app.generated_word_limit).grid(row=3, column=0, sticky=tk.W, pady=(0, 10))
        
        # Override update word count functions
        self.app.update_raw_word_count = lambda event=None: self.validate_word_limit(
            self.app.raw_statement, 500, self.app.raw_word_limit)
        
        self.app.update_generated_word_count = lambda event=None: self.validate_word_limit(
            self.app.generated_statement, 500, self.app.generated_word_limit)
        
        # Rebind events
        self.app.raw_statement.bind('<KeyRelease>', self.app.update_raw_word_count)
        self.app.generated_statement.bind('<KeyRelease>', self.app.update_generated_word_count)
        
        # Initial update
        self.app.update_raw_word_count()
        self.app.update_generated_word_count()
    
    def setup_highlighting(self):
        """Set up change highlighting functionality"""
        # Store original text for comparison
        self.app.original_generated_text = ""
        
        # Override the update_ui_with_generation function
        original_update_ui = self.app.update_ui_with_generation
        
        def enhanced_update_ui(generated_text):
            self.app.original_generated_text = generated_text
            original_update_ui(generated_text)
        
        self.app.update_ui_with_generation = enhanced_update_ui
        
        # Override the enable_editing function
        original_enable_editing = self.app.enable_editing
        
        def enhanced_enable_editing():
            original_enable_editing()
            
            # Add binding for highlighting changes as user edits
            def on_edit(event):
                current_text = self.app.generated_statement.get("1.0", tk.END).strip()
                self.highlight_text_changes(self.app.original_generated_text, current_text, self.app.generated_statement)
            
            self.app.generated_statement.bind("<KeyRelease>", on_edit)
        
        self.app.enable_editing = enhanced_enable_editing
    
    def enhance_progress_indicator(self):
        """Enhance the progress indicator with animation"""
        # Override the submit function to use animated progress
        original_submit = self.app.submit
        
        def enhanced_submit():
            # Get input values (same as original)
            raw_text = self.app.raw_statement.get("1.0", tk.END).strip()
            context = self.app.context.get().strip()
            audience = self.app.target_audience.get().strip()
            tone = self.app.tone_var.get()
            notes = self.app.notes.get().strip()
            
            # Validate inputs
            if not raw_text:
                messagebox.showwarning("Input Required", "Please enter the raw government statement.")
                return
            
            # Update status
            self.app.status_var.set("Generating rewritten statement...")
            
            # Disable buttons while processing
            self.app.accept_button.config(state=tk.DISABLED)
            self.app.refresh_button.config(state=tk.DISABLED)
            self.app.edit_button.config(state=tk.DISABLED)
            self.app.copy_button.config(state=tk.DISABLED)
            
            # Show and animate progress bar
            self.animate_progress(self.app.progress, 3.0)
            
            # Use threading to prevent UI freeze
            threading.Thread(target=self.app.process_submission, args=(raw_text, context, audience, tone, notes)).start()
        
        self.app.submit = enhanced_submit
        
        # Same for refresh
        original_refresh = self.app.refresh_statement
        
        def enhanced_refresh():
            if not self.app.current_submission_id:
                messagebox.showwarning("No Submission", "No statement has been generated yet.")
                return
            
            try:
                # Mark current submission as rejected
                conn = sqlite3.connect('mp_rewriter.db')
                cursor = conn.cursor()
                
                cursor.execute("""
                UPDATE submissions SET status = 'rejected' WHERE id = ?
                """, (self.app.current_submission_id,))
                
                conn.commit()
                conn.close()
                
                # Get original inputs for regeneration
                raw_text = self.app.raw_statement.get("1.0", tk.END).strip()
                context = self.app.context.get().strip()
                audience = self.app.target_audience.get().strip()
                tone = self.app.tone_var.get()
                notes = self.app.notes.get().strip()
                
                # Update status
                self.app.status_var.set("Regenerating statement with new approach...")
                
                # Show and animate progress bar
                self.animate_progress(self.app.progress, 3.5)  # Slightly longer for "thinking"
                
                # Disable buttons while processing
                self.app.accept_button.config(state=tk.DISABLED)
                self.app.refresh_button.config(state=tk.DISABLED)
                self.app.edit_button.config(state=tk.DISABLED)
                self.app.copy_button.config(state=tk.DISABLED)
                
                # Regenerate with slightly higher temperature for diversity
                threading.Thread(target=self.app.process_refresh, args=(raw_text, context, audience, tone, notes)).start()
                
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to refresh statement: {str(e)}")
                self.log_error("Enhanced refresh error", e)
        
        self.app.refresh_statement = enhanced_refresh
    
    def apply_theme_improvements(self):
        """Apply theme improvements to the application"""
        # Apply theme colors
        self.apply_theme_colors(self.app.root)
        
        # Add visual feedback when statement is accepted
        original_accept = self.app.accept_statement
        
        def enhanced_accept():
            result = original_accept()
            if result:  # Only pulse if successful
                self.pulse_widget(self.app.generated_statement)
            return result
        
        self.app.accept_statement = enhanced_accept
    
    # Helper functions
    def create_tooltip(self, widget, text):
        """Create a tooltip for the given widget with the specified text"""
        def enter(event):
            try:
                x, y, _, _ = widget.bbox("insert") if hasattr(widget, "bbox") else (0, 0, 0, 0)
                x += widget.winfo_rootx() + 25
                y += widget.winfo_rooty() + 25
                
                # Create a toplevel window
                tooltip = tk.Toplevel(widget)
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry(f"+{x}+{y}")
                
                # Add a label in the toplevel window
                label = tk.Label(tooltip, text=text, justify=tk.LEFT,
                                background="#ffffff", relief=tk.SOLID, borderwidth=1,
                                font=("Segoe UI", "9", "normal"))
                label.pack(padx=5, pady=5)
                
                # Assign the tooltip to the widget
                widget.tooltip = tooltip
            except Exception as e:
                # Silently fail if tooltip creation fails - not critical
                pass
            
        def leave(event):
            if hasattr(widget, "tooltip"):
                try:
                    widget.tooltip.destroy()
                except:
                    pass
        
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
    
    def apply_theme_colors(self, root):
        """Apply a consistent color theme to the application"""
        try:
            # Define colors
            bg_color = "#f0f0f0"
            accent_color = "#0078D7"
            
            # Set window background
            root.config(bg=bg_color)
            
            # Apply to all frames
            for widget in root.winfo_children():
                if isinstance(widget, ttk.Frame) or isinstance(widget, ttk.LabelFrame):
                    widget.config(style='Themed.TFrame')
            
            # Create themed styles
            style = ttk.Style()
            style.configure('Themed.TFrame', background=bg_color)
            style.configure('Themed.TLabelframe', background=bg_color)
            style.configure('Accent.TButton', foreground='white', background=accent_color)
        except Exception as e:
            # Silently fail - theming is not critical
            pass
    
    def validate_word_limit(self, text_widget, limit=500, label_var=None):
        """Validate the word count and update label, return True if within limit"""
        try:
            text = text_widget.get("1.0", tk.END).strip()
            word_count = len(re.findall(r'\b\w+\b', text))
            
            if label_var:
                if word_count > limit:
                    label_var.set(f"Words: {word_count}/{limit} (Exceeds limit)")
                    return False
                else:
                    label_var.set(f"Words: {word_count}/{limit}")
            
            return word_count <= limit
        except Exception as e:
            # Fail gracefully - validation is not critical
            if label_var:
                label_var.set(f"Words: {0}/{limit}")
            return True
    
    def highlight_text_changes(self, original_text, new_text, text_widget):
        """Highlight the differences between original and new text"""
        try:
            # Clear any existing tags
            for tag in text_widget.tag_names():
                if tag.startswith("change_"):
                    text_widget.tag_delete(tag)
            
            # Skip if either text is empty
            if not original_text or not new_text:
                return
                
            # Split texts into words and punctuation
            original_words = re.findall(r'\b\w+\b|\W+', original_text)
            new_words = re.findall(r'\b\w+\b|\W+', new_text)
            
            # Find differences
            differ = difflib.SequenceMatcher(None, original_words, new_words)
            
            # Get current content with line information
            current_content = text_widget.get("1.0", tk.END)
            lines = current_content.split('\n')
            
            # Process differences
            for tag, i1, i2, j1, j2 in differ.get_opcodes():
                if tag in ('replace', 'insert'):
                    # Calculate the text that was inserted or replaced
                    added_text = ''.join(new_words[j1:j2])
                    if not added_text.strip():
                        continue
                    
                    # Find this text in the widget
                    start_index = "1.0"
                    while True:
                        try:
                            start_index = text_widget.search(added_text, start_index, stopindex=tk.END)
                            if not start_index:
                                break
                            
                            end_index = f"{start_index}+{len(added_text)}c"
                            
                            # Create tag for this change
                            tag_name = f"change_{i1}_{j1}_{j2}"
                            text_widget.tag_add(tag_name, start_index, end_index)
                            text_widget.tag_config(tag_name, background="#FFFF99")
                            
                            # Move to next occurrence
                            start_index = end_index
                        except:
                            # Break the loop if there's an error in search/tag
                            break
            
        except Exception as e:
            # Silently fail - highlighting is not critical functionality
            pass
    
    def animate_progress(self, progress_bar, duration=3.0):
        """Animate the progress bar over the specified duration"""
        try:
            progress_bar.grid()  # Make sure it's visible
            progress_bar.config(mode='determinate', maximum=100, value=0)
            
            def update_progress(elapsed=0, interval=0.05):
                if elapsed < duration:
                    progress = min(100, int((elapsed / duration) * 100))
                    progress_bar.config(value=progress)
                    self.app.root.after(int(interval * 1000), lambda: update_progress(elapsed + interval, interval))
                else:
                    progress_bar.config(value=100)
            
            update_progress()
        except Exception as e:
            # If animation fails, just show indeterminate progress
            try:
                progress_bar.grid()
                progress_bar.config(mode='indeterminate')
                progress_bar.start()
            except:
                pass
    
    def pulse_widget(self, widget, times=3):
        """Create an attention-grabbing pulse effect on a widget"""
        try:
            if hasattr(widget, 'cget'):
                original_bg = widget.cget("background") if widget.cget("background") else "#ffffff"
            else:
                original_bg = "#ffffff"
            
            def flash(count=0):
                if count >= times * 2:
                    widget.config(background=original_bg)
                    return
                
                if count % 2 == 0:
                    widget.config(background="#e1f5fe")  # Light blue flash
                else:
                    widget.config(background=original_bg)
                    
                self.app.root.after(200, lambda: flash(count + 1))
            
            flash()
        except Exception as e:
            # Silently fail - visual feedback is not critical
            pass
    
    def add_dropdown_suggestions(self, entry_widget, suggestions):
        """Add dropdown suggestions to an Entry widget"""
        try:
            # Store suggestions
            if not hasattr(entry_widget, 'suggestions'):
                entry_widget.suggestions = suggestions
            
            # Create a listbox popup for suggestions
            def show_suggestions(event=None):
                # Get entry text
                text = entry_widget.get()
                
                # If there's text, filter suggestions
                matching = [s for s in entry_widget.suggestions if text.lower() in s.lower()]
                if matching:
                    show_dropdown(matching)
            
            def show_dropdown(matching):
                try:
                    # Create or clear the listbox
                    if not hasattr(entry_widget, 'suggestion_lb'):
                        # Calculate position
                        x = entry_widget.winfo_rootx()
                        y = entry_widget.winfo_rooty() + entry_widget.winfo_height()
                        width = entry_widget.winfo_width()
                        
                        # Create listbox
                        lb = tk.Listbox(self.app.root, width=width)
                        lb.place(x=x, y=y, width=width)
                        entry_widget.suggestion_lb = lb
                        
                        # Bind selection
                        lb.bind("<<ListboxSelect>>", lambda e: select_suggestion())
                        lb.bind("<FocusOut>", lambda e: hide_dropdown())
                    else:
                        entry_widget.suggestion_lb.delete(0, tk.END)
                        entry_widget.suggestion_lb.place(
                            x=entry_widget.winfo_rootx(),
                            y=entry_widget.winfo_rooty() + entry_widget.winfo_height(),
                            width=entry_widget.winfo_width()
                        )
                    
                    # Add matching items (limit to 10)
                    for item in matching[:10]:
                        entry_widget.suggestion_lb.insert(tk.END, item)
                except Exception as e:
                    # Silently fail if dropdown creation fails
                    pass
            
            def select_suggestion():
                try:
                    if hasattr(entry_widget, 'suggestion_lb') and entry_widget.suggestion_lb.curselection():
                        selected = entry_widget.suggestion_lb.get(entry_widget.suggestion_lb.curselection()[0])
                        entry_widget.delete(0, tk.END)
                        entry_widget.insert(0, selected)
                        hide_dropdown()
                except:
                    hide_dropdown()
            
            def hide_dropdown():
                if hasattr(entry_widget, 'suggestion_lb'):
                    try:
                        entry_widget.suggestion_lb.place_forget()
                    except:
                        pass
            
            # Bind events
            entry_widget.bind("<KeyRelease>", show_suggestions)
            entry_widget.bind("<FocusOut>", lambda e: self.app.root.after(100, hide_dropdown))
            
            # Create dropdown button
            if not hasattr(entry_widget, 'dropdown_button'):
                # Override entry_widget's master grid function to update button position
                original_grid = entry_widget.grid
                
                def grid_override(*args, **kwargs):
                    result = original_grid(*args, **kwargs)
                    self.app.root.after(100, add_dropdown_button)
                    return result
                
                try:
                    entry_widget.grid = grid_override
                except:
                    pass
                
                # Create dropdown button
                def add_dropdown_button():
                    try:
                        if hasattr(entry_widget, 'dropdown_button'):
                            entry_widget.dropdown_button.destroy()
                        
                        button = ttk.Button(entry_widget.master, text="▼", width=2, 
                                            command=lambda: show_suggestions())
                        
                        # Position to the right of entry widget
                        entry_info = entry_widget.grid_info()
                        button.grid(row=entry_info['row'], column=entry_info['column']+1, padx=(0, 5))
                        
                        # Store reference
                        entry_widget.dropdown_button = button
                    except:
                        # Silently fail if button creation fails
                        pass
                
                self.app.root.after(100, add_dropdown_button)
        except Exception as e:
            # Silently fail - suggestions are not critical
            pass
    
    def log_error(self, context, exception):
        """Log an error to the error log file"""
        try:
            with open("error_log.txt", "a") as log_file:
                log_file.write(f"\n[{self.get_timestamp()}] ERROR in EnhancedUI {context}: {str(exception)}\n")
                log_file.write("".join(traceback.format_exception(type(exception), exception, exception.__traceback__)))
                log_file.write("\n" + "-"*80 + "\n")
        except:
            # Silent failure for logging errors
            pass