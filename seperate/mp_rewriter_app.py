import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import threading
import csv
import sqlite3
from tkinter import scrolledtext

# Import custom modules
from error_handler import log_error
from database_manager import initialize_database, log_submission, get_past_responses, update_submission_status, get_submission_by_id, save_accepted_statement
from ui_components import setup_styles, create_menu, create_input_panel, create_output_panel, create_status_bar
from api_manager import ApiManager
from system_prompt import construct_prompt, construct_refresh_prompt
from history_manager import (create_history_window, load_submissions, search_submissions, 
                          view_submission_details, create_approved_statements_window, 
                          search_approved_statements, view_approved_statement_details)
from config_manager import save_api_settings
from sample_data import populate_sample_data
from utils import update_word_count, copy_to_clipboard

class MPStatementRewriter:
    def __init__(self, root):
        self.root = root
        self.root.title("MP Statement Rewriter - AI-Powered Communication Tool")
        self.root.geometry("1400x800")
        self.root.minsize(1000, 700)
        
        # Define variables first before using them
        # Status variable
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        
        # Word count variables
        self.raw_word_count = tk.StringVar()
        self.raw_word_count.set("Words: 0")
        
        self.generated_word_count = tk.StringVar()
        self.generated_word_count.set("Words: 0")
        
        # Current submission ID
        self.current_submission_id = None
        
        # History window reference
        self.history_window = None
        
        # UI widget references - will be populated by create_ui
        self.raw_statement = None
        self.context = None
        self.target_audience = None
        self.tone_dropdown = None
        self.tone_var = None
        self.notes = None
        self.generated_statement = None
        self.accept_button = None
        self.refresh_button = None
        self.edit_button = None
        self.copy_button = None
        self.progress = None
        
        # Set application icon if available
        try:
            if os.path.exists("icon.ico"):
                self.root.iconbitmap("icon.ico")
        except:
            pass  # Ignore if icon setting fails
        
        # Define tone options (moved from create_ui)
        self.tone_options = [
            "Neutral/Balanced",
            "Empathetic/Caring",
            "Authoritative/Confident",
            "Optimistic/Positive",
            "Concerned/Serious",
            "Conversational/Friendly",
            "Formal/Professional",
            "Urgent/Call to Action"
        ]
        
        # Initialize database first
        initialize_database()
        
        # Initialize OpenAI API
        self.api_manager = ApiManager()
        
        # Set up style
        setup_styles()
        
        # Create UI elements
        self.create_ui()
        
        # Load sample data if needed (moved after database initialization)
        threading.Thread(target=populate_sample_data).start()

    def create_ui(self):
        """Create the user interface"""
        try:
            # Create main frame with two panels
            main_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Left panel (Input)
            left_frame = ttk.LabelFrame(main_frame, text="Input Parameters")
            main_frame.add(left_frame, weight=1)
            
            # Right panel (Output)
            right_frame = ttk.LabelFrame(main_frame, text="Generated Output")
            main_frame.add(right_frame, weight=1)
            
            # Set up menu callbacks
            menu_callbacks = {
                'clear_all_fields': self.clear_all_fields,
                'export_statement': self.export_statement,
                'open_history': self.open_history,
                'view_approved_statements': self.view_approved_statements,
                'import_past_statements': self.import_past_statements,
                'open_settings': self.open_settings,
                'show_user_guide': self.show_user_guide,
                'show_about': self.show_about
            }
            
            # Create the menu
            create_menu(self.root, menu_callbacks)
            
            # Set up input panel callbacks
            input_callbacks = {
                'update_raw_word_count': self.update_raw_word_count,
                'clear_all_fields': self.clear_all_fields,
                'submit': self.submit
            }
            
            # Create the input panel
            input_widgets = create_input_panel(left_frame, 
                                            {'raw_word_count': self.raw_word_count}, 
                                            input_callbacks)
            
            # Set up output panel callbacks
            output_callbacks = {
                'update_generated_word_count': self.update_generated_word_count,
                'enable_editing': self.enable_editing,
                'refresh_statement': self.refresh_statement,
                'accept_statement': self.accept_statement,
                'copy_to_clipboard': self.copy_to_clipboard
            }
            
            # Create the output panel
            output_widgets = create_output_panel(right_frame, 
                                              {'generated_word_count': self.generated_word_count}, 
                                              output_callbacks)
            
            # Set references to widgets
            self.raw_statement = input_widgets['raw_statement']
            self.context = input_widgets['context']
            self.target_audience = input_widgets['target_audience']
            self.tone_dropdown = input_widgets['tone_dropdown']
            self.tone_var = input_widgets['tone_var']
            self.notes = input_widgets['notes']
            
            self.generated_statement = output_widgets['generated_statement']
            self.progress = output_widgets['progress']
            self.edit_button = output_widgets['edit_button']
            self.refresh_button = output_widgets['refresh_button']
            self.accept_button = output_widgets['accept_button']
            self.copy_button = output_widgets['copy_button']
            
            # Status bar
            create_status_bar(self.root, self.status_var)
        except Exception as e:
            messagebox.showerror("UI Error", f"Failed to create UI: {str(e)}")
            log_error("UI creation error", e)
    
    def update_raw_word_count(self, event=None):
        """Update the word count for the raw statement text box"""
        update_word_count(self.raw_statement, self.raw_word_count)

    def update_generated_word_count(self, event=None):
        """Update the word count for the generated statement text box"""
        update_word_count(self.generated_statement, self.generated_word_count)

    def clear_all_fields(self):
        """Clear all input and output fields"""
        try:
            if messagebox.askyesno("Clear Form", "Are you sure you want to clear all fields?"):
                self.raw_statement.delete("1.0", tk.END)
                self.context.delete(0, tk.END)
                self.target_audience.delete(0, tk.END)
                self.tone_dropdown.current(0)
                self.notes.delete(0, tk.END)
                self.generated_statement.delete("1.0", tk.END)
                self.current_submission_id = None
                self.accept_button.config(state=tk.DISABLED)
                self.refresh_button.config(state=tk.DISABLED)
                self.edit_button.config(state=tk.DISABLED)
                self.copy_button.config(state=tk.DISABLED)
                self.status_var.set("Form cleared. Ready for new input.")
                self.update_raw_word_count()
                self.update_generated_word_count()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear fields: {str(e)}")
            log_error("Clear fields error", e)

    def enable_editing(self):
        """Enable manual editing of the generated statement"""
        try:
            self.generated_statement.config(state=tk.NORMAL)
            self.status_var.set("Editing mode enabled. Make your changes and then click Accept & Save.")
            messagebox.showinfo("Editing Enabled", "You can now edit the generated statement directly. Click 'Accept & Save' when done.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to enable editing: {str(e)}")
            log_error("Enable editing error", e)

    def copy_to_clipboard(self):
        """Copy the generated statement to clipboard"""
        try:
            if copy_to_clipboard(self.root, self.generated_statement):
                self.status_var.set("Statement copied to clipboard.")
                messagebox.showinfo("Copied", "The statement has been copied to your clipboard.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy to clipboard: {str(e)}")
            log_error("Copy to clipboard error", e)

    def export_statement(self):
        """Export the generated statement to a text file"""
        try:
            if not self.generated_statement.get("1.0", tk.END).strip():
                messagebox.showwarning("No Content", "There is no statement to export.")
                return
                
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Export Statement"
            )
            
            if not file_path:
                return
                
            with open(file_path, 'w') as file:
                text = self.generated_statement.get("1.0", tk.END).strip()
                file.write(text)
                
            self.status_var.set(f"Statement exported to {file_path}")
            messagebox.showinfo("Export Successful", f"Statement successfully exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export statement: {str(e)}")
            log_error("Export statement error", e)

    def open_history(self):
        """Open a window showing submission history"""
        try:
            if self.history_window is not None and self.history_window.winfo_exists():
                self.history_window.lift()
                return
            
            # Create callbacks dictionary for the history window
            history_callbacks = {
                'load_submissions': load_submissions,
                'search_submissions': search_submissions,
                'view_submission_details': lambda submission_id: self.view_submission_details(submission_id),
                'load_submission_to_editor': self.load_submission_to_editor
            }
            
            # Create the history window
            self.history_window, self.history_tree = create_history_window(self.root, history_callbacks)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open history: {str(e)}")
            log_error("Open history error", e)

    def view_submission_details(self, submission_id):
        """Show details of a specific submission"""
        try:
            detail_window, callbacks = view_submission_details(self.root, submission_id)
            if detail_window and callbacks:
                # Set the callbacks to use our methods
                callbacks['load_submission'] = self.load_submission_to_editor
                callbacks['copy_to_clipboard'] = lambda: copy_to_clipboard(self.root, self.generated_statement)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to view submission details: {str(e)}")
            log_error("View submission details error", e)

    def load_submission_to_editor(self, submission_id):
        """Load a submission from history into the editor"""
        try:
            if not submission_id:
                messagebox.showwarning("No Selection", "Please select a submission to load.")
                return
            
            # Get submission from database    
            result = get_submission_by_id(submission_id)
            
            if not result:
                messagebox.showwarning("Not Found", f"Submission #{submission_id} not found.")
                return
                
            original, context, audience, tone, generated, notes = result
            
            # Clear current fields
            self.raw_statement.delete("1.0", tk.END)
            self.context.delete(0, tk.END)
            self.target_audience.delete(0, tk.END)
            self.notes.delete(0, tk.END)
            self.generated_statement.delete("1.0", tk.END)
            
            # Set values from submission
            self.raw_statement.insert(tk.END, original)
            self.context.insert(0, context)
            self.target_audience.insert(0, audience)
            self.notes.insert(0, notes or "")
            
            # Set tone
            if tone in self.tone_options:
                self.tone_dropdown.set(tone)
            else:
                self.tone_dropdown.current(0)
                
            # Set generated statement
            self.generated_statement.insert(tk.END, generated)
            
            # Update word counts
            self.update_raw_word_count()
            self.update_generated_word_count()
            
            # Enable buttons
            self.accept_button.config(state=tk.NORMAL)
            self.refresh_button.config(state=tk.NORMAL)
            self.edit_button.config(state=tk.NORMAL)
            self.copy_button.config(state=tk.NORMAL)
            
            # Set current submission ID
            self.current_submission_id = submission_id
            
            # Close history window if it exists
            if self.history_window and self.history_window.winfo_exists():
                self.history_window.destroy()
                
            self.status_var.set(f"Loaded submission #{submission_id}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load submission: {str(e)}")
            log_error("Load submission to editor error", e)

    def view_approved_statements(self):
        """View all approved past statements"""
        try:
            # Create callbacks for the approved statements window
            approved_callbacks = {
                'search_approved': search_approved_statements,
                'view_approved_details': lambda statement_id: self.view_approved_details(statement_id)
            }
            
            # Create the approved statements window
            approved_window, tree = create_approved_statements_window(self.root, approved_callbacks)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load approved statements: {str(e)}")
            log_error("View approved statements error", e)

    def view_approved_details(self, statement_id):
        """View details of an approved statement"""
        try:
            # Create callbacks for the details window
            detail_callbacks = {
                'use_as_template': self.use_as_template
            }
            
            # Show the details window
            detail_window = view_approved_statement_details(self.root, statement_id, detail_callbacks)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to view statement details: {str(e)}")
            log_error("View approved details error", e)

    def use_as_template(self, text):
        """Use an approved statement as a template"""
        try:
            self.generated_statement.delete("1.0", tk.END)
            self.generated_statement.insert(tk.END, text)
            self.update_generated_word_count()
            self.status_var.set("Past statement loaded as template. You can now edit it.")
            self.edit_button.config(state=tk.NORMAL)
            self.accept_button.config(state=tk.NORMAL)
            self.copy_button.config(state=tk.NORMAL)
            
            # Enable editing by default
            self.enable_editing()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to use template: {str(e)}")
            log_error("Use as template error", e)

    def import_past_statements(self):
        """Import past statements from a CSV file"""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Import Past Statements from CSV"
            )
            
            if not file_path:
                return
                
            # Ask for confirmation
            if not messagebox.askyesno("Confirm Import", 
                                     "This will import past statements from the selected CSV file. Continue?"):
                return
                
            # Show import dialog
            import_window = tk.Toplevel(self.root)
            import_window.title("Import Statements")
            import_window.geometry("600x400")
            import_window.grab_set()  # Modal dialog
            
            frame = ttk.Frame(import_window, padding=10)
            frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(frame, text=f"Importing from: {os.path.basename(file_path)}", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 10))
            
            # Progress text
            progress_text = scrolledtext.ScrolledText(frame, height=15, wrap=tk.WORD)
            progress_text.pack(fill=tk.BOTH, expand=True, pady=10)
            progress_text.insert(tk.END, "Starting import...\n")
            
            # Progress bar
            progress_bar = ttk.Progressbar(frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
            progress_bar.pack(fill=tk.X, pady=10)
            
            # Status label
            status_label = ttk.Label(frame, text="Reading file...")
            status_label.pack(anchor=tk.W, pady=5)
            
            # Close button (disabled during import)
            close_button = ttk.Button(frame, text="Close", command=import_window.destroy, state=tk.DISABLED)
            close_button.pack(side=tk.RIGHT, pady=10)
            
            # Update GUI
            import_window.update()
            
            # Run import in thread
            threading.Thread(target=self.perform_import, 
                           args=(file_path, progress_text, progress_bar, status_label, close_button, import_window)).start()
            
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import statements: {str(e)}")
            log_error("Import past statements error", e)

    def perform_import(self, file_path, progress_text, progress_bar, status_label, close_button, window):
        """Perform the actual import operation"""
        try:
            # Read CSV file
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                
                # Get header row
                headers = next(reader)
                
                # Try to map columns
                col_map = {}
                required_cols = ['text', 'topic']
                
                for i, header in enumerate(headers):
                    header_lower = header.lower().strip()
                    
                    if 'text' in header_lower or 'statement' in header_lower or 'content' in header_lower:
                        col_map['text'] = i
                    elif 'topic' in header_lower or 'subject' in header_lower or 'category' in header_lower:
                        col_map['topic'] = i
                    elif 'tone' in header_lower:
                        col_map['tone'] = i
                    elif 'date' in header_lower or 'time' in header_lower:
                        col_map['timestamp'] = i
                    elif 'source' in header_lower:
                        col_map['source'] = i
                    elif 'tag' in header_lower:
                        col_map['tags'] = i
                
                # Validate required columns
                missing = [col for col in required_cols if col not in col_map]
                if missing:
                    window.after(0, lambda: [
                        progress_text.insert(tk.END, f"Error: Missing required columns: {', '.join(missing)}\n"),
                        progress_text.see(tk.END),
                        status_label.config(text="Import failed: Missing required columns"),
                        close_button.config(state=tk.NORMAL)
                    ])
                    return
                
                # Read all rows to get count
                all_rows = list(reader)
                total_rows = len(all_rows)
                
                window.after(0, lambda: [
                    progress_text.insert(tk.END, f"Found {total_rows} statements to import\n"),
                    progress_text.see(tk.END),
                    progress_bar.config(maximum=total_rows)
                ])
                
                # Connect to database
                conn = sqlite3.connect('mp_rewriter.db')
                cursor = conn.cursor()
                
                # Process each row
                success_count = 0
                error_count = 0
                
                for i, row in enumerate(all_rows):
                    try:
                        # Extract data using column mapping
                        text = row[col_map['text']] if 'text' in col_map and len(row) > col_map['text'] else None
                        topic = row[col_map['topic']] if 'topic' in col_map and len(row) > col_map['topic'] else None
                        tone = row[col_map['tone']] if 'tone' in col_map and len(row) > col_map['tone'] else None
                        timestamp = row[col_map['timestamp']] if 'timestamp' in col_map and len(row) > col_map['timestamp'] else None
                        source = row[col_map['source']] if 'source' in col_map and len(row) > col_map['source'] else "Imported"
                        tags = row[col_map['tags']] if 'tags' in col_map and len(row) > col_map['tags'] else None
                        
                        # Skip empty rows
                        if not text or not text.strip():
                            window.after(0, lambda i=i: [
                                progress_text.insert(tk.END, f"Skipping row {i+1}: Empty text\n"),
                                progress_text.see(tk.END),
                                progress_bar.step(1)
                            ])
                            continue
                        
                        # Insert into database
                        cursor.execute("""
                        INSERT INTO past_responses (published_text, topic, tone, timestamp, source, tags)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """, (text, topic, tone, timestamp, source, tags))
                        
                        success_count += 1
                        
                        # Update progress every 10 rows
                        if i % 10 == 0 or i == total_rows - 1:
                            window.after(0, lambda i=i, sc=success_count: [
                                progress_text.insert(tk.END, f"Imported {sc} statements so far... ({i+1}/{total_rows})\n"),
                                progress_text.see(tk.END),
                                progress_bar.step(10 if i % 10 == 0 else i % 10),
                                status_label.config(text=f"Importing... ({i+1}/{total_rows})")
                            ])
                            
                    except Exception as e:
                        error_count += 1
                        window.after(0, lambda i=i, e=str(e): [
                            progress_text.insert(tk.END, f"Error in row {i+1}: {e}\n"),
                            progress_text.see(tk.END),
                            progress_bar.step(1)
                        ])
                
                # Commit changes
                conn.commit()
                conn.close()
                
                # Final update
                window.after(0, lambda: [
                    progress_text.insert(tk.END, f"\nImport completed:\n- {success_count} statements imported successfully\n- {error_count} errors encountered\n"),
                    progress_text.see(tk.END),
                    status_label.config(text=f"Import completed: {success_count} statements imported"),
                    close_button.config(state=tk.NORMAL)
                ])
                
        except Exception as e:
            window.after(0, lambda: [
                progress_text.insert(tk.END, f"Import failed: {str(e)}\n"),
                progress_text.see(tk.END),
                status_label.config(text="Import failed"),
                close_button.config(state=tk.NORMAL)
            ])
            log_error("Import execution error", e)

    def open_settings(self):
        """Open settings dialog"""
        try:
            settings_window = tk.Toplevel(self.root)
            settings_window.title("Settings")
            settings_window.geometry("500x400")
            settings_window.minsize(400, 300)
            settings_window.grab_set()  # Modal dialog
            
            notebook = ttk.Notebook(settings_window)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # API Settings tab
            api_tab = ttk.Frame(notebook)
            notebook.add(api_tab, text="API Settings")
            
            api_frame = ttk.Frame(api_tab, padding=10)
            api_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(api_frame, text="OpenAI API Key:", style='Header.TLabel').grid(row=0, column=0, sticky=tk.W, pady=(10, 5))
            
            # Load current API key
            import configparser
            config = configparser.ConfigParser()
            config.read('config.ini')
            current_key = config['API']['OPENAI_API_KEY'] if 'API' in config and 'OPENAI_API_KEY' in config['API'] else ''
            
            # If it's the actual key, mask it
            masked_key = "•" * 20 + current_key[-5:] if current_key and current_key != 'your_api_key_here' else ''
            
            api_key_var = tk.StringVar(value=masked_key)
            api_key_entry = ttk.Entry(api_frame, textvariable=api_key_var, width=40, show="•")
            api_key_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
            
            show_key_var = tk.BooleanVar(value=False)
            show_key_check = ttk.Checkbutton(api_frame, text="Show Key", variable=show_key_var, 
                                           command=lambda: api_key_entry.config(show="" if show_key_var.get() else "•"))
            show_key_check.grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
            
            ttk.Label(api_frame, text="LLM Model:").grid(row=3, column=0, sticky=tk.W, pady=(10, 5))
            
            model_var = tk.StringVar(value="gpt-4o")  # Updated default model
            model_options = ["gpt-4o", "gpt-4o-mini"]  # Updated model options
            model_dropdown = ttk.Combobox(api_frame, textvariable=model_var, values=model_options, state="readonly")
            model_dropdown.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
            
            ttk.Button(api_frame, text="Save API Settings", 
                      command=lambda: save_api_settings(api_key_entry.get(), model_var.get(), settings_window)).grid(row=5, column=0, pady=20)
            
            # UI Settings tab
            ui_tab = ttk.Frame(notebook)
            notebook.add(ui_tab, text="UI Settings")
            
            ui_frame = ttk.Frame(ui_tab, padding=10)
            ui_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(ui_frame, text="Default Tone:").grid(row=0, column=0, sticky=tk.W, pady=(10, 5))
            
            default_tone_var = tk.StringVar(value=self.tone_options[0])
            default_tone_dropdown = ttk.Combobox(ui_frame, textvariable=default_tone_var, values=self.tone_options, state="readonly")
            default_tone_dropdown.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
            
            # Buttons at bottom
            button_frame = ttk.Frame(settings_window)
            button_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Button(button_frame, text="Close", command=settings_window.destroy).pack(side=tk.RIGHT)
        except Exception as e:
            messagebox.showerror("Settings Error", f"Failed to open settings: {str(e)}")
            log_error("Open settings error", e)

    def show_user_guide(self):
        """Show the user guide"""
        try:
            guide_window = tk.Toplevel(self.root)
            guide_window.title("User Guide")
            guide_window.geometry("800x600")
            guide_window.minsize(700, 500)
            
            frame = ttk.Frame(guide_window, padding=10)
            frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(frame, text="MP Statement Rewriter - User Guide", font=('Segoe UI', 16, 'bold')).pack(anchor=tk.W, pady=(0, 20))
            
            text_widget = scrolledtext.ScrolledText(frame, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True, pady=10)
            
            guide_text = """
# Quick Start Guide

## Basic Workflow

1. **Enter Input Data**
   - Paste the raw government statement in the left panel
   - Add relevant local context and target audience information
   - Select the appropriate tone from the dropdown menu

2. **Generate Statement**
   - Click "Generate Rewritten Statement" to process your inputs
   - The application will retrieve past statements and create a new version

3. **Review & Refine**
   - Review the generated statement in the right panel
   - Click "Regenerate" for alternative versions
   - Click "Edit" to make manual changes

4. **Save Your Work**
   - Click "Accept & Save" when satisfied
   - The statement will be saved to the database for future reference

## Tips for Better Results

- **Provide Rich Context**: The more specific your local context, the more tailored the output.
- **Be Specific About Audience**: Define your audience clearly (e.g., "parents of primary school children" vs. just "parents").
- **Try Different Tones**: Experiment with different tone options to find the right voice.
- **Edit When Needed**: Don't hesitate to use the Edit button to make final adjustments.
- **Build Your Library**: Each accepted statement improves future generations.

## Advanced Features

- **View History**: Access past submissions from the View menu
- **Export**: Save statements to text files or copy to clipboard
- **Import Past Statements**: Add previously published statements via CSV
- **Settings**: Configure API settings and defaults

For more detailed information, refer to the full documentation provided with the application.
"""
            
            text_widget.insert(tk.END, guide_text)
            text_widget.config(state=tk.DISABLED)
            
            button_frame = ttk.Frame(frame)
            button_frame.pack(fill=tk.X, pady=10)
            
            ttk.Button(button_frame, text="Close", command=guide_window.destroy).pack(side=tk.RIGHT)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show user guide: {str(e)}")
            log_error("Show user guide error", e)

    def show_about(self):
        """Show the about dialog"""
        try:
            about_window = tk.Toplevel(self.root)
            about_window.title("About")
            about_window.geometry("400x300")
            about_window.resizable(False, False)
            
            frame = ttk.Frame(about_window, padding=20)
            frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(frame, text="MP Statement Rewriter", font=('Segoe UI', 16, 'bold')).pack(pady=(0, 5))
            ttk.Label(frame, text="Version 1.2.0").pack(pady=(0, 20))
            
            ttk.Label(frame, text="An AI-powered tool for transforming government statements into", wraplength=350).pack()
            ttk.Label(frame, text="personalized communications that maintain your MP's voice.", wraplength=350).pack(pady=(0, 20))
            
            ttk.Label(frame, text="© 2025 All rights reserved", font=('Segoe UI', 8)).pack(side=tk.BOTTOM, pady=10)
            
            ttk.Button(frame, text="Close", command=about_window.destroy).pack(side=tk.BOTTOM, pady=10)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show about dialog: {str(e)}")
            log_error("Show about dialog error", e)

    def submit(self):
        """Handle the submit button click event"""
        try:
            # Get input values
            raw_text = self.raw_statement.get("1.0", tk.END).strip()
            context = self.context.get().strip()
            audience = self.target_audience.get().strip()
            tone = self.tone_var.get()
            notes = self.notes.get().strip()
            
            # Validate inputs
            if not raw_text:
                messagebox.showwarning("Input Required", "Please enter the raw government statement.")
                return
            
            # Update status
            self.status_var.set("Generating rewritten statement...")
            self.progress.grid()
            self.progress.start(10)
            
            # Disable buttons while processing
            self.accept_button.config(state=tk.DISABLED)
            self.refresh_button.config(state=tk.DISABLED)
            self.edit_button.config(state=tk.DISABLED)
            self.copy_button.config(state=tk.DISABLED)
            
            # Use threading to prevent UI freeze
            threading.Thread(target=self.process_submission, args=(raw_text, context, audience, tone, notes)).start()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to submit: {str(e)}")
            log_error("Submit error", e)
            self.progress.stop()
            self.progress.grid_remove()
            self.status_var.set("Error during submission.")

    def process_submission(self, raw_text, context, audience, tone, notes):
        """Process the submission in a separate thread"""
        try:
            # Retrieve past statements
            accepted_responses = get_past_responses(status="accepted", limit=3)
            rejected_responses = get_past_responses(status="rejected", limit=2)
            
            # Construct prompt
            prompt = construct_prompt(raw_text, context, audience, tone, accepted_responses, rejected_responses)
            
            # Call the LLM API
            generated_text = self.api_manager.call_llm_api(prompt)
            
            # Log the submission
            self.current_submission_id = log_submission(raw_text, context, audience, tone, generated_text, notes)
            
            # Update UI
            self.root.after(0, self.update_ui_with_generation, generated_text)
            
        except Exception as e:
            self.root.after(0, lambda: self.handle_error(f"Error during generation: {str(e)}"))
            log_error("Process submission error", e)

    def update_ui_with_generation(self, generated_text):
        """Update the UI with the generated text"""
        try:
            # Update the output text box
            self.generated_statement.delete("1.0", tk.END)
            self.generated_statement.insert(tk.END, generated_text)
            
            # Update word count
            self.update_generated_word_count()
            
            # Hide progress bar
            self.progress.stop()
            self.progress.grid_remove()
            
            # Enable action buttons
            self.accept_button.config(state=tk.NORMAL)
            self.refresh_button.config(state=tk.NORMAL)
            self.edit_button.config(state=tk.NORMAL)
            self.copy_button.config(state=tk.NORMAL)
            
            # Update status
            self.status_var.set("Statement generated. Please review and accept or regenerate.")
        except Exception as e:
            self.handle_error(f"Error updating UI: {str(e)}")
            log_error("Update UI error", e)

    def handle_error(self, error_message):
        """Handle errors and update UI accordingly"""
        try:
            # Hide progress bar
            self.progress.stop()
            self.progress.grid_remove()
            
            messagebox.showerror("Error", error_message)
            self.status_var.set("Error occurred. Please try again.")
        except Exception as e:
            log_error("Error handler error", e)

    def accept_statement(self):
        """Handle the accept button click event"""
        if not self.current_submission_id:
            messagebox.showwarning("No Submission", "No statement has been generated yet.")
            return
        
        try:
            # Update submission status to 'accepted'
            update_submission_status(self.current_submission_id, 'accepted')
            
            # Get the accepted text and metadata to add to past_responses
            conn = sqlite3.connect('mp_rewriter.db')
            cursor = conn.cursor()
            
            # Get the accepted text and metadata
            cursor.execute("""
            SELECT generated_text, target_audience, tone, context 
            FROM submissions 
            WHERE id = ?
            """, (self.current_submission_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                generated_text, audience, tone, context = result
                
                # Determine topic from context/audience
                topic = context if context else audience
                
                # Add to past_responses
                save_accepted_statement(self.current_submission_id, generated_text, topic, tone)
            
            # Update status
            self.status_var.set("Statement accepted and saved to your library.")
            
            # Disable action buttons
            self.accept_button.config(state=tk.DISABLED)
            self.refresh_button.config(state=tk.DISABLED)
            
            # Show success message with options
            response = messagebox.askyesnocancel(
                "Statement Accepted", 
                "The statement has been saved to your library.\n\nWould you like to start a new statement?",
                icon=messagebox.INFO
            )
            
            if response is True:  # Yes
                self.clear_all_fields()
            elif response is False:  # No
                # Keep current content but clear submission ID
                self.current_submission_id = None
                self.generated_statement.config(state=tk.NORMAL)
            
            return True
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to accept statement: {str(e)}")
            log_error("Accept statement error", e)
            return False

    def refresh_statement(self):
        """Handle the refresh button click event"""
        if not self.current_submission_id:
            messagebox.showwarning("No Submission", "No statement has been generated yet.")
            return
        
        try:
            # Mark current submission as rejected
            update_submission_status(self.current_submission_id, 'rejected')
            
            # Get original inputs for regeneration
            raw_text = self.raw_statement.get("1.0", tk.END).strip()
            context = self.context.get().strip()
            audience = self.target_audience.get().strip()
            tone = self.tone_var.get()
            notes = self.notes.get().strip()
            
            # Update status and show progress
            self.status_var.set("Regenerating statement with new approach...")
            self.progress.grid()
            self.progress.start(10)
            
            # Disable buttons while processing
            self.accept_button.config(state=tk.DISABLED)
            self.refresh_button.config(state=tk.DISABLED)
            self.edit_button.config(state=tk.DISABLED)
            self.copy_button.config(state=tk.DISABLED)
            
            # Regenerate with slightly higher temperature for diversity
            threading.Thread(target=self.process_refresh, args=(raw_text, context, audience, tone, notes)).start()
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to refresh statement: {str(e)}")
            log_error("Refresh statement error", e)

    def process_refresh(self, raw_text, context, audience, tone, notes):
        """Process the refresh in a separate thread"""
        try:
            # Get the most recently rejected statement to explicitly avoid
            conn = sqlite3.connect('mp_rewriter.db')
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT generated_text FROM submissions 
            WHERE id = ? 
            LIMIT 1
            """, (self.current_submission_id,))
            
            rejected_text = cursor.fetchone()
            
            # Get examples of good statements
            cursor.execute("""
            SELECT published_text, topic, tone FROM past_responses 
            ORDER BY RANDOM() 
            LIMIT 3
            """)
            
            good_examples = cursor.fetchall()
            
            # Get another rejected statement
            cursor.execute("""
            SELECT generated_text, target_audience, tone FROM submissions 
            WHERE status = 'rejected' AND id != ? 
            ORDER BY RANDOM() 
            LIMIT 1
            """, (self.current_submission_id,))
            
            other_rejected = cursor.fetchall()
            
            conn.close()
            
            # Create an explicit rejection example
            rejected_examples = []
            if rejected_text:
                rejected_examples.append((rejected_text[0], f"Previous attempt for {audience}", tone))
            
            # Add other rejected examples
            rejected_examples.extend(other_rejected)
            
            # Construct a refresh prompt
            prompt = construct_refresh_prompt(raw_text, context, audience, tone, good_examples, rejected_examples)
            
            # Call the LLM API with higher temperature
            generated_text = self.api_manager.call_refresh_llm_api(prompt)
            
            # Log as a new submission
            self.current_submission_id = log_submission(raw_text, context, audience, tone, generated_text, notes)
            
            # Update UI
            self.root.after(0, self.update_ui_with_generation, generated_text)
            
        except Exception as e:
            self.root.after(0, lambda: self.handle_error(f"Error during regeneration: {str(e)}"))
            log_error("Process refresh error", e)