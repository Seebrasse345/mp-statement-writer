import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import sqlite3
import os
import datetime
import random
import json
import configparser
import threading
import re
import csv
from io import StringIO
import traceback
import sys

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
        
        # Initialize instance variables
        self.raw_statement = None
        self.context = None
        self.target_audience = None
        self.tone_dropdown = None
        self.notes = None
        self.generated_statement = None
        self.accept_button = None
        self.refresh_button = None
        self.edit_button = None
        self.copy_button = None
        self.progress = None
        
        # Current submission ID
        self.current_submission_id = None
        
        # History window reference
        self.history_window = None
        
        # Set application icon if available
        try:
            if os.path.exists("icon.ico"):
                self.root.iconbitmap("icon.ico")
        except:
            pass  # Ignore if icon setting fails
        
        # Define tone options
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
        self.initialize_database()
        
        # Initialize OpenAI API
        self.initialize_openai()
        
        # Set up style
        self.setup_styles()
        
        # Create UI elements
        self.create_ui()
        
        # Load sample data if needed (moved after database initialization)
        threading.Thread(target=populate_sample_data).start()

    def setup_styles(self):
        """Set up ttk styles for better UI appearance"""
        style = ttk.Style()
        
        # Configure colors based on system
        if os.name == 'nt':  # Windows
            style.theme_use('vista')
        else:
            try:
                style.theme_use('clam')
            except:
                pass
        
        # Configure button styles
        style.configure('Primary.TButton', 
                        font=('Segoe UI', 10, 'bold'),
                        background='#0078D7')
        
        style.configure('Secondary.TButton',
                        font=('Segoe UI', 10))
        
        # Configure label styles
        style.configure('Header.TLabel',
                        font=('Segoe UI', 12, 'bold'))
        
        style.configure('Subheader.TLabel',
                        font=('Segoe UI', 10, 'italic'))
        
        # Configure frame styles
        style.configure('Card.TFrame', 
                        background='#f5f5f5',
                        relief='raised')

    def initialize_openai(self):
        """Initialize OpenAI API with key from config file"""
        try:
            import openai
            self.openai = openai
            
            config = configparser.ConfigParser()
            
            # Check if config file exists, if not create it
            if not os.path.exists('config.ini'):
                config['API'] = {
                    'OPENAI_API_KEY': 'your_api_key_here',
                    'MODEL': 'gpt-4o'  # Updated model to gpt-4o
                }
                with open('config.ini', 'w') as f:
                    config.write(f)
                messagebox.showwarning(
                    "API Key Required", 
                    "Please edit the config.ini file and add your OpenAI API key."
                )
            
            config.read('config.ini')
            
            if 'API' not in config:
                config['API'] = {
                    'OPENAI_API_KEY': 'your_api_key_here',
                    'MODEL': 'gpt-4o'  # Updated model to gpt-4o
                }
                with open('config.ini', 'w') as f:
                    config.write(f)
            
            api_key = config['API']['OPENAI_API_KEY']
            
            if api_key == 'your_api_key_here':
                messagebox.showwarning(
                    "API Key Required", 
                    "Please edit the config.ini file and add your OpenAI API key."
                )
            
            openai.api_key = api_key
        except ImportError:
            messagebox.showerror("Missing Dependency", 
                                "The openai package is not installed. Please run: pip install openai")
        except Exception as e:
            messagebox.showerror("API Error", f"Failed to initialize OpenAI API: {str(e)}")
            log_error("OpenAI initialization error", e)

    def initialize_database(self):
        """Create database tables if they don't exist"""
        try:
            conn = sqlite3.connect('mp_rewriter.db')
            cursor = conn.cursor()
            
            # Create submissions table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_text TEXT NOT NULL,
                context TEXT,
                target_audience TEXT,
                tone TEXT,
                generated_text TEXT,
                status TEXT DEFAULT 'pending',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
            ''')
            
            # Create past_responses table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS past_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                published_text TEXT NOT NULL,
                topic TEXT,
                tone TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                source TEXT,
                tags TEXT
            )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to initialize database: {str(e)}")
            log_error("Database initialization error", e)

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
            
            # Configure the input panel
            self.configure_input_panel(left_frame)
            
            # Configure the output panel
            self.configure_output_panel(right_frame)
            
            # Menu bar
            self.create_menu()
            
            # Status bar
            status_frame = ttk.Frame(self.root)
            status_frame.pack(side=tk.BOTTOM, fill=tk.X)
            
            status_bar = ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
            status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Version info
            version_label = ttk.Label(status_frame, text="v1.2.0", relief=tk.SUNKEN, anchor=tk.E)
            version_label.pack(side=tk.RIGHT, padx=5)
        except Exception as e:
            messagebox.showerror("UI Error", f"Failed to create UI: {str(e)}")
            log_error("UI creation error", e)

    def create_menu(self):
        """Create the application menu"""
        try:
            menubar = tk.Menu(self.root)
            
            # File menu
            file_menu = tk.Menu(menubar, tearoff=0)
            file_menu.add_command(label="New", command=self.clear_all_fields)
            file_menu.add_command(label="Export Statement", command=self.export_statement)
            file_menu.add_separator()
            file_menu.add_command(label="Exit", command=self.root.quit)
            menubar.add_cascade(label="File", menu=file_menu)
            
            # View menu
            view_menu = tk.Menu(menubar, tearoff=0)
            view_menu.add_command(label="Submission History", command=self.open_history)
            view_menu.add_command(label="Past Approved Statements", command=self.view_approved_statements)
            menubar.add_cascade(label="View", menu=view_menu)
            
            # Tools menu
            tools_menu = tk.Menu(menubar, tearoff=0)
            tools_menu.add_command(label="Import Past Statements", command=self.import_past_statements)
            tools_menu.add_command(label="Settings", command=self.open_settings)
            menubar.add_cascade(label="Tools", menu=tools_menu)
            
            # Help menu
            help_menu = tk.Menu(menubar, tearoff=0)
            help_menu.add_command(label="User Guide", command=self.show_user_guide)
            help_menu.add_command(label="About", command=self.show_about)
            menubar.add_cascade(label="Help", menu=help_menu)
            
            self.root.config(menu=menubar)
        except Exception as e:
            messagebox.showerror("Menu Error", f"Failed to create menu: {str(e)}")
            log_error("Menu creation error", e)

    def configure_input_panel(self, parent):
        """Set up the input panel with all needed fields"""
        try:
            # Frame for input fields
            input_frame = ttk.Frame(parent)
            input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Raw Statement
            ttk.Label(input_frame, text="Raw Government Statement:", style='Header.TLabel').grid(row=0, column=0, sticky=tk.W, pady=(10, 5))
            ttk.Label(input_frame, text="Enter the original statement that needs to be rewritten", style='Subheader.TLabel').grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
            
            self.raw_statement = scrolledtext.ScrolledText(input_frame, height=10, wrap=tk.WORD)
            self.raw_statement.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))
            self.raw_statement.bind('<KeyRelease>', self.update_raw_word_count)
            
            # Word count for raw statement
            ttk.Label(input_frame, textvariable=self.raw_word_count).grid(row=3, column=0, sticky=tk.E, pady=(0, 10))
            
            # Context
            ttk.Label(input_frame, text="Local Context:", style='Header.TLabel').grid(row=4, column=0, sticky=tk.W, pady=(10, 5))
            ttk.Label(input_frame, text="Include relevant local issues, constituency concerns, or personal campaign history", style='Subheader.TLabel').grid(row=5, column=0, sticky=tk.W, pady=(0, 5))
            
            self.context = ttk.Entry(input_frame, width=50)
            self.context.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
            
            # Target Audience
            ttk.Label(input_frame, text="Target Audience:", style='Header.TLabel').grid(row=7, column=0, sticky=tk.W, pady=(10, 5))
            ttk.Label(input_frame, text="Specify who will be reading this communication", style='Subheader.TLabel').grid(row=8, column=0, sticky=tk.W, pady=(0, 5))
            
            self.target_audience = ttk.Entry(input_frame, width=50)
            self.target_audience.grid(row=9, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
            
            # Tone Selection
            ttk.Label(input_frame, text="Communication Tone:", style='Header.TLabel').grid(row=10, column=0, sticky=tk.W, pady=(10, 5))
            ttk.Label(input_frame, text="Select the appropriate tone for this message", style='Subheader.TLabel').grid(row=11, column=0, sticky=tk.W, pady=(0, 5))
            
            self.tone_var = tk.StringVar()
            self.tone_dropdown = ttk.Combobox(input_frame, textvariable=self.tone_var, values=self.tone_options, state="readonly")
            self.tone_dropdown.current(0)  # Set default tone
            self.tone_dropdown.grid(row=12, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
            
            # Notes/Tags
            ttk.Label(input_frame, text="Additional Notes (optional):", style='Header.TLabel').grid(row=13, column=0, sticky=tk.W, pady=(10, 5))
            
            self.notes = ttk.Entry(input_frame, width=50)
            self.notes.grid(row=14, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
            
            # Submit Button
            button_frame = ttk.Frame(input_frame)
            button_frame.grid(row=15, column=0, sticky=tk.E, pady=20)
            
            clear_button = ttk.Button(button_frame, text="Clear Form", command=self.clear_all_fields, style='Secondary.TButton')
            clear_button.pack(side=tk.LEFT, padx=5)
            
            submit_button = ttk.Button(button_frame, text="Generate Rewritten Statement", command=self.submit, style='Primary.TButton')
            submit_button.pack(side=tk.LEFT)
            
            # Configure grid weights
            input_frame.grid_columnconfigure(0, weight=1)
            for i in range(16):
                input_frame.grid_rowconfigure(i, weight=0)
            input_frame.grid_rowconfigure(2, weight=3)  # Give more weight to raw statement
        except Exception as e:
            messagebox.showerror("UI Error", f"Failed to configure input panel: {str(e)}")
            log_error("Input panel configuration error", e)

    def configure_output_panel(self, parent):
        """Set up the output panel with the generated text and action buttons"""
        try:
            # Frame for output and buttons
            output_frame = ttk.Frame(parent)
            output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Generated Statement
            ttk.Label(output_frame, text="Rewritten Statement:", style='Header.TLabel').grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
            ttk.Label(output_frame, text="AI-generated response in the MP's voice", style='Subheader.TLabel').grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
            
            self.generated_statement = scrolledtext.ScrolledText(output_frame, height=20, wrap=tk.WORD)
            self.generated_statement.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))
            self.generated_statement.bind('<KeyRelease>', self.update_generated_word_count)
            
            # Word count for generated statement
            ttk.Label(output_frame, textvariable=self.generated_word_count).grid(row=3, column=0, sticky=tk.W, pady=(0, 10))
            
            # Feedback section
            ttk.Label(output_frame, text="Feedback on Generated Statement:", style='Header.TLabel').grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
            
            # Progress bar for generation
            self.progress = ttk.Progressbar(output_frame, orient=tk.HORIZONTAL, length=100, mode='indeterminate')
            self.progress.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
            self.progress.grid_remove()  # Hide initially
            
            # Action Buttons
            button_frame = ttk.Frame(output_frame)
            button_frame.grid(row=6, column=0, columnspan=3, sticky=tk.E, pady=10)
            
            self.edit_button = ttk.Button(button_frame, text="Edit", command=self.enable_editing, state=tk.DISABLED)
            self.edit_button.pack(side=tk.LEFT, padx=5)
            
            self.refresh_button = ttk.Button(button_frame, text="Regenerate", command=self.refresh_statement, state=tk.DISABLED)
            self.refresh_button.pack(side=tk.LEFT, padx=5)
            
            self.accept_button = ttk.Button(button_frame, text="Accept & Save", command=self.accept_statement, state=tk.DISABLED, style='Primary.TButton')
            self.accept_button.pack(side=tk.LEFT, padx=5)
            
            # Copy button
            self.copy_button = ttk.Button(button_frame, text="Copy to Clipboard", command=self.copy_to_clipboard, state=tk.DISABLED)
            self.copy_button.pack(side=tk.LEFT, padx=5)
            
            # Configure grid weights
            output_frame.grid_columnconfigure(0, weight=1)
            output_frame.grid_columnconfigure(1, weight=1)
            output_frame.grid_columnconfigure(2, weight=1)
            
            for i in range(7):
                output_frame.grid_rowconfigure(i, weight=0)
            output_frame.grid_rowconfigure(2, weight=1)  # Give more weight to generated statement
        except Exception as e:
            messagebox.showerror("UI Error", f"Failed to configure output panel: {str(e)}")
            log_error("Output panel configuration error", e)

    def update_raw_word_count(self, event=None):
        """Update the word count for the raw statement text box"""
        try:
            text = self.raw_statement.get("1.0", tk.END).strip()
            word_count = len(re.findall(r'\b\w+\b', text))
            self.raw_word_count.set(f"Words: {word_count}")
        except Exception as e:
            log_error("Word count update error", e)

    def update_generated_word_count(self, event=None):
        """Update the word count for the generated statement text box"""
        try:
            text = self.generated_statement.get("1.0", tk.END).strip()
            word_count = len(re.findall(r'\b\w+\b', text))
            self.generated_word_count.set(f"Words: {word_count}")
        except Exception as e:
            log_error("Word count update error", e)

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
            text = self.generated_statement.get("1.0", tk.END).strip()
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
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
                
            self.history_window = tk.Toplevel(self.root)
            self.history_window.title("Submission History")
            self.history_window.geometry("900x600")
            self.history_window.minsize(800, 500)
            
            # Create treeview for submissions
            frame = ttk.Frame(self.history_window, padding=10)
            frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(frame, text="Recent Submissions", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 10))
            
            columns = ('id', 'timestamp', 'status', 'audience', 'tone', 'preview')
            tree = ttk.Treeview(frame, columns=columns, show='headings')
            
            # Define headings
            tree.heading('id', text='ID')
            tree.heading('timestamp', text='Date & Time')
            tree.heading('status', text='Status')
            tree.heading('audience', text='Audience')
            tree.heading('tone', text='Tone')
            tree.heading('preview', text='Preview')
            
            # Define columns
            tree.column('id', width=50, anchor=tk.CENTER)
            tree.column('timestamp', width=150, anchor=tk.W)
            tree.column('status', width=100, anchor=tk.CENTER)
            tree.column('audience', width=150, anchor=tk.W)
            tree.column('tone', width=150, anchor=tk.W)
            tree.column('preview', width=280, anchor=tk.W)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscroll=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            tree.pack(fill=tk.BOTH, expand=True)
            
            # Add a search frame
            search_frame = ttk.Frame(frame)
            search_frame.pack(fill=tk.X, pady=10)
            
            ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
            search_entry = ttk.Entry(search_frame, width=30)
            search_entry.pack(side=tk.LEFT, padx=5)
            
            search_by = tk.StringVar()
            search_by.set("All Fields")
            ttk.OptionMenu(search_frame, search_by, "All Fields", "Content", "Audience", "Status", "Tone").pack(side=tk.LEFT, padx=5)
            
            ttk.Button(search_frame, text="Search", command=lambda: self.search_submissions(tree, search_entry.get(), search_by.get())).pack(side=tk.LEFT, padx=5)
            ttk.Button(search_frame, text="Clear", command=lambda: [search_entry.delete(0, tk.END), self.load_submissions(tree)]).pack(side=tk.LEFT)
            
            # Buttons frame
            buttons_frame = ttk.Frame(frame)
            buttons_frame.pack(fill=tk.X, pady=10)
            
            ttk.Button(buttons_frame, text="View Details", command=lambda: self.view_submission_details(tree.item(tree.focus())['values'][0] if tree.focus() else None)).pack(side=tk.LEFT, padx=5)
            ttk.Button(buttons_frame, text="Load to Editor", command=lambda: self.load_submission_to_editor(tree.item(tree.focus())['values'][0] if tree.focus() else None)).pack(side=tk.LEFT, padx=5)
            ttk.Button(buttons_frame, text="Refresh", command=lambda: self.load_submissions(tree)).pack(side=tk.LEFT, padx=5)
            ttk.Button(buttons_frame, text="Close", command=self.history_window.destroy).pack(side=tk.RIGHT)
            
            # Load submissions
            self.load_submissions(tree)
            
            # Double-click to view details
            tree.bind("<Double-1>", lambda event: self.view_submission_details(tree.item(tree.focus())['values'][0] if tree.focus() else None))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open history: {str(e)}")
            log_error("Open history error", e)

    def load_submissions(self, tree):
        """Load submissions into the treeview"""
        try:
            # Clear existing items
            for item in tree.get_children():
                tree.delete(item)
                
            conn = sqlite3.connect('mp_rewriter.db')
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT id, timestamp, status, target_audience, tone, original_text, generated_text 
            FROM submissions
            ORDER BY timestamp DESC
            LIMIT 100
            """)
            
            for row in cursor.fetchall():
                id, timestamp, status, audience, tone, original, generated = row
                
                # Format the timestamp
                try:
                    dt = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    formatted_time = dt.strftime("%d %b %Y, %H:%M")
                except:
                    formatted_time = timestamp
                
                # Preview of original text (first 30 chars)
                preview = original[:50] + "..." if original and len(original) > 50 else original
                
                tree.insert('', tk.END, values=(id, formatted_time, status, audience, tone, preview))
                
            conn.close()
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load submissions: {str(e)}")
            log_error("Load submissions error", e)

    def search_submissions(self, tree, search_text, search_field):
        """Search submissions based on criteria"""
        try:
            # Clear existing items
            for item in tree.get_children():
                tree.delete(item)
                
            if not search_text:
                self.load_submissions(tree)
                return
                
            conn = sqlite3.connect('mp_rewriter.db')
            cursor = conn.cursor()
            
            # Build query based on search field
            if search_field == "All Fields":
                query = """
                SELECT id, timestamp, status, target_audience, tone, original_text, generated_text 
                FROM submissions
                WHERE original_text LIKE ? OR generated_text LIKE ? OR target_audience LIKE ? OR status LIKE ? OR tone LIKE ?
                ORDER BY timestamp DESC
                """
                params = ('%' + search_text + '%',) * 5
            elif search_field == "Content":
                query = """
                SELECT id, timestamp, status, target_audience, tone, original_text, generated_text 
                FROM submissions
                WHERE original_text LIKE ? OR generated_text LIKE ?
                ORDER BY timestamp DESC
                """
                params = ('%' + search_text + '%', '%' + search_text + '%')
            else:
                # Map UI fields to database fields
                field_map = {
                    "Audience": "target_audience",
                    "Status": "status",
                    "Tone": "tone"
                }
                db_field = field_map.get(search_field, "target_audience")
                
                query = f"""
                SELECT id, timestamp, status, target_audience, tone, original_text, generated_text 
                FROM submissions
                WHERE {db_field} LIKE ?
                ORDER BY timestamp DESC
                """
                params = ('%' + search_text + '%',)
            
            cursor.execute(query, params)
            
            for row in cursor.fetchall():
                id, timestamp, status, audience, tone, original, generated = row
                
                # Format the timestamp
                try:
                    dt = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    formatted_time = dt.strftime("%d %b %Y, %H:%M")
                except:
                    formatted_time = timestamp
                
                # Preview of original text (first 30 chars)
                preview = original[:50] + "..." if original and len(original) > 50 else original
                
                tree.insert('', tk.END, values=(id, formatted_time, status, audience, tone, preview))
                
            conn.close()
            
        except Exception as e:
            messagebox.showerror("Search Error", f"Failed to search submissions: {str(e)}")
            log_error("Search submissions error", e)

    def view_submission_details(self, submission_id):
        """Show details of a specific submission"""
        try:
            if not submission_id:
                messagebox.showwarning("No Selection", "Please select a submission to view.")
                return
                
            conn = sqlite3.connect('mp_rewriter.db')
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT original_text, context, target_audience, tone, generated_text, status, timestamp, notes
            FROM submissions
            WHERE id = ?
            """, (submission_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                messagebox.showwarning("Not Found", f"Submission #{submission_id} not found.")
                return
                
            original, context, audience, tone, generated, status, timestamp, notes = result
            
            # Create detail window
            detail_window = tk.Toplevel(self.root)
            detail_window.title(f"Submission #{submission_id} Details")
            detail_window.geometry("800x600")
            detail_window.minsize(700, 500)
            
            main_frame = ttk.Frame(detail_window, padding=10)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Create a notebook (tab control)
            notebook = ttk.Notebook(main_frame)
            notebook.pack(fill=tk.BOTH, expand=True, pady=10)
            
            # Tab 1: Original Content
            tab1 = ttk.Frame(notebook)
            notebook.add(tab1, text="Original Input")
            
            # Original info
            info_frame = ttk.LabelFrame(tab1, text="Submission Information")
            info_frame.pack(fill=tk.X, padx=5, pady=5)
            
            info_grid = ttk.Frame(info_frame)
            info_grid.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Label(info_grid, text="Date:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Label(info_grid, text=timestamp).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
            
            ttk.Label(info_grid, text="Status:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Label(info_grid, text=status).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
            
            ttk.Label(info_grid, text="Audience:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Label(info_grid, text=audience).grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
            
            ttk.Label(info_grid, text="Tone:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Label(info_grid, text=tone).grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)
            
            ttk.Label(info_grid, text="Context:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Label(info_grid, text=context).grid(row=4, column=1, sticky=tk.W, padx=5, pady=2)
            
            ttk.Label(info_grid, text="Notes:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Label(info_grid, text=notes or "None").grid(row=5, column=1, sticky=tk.W, padx=5, pady=2)
            
            # Original text
            original_frame = ttk.LabelFrame(tab1, text="Raw Statement")
            original_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            original_text = scrolledtext.ScrolledText(original_frame, wrap=tk.WORD)
            original_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            original_text.insert(tk.END, original)
            original_text.config(state=tk.DISABLED)
            
            # Tab 2: Generated Content
            tab2 = ttk.Frame(notebook)
            notebook.add(tab2, text="Generated Output")
            
            # Generated text
            generated_frame = ttk.LabelFrame(tab2, text="Rewritten Statement")
            generated_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            generated_text = scrolledtext.ScrolledText(generated_frame, wrap=tk.WORD)
            generated_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            generated_text.insert(tk.END, generated)
            generated_text.config(state=tk.DISABLED)
            
            # Buttons
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=10)
            
            ttk.Button(button_frame, text="Load to Editor", 
                      command=lambda: [self.load_submission_to_editor(submission_id), detail_window.destroy()]).pack(side=tk.LEFT, padx=5)
                      
            ttk.Button(button_frame, text="Copy to Clipboard", 
                      command=lambda: [self.root.clipboard_clear(), self.root.clipboard_append(generated), 
                      messagebox.showinfo("Copied", "Generated text copied to clipboard")]).pack(side=tk.LEFT, padx=5)
                      
            ttk.Button(button_frame, text="Close", command=detail_window.destroy).pack(side=tk.RIGHT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load submission details: {str(e)}")
            log_error("View submission details error", e)

    def load_submission_to_editor(self, submission_id):
        """Load a submission from history into the editor"""
        try:
            if not submission_id:
                messagebox.showwarning("No Selection", "Please select a submission to load.")
                return
                
            conn = sqlite3.connect('mp_rewriter.db')
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT original_text, context, target_audience, tone, generated_text, notes
            FROM submissions
            WHERE id = ?
            """, (submission_id,))
            
            result = cursor.fetchone()
            conn.close()
            
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
            # Create window
            approved_window = tk.Toplevel(self.root)
            approved_window.title("Approved Past Statements")
            approved_window.geometry("900x600")
            approved_window.minsize(800, 500)
            
            # Create frame
            frame = ttk.Frame(approved_window, padding=10)
            frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(frame, text="Approved Statements Library", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 10))
            
            # Create treeview
            columns = ('id', 'timestamp', 'topic', 'tone', 'preview')
            tree = ttk.Treeview(frame, columns=columns, show='headings')
            
            # Define headings
            tree.heading('id', text='ID')
            tree.heading('timestamp', text='Date')
            tree.heading('topic', text='Topic')
            tree.heading('tone', text='Tone')
            tree.heading('preview', text='Preview')
            
            # Define columns
            tree.column('id', width=50, anchor=tk.CENTER)
            tree.column('timestamp', width=120, anchor=tk.W)
            tree.column('topic', width=150, anchor=tk.W)
            tree.column('tone', width=150, anchor=tk.W)
            tree.column('preview', width=400, anchor=tk.W)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscroll=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            tree.pack(fill=tk.BOTH, expand=True)
            
            # Load data
            conn = sqlite3.connect('mp_rewriter.db')
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT id, timestamp, topic, tone, published_text 
            FROM past_responses
            ORDER BY timestamp DESC
            """)
            
            for row in cursor.fetchall():
                id, timestamp, topic, tone, text = row
                
                # Format the timestamp
                try:
                    dt = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    formatted_time = dt.strftime("%d %b %Y")
                except:
                    formatted_time = timestamp
                
                # Preview of text
                preview = text[:50] + "..." if text and len(text) > 50 else text
                
                tree.insert('', tk.END, values=(id, formatted_time, topic or "General", tone or "Not specified", preview))
                
            conn.close()
            
            # Add search frame
            search_frame = ttk.Frame(frame)
            search_frame.pack(fill=tk.X, pady=10)
            
            ttk.Label(search_frame, text="Filter by:").pack(side=tk.LEFT)
            search_entry = ttk.Entry(search_frame, width=30)
            search_entry.pack(side=tk.LEFT, padx=5)
            
            search_by = tk.StringVar()
            search_by.set("All Fields")
            ttk.OptionMenu(search_frame, search_by, "All Fields", "Content", "Topic", "Tone").pack(side=tk.LEFT, padx=5)
            
            ttk.Button(search_frame, text="Search", command=lambda: self.search_approved(tree, search_entry.get(), search_by.get())).pack(side=tk.LEFT, padx=5)
            
            # Add buttons
            buttons_frame = ttk.Frame(frame)
            buttons_frame.pack(fill=tk.X, pady=10)
            
            ttk.Button(buttons_frame, text="View Full Statement", 
                      command=lambda: self.view_approved_details(tree.item(tree.focus())['values'][0] if tree.focus() else None)).pack(side=tk.LEFT, padx=5)
                      
            ttk.Button(buttons_frame, text="Close", command=approved_window.destroy).pack(side=tk.RIGHT)
            
            # Double-click to view details
            tree.bind("<Double-1>", lambda event: self.view_approved_details(tree.item(tree.focus())['values'][0] if tree.focus() else None))
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load approved statements: {str(e)}")
            log_error("View approved statements error", e)

    def search_approved(self, tree, search_text, search_field):
        """Search approved statements based on criteria"""
        try:
            # Clear existing items
            for item in tree.get_children():
                tree.delete(item)
                
            if not search_text:
                # Reload all
                conn = sqlite3.connect('mp_rewriter.db')
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT id, timestamp, topic, tone, published_text 
                FROM past_responses
                ORDER BY timestamp DESC
                """)
                
                for row in cursor.fetchall():
                    id, timestamp, topic, tone, text = row
                    
                    # Format the timestamp
                    try:
                        dt = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                        formatted_time = dt.strftime("%d %b %Y")
                    except:
                        formatted_time = timestamp
                    
                    # Preview of text
                    preview = text[:50] + "..." if text and len(text) > 50 else text
                    
                    tree.insert('', tk.END, values=(id, formatted_time, topic or "General", tone or "Not specified", preview))
                    
                conn.close()
                return
                
            conn = sqlite3.connect('mp_rewriter.db')
            cursor = conn.cursor()
            
            # Build query based on search field
            if search_field == "All Fields":
                query = """
                SELECT id, timestamp, topic, tone, published_text 
                FROM past_responses
                WHERE published_text LIKE ? OR topic LIKE ? OR tone LIKE ?
                ORDER BY timestamp DESC
                """
                params = ('%' + search_text + '%',) * 3
            elif search_field == "Content":
                query = """
                SELECT id, timestamp, topic, tone, published_text 
                FROM past_responses
                WHERE published_text LIKE ?
                ORDER BY timestamp DESC
                """
                params = ('%' + search_text + '%',)
            else:
                # Map UI fields to database fields
                field_map = {
                    "Topic": "topic",
                    "Tone": "tone"
                }
                db_field = field_map.get(search_field, "topic")
                
                query = f"""
                SELECT id, timestamp, topic, tone, published_text 
                FROM past_responses
                WHERE {db_field} LIKE ?
                ORDER BY timestamp DESC
                """
                params = ('%' + search_text + '%',)
            
            cursor.execute(query, params)
            
            for row in cursor.fetchall():
                id, timestamp, topic, tone, text = row
                
                # Format the timestamp
                try:
                    dt = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    formatted_time = dt.strftime("%d %b %Y")
                except:
                    formatted_time = timestamp
                
                # Preview of text
                preview = text[:50] + "..." if text and len(text) > 50 else text
                
                tree.insert('', tk.END, values=(id, formatted_time, topic or "General", tone or "Not specified", preview))
                
            conn.close()
            
        except Exception as e:
            messagebox.showerror("Search Error", f"Failed to search statements: {str(e)}")
            log_error("Search approved statements error", e)

    def view_approved_details(self, statement_id):
        """View details of an approved statement"""
        try:
            if not statement_id:
                messagebox.showwarning("No Selection", "Please select a statement to view.")
                return
                
            conn = sqlite3.connect('mp_rewriter.db')
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT published_text, topic, tone, timestamp, source, tags
            FROM past_responses
            WHERE id = ?
            """, (statement_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                messagebox.showwarning("Not Found", f"Statement #{statement_id} not found.")
                return
                
            text, topic, tone, timestamp, source, tags = result
            
            # Create detail window
            detail_window = tk.Toplevel(self.root)
            detail_window.title(f"Approved Statement #{statement_id}")
            detail_window.geometry("700x500")
            detail_window.minsize(600, 400)
            
            main_frame = ttk.Frame(detail_window, padding=10)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Info panel
            info_frame = ttk.LabelFrame(main_frame, text="Statement Information")
            info_frame.pack(fill=tk.X, padx=5, pady=5)
            
            info_grid = ttk.Frame(info_frame)
            info_grid.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Label(info_grid, text="Date:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Label(info_grid, text=timestamp).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
            
            ttk.Label(info_grid, text="Topic:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Label(info_grid, text=topic or "General").grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
            
            ttk.Label(info_grid, text="Tone:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Label(info_grid, text=tone or "Not specified").grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
            
            ttk.Label(info_grid, text="Source:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Label(info_grid, text=source or "Generated by application").grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)
            
            ttk.Label(info_grid, text="Tags:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Label(info_grid, text=tags or "None").grid(row=4, column=1, sticky=tk.W, padx=5, pady=2)
            
            # Text content
            text_frame = ttk.LabelFrame(main_frame, text="Statement Content")
            text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            text_widget = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_widget.insert(tk.END, text)
            text_widget.config(state=tk.DISABLED)
            
            # Buttons
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=10)
            
            ttk.Button(button_frame, text="Use as Template", 
                      command=lambda: [self.use_as_template(text), detail_window.destroy()]).pack(side=tk.LEFT, padx=5)
                      
            ttk.Button(button_frame, text="Copy to Clipboard", 
                      command=lambda: [self.root.clipboard_clear(), self.root.clipboard_append(text), 
                      messagebox.showinfo("Copied", "Statement copied to clipboard")]).pack(side=tk.LEFT, padx=5)
                      
            ttk.Button(button_frame, text="Close", command=detail_window.destroy).pack(side=tk.RIGHT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load statement details: {str(e)}")
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
                      command=lambda: self.save_api_settings(api_key_entry.get(), model_var.get(), settings_window)).grid(row=5, column=0, pady=20)
            
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

    def save_api_settings(self, api_key, model, window):
        """Save API settings to config file"""
        try:
            config = configparser.ConfigParser()
            
            # Load existing config
            if os.path.exists('config.ini'):
                config.read('config.ini')
            
            # Check if API section exists
            if 'API' not in config:
                config['API'] = {}
            
            # Update only if changed and not empty
            if api_key and not api_key.startswith('•'):
                config['API']['OPENAI_API_KEY'] = api_key
            
            # Update model
            config['API']['MODEL'] = model
            
            # Save config
            with open('config.ini', 'w') as f:
                config.write(f)
            
            # Update API key
            if api_key and not api_key.startswith('•'):
                self.openai.api_key = api_key
            
            messagebox.showinfo("Settings Saved", "API settings have been saved.")
            window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
            log_error("Save API settings error", e)

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
            accepted_responses = self.get_past_responses(status="accepted", limit=3)
            rejected_responses = self.get_past_responses(status="rejected", limit=2)
            
            # Construct prompt
            prompt = self.construct_prompt(raw_text, context, audience, tone, accepted_responses, rejected_responses)
            
            # Call the LLM API
            generated_text = self.call_llm_api(prompt)
            
            # Log the submission
            self.current_submission_id = self.log_submission(raw_text, context, audience, tone, generated_text, notes)
            
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

    def get_past_responses(self, status=None, limit=3):
        """Retrieve past responses from the database"""
        try:
            conn = sqlite3.connect('mp_rewriter.db')
            cursor = conn.cursor()
            
            if status == "accepted":
                # Get random past approved responses
                cursor.execute("""
                SELECT published_text, topic, tone FROM past_responses
                ORDER BY RANDOM()
                LIMIT ?
                """, (limit,))
                
                results = cursor.fetchall()
                
                # If we don't have enough from past_responses, get from accepted submissions
                if len(results) < limit:
                    cursor.execute("""
                    SELECT generated_text, target_audience, tone FROM submissions
                    WHERE status = 'accepted'
                    ORDER BY RANDOM()
                    LIMIT ?
                    """, (limit - len(results),))
                    
                    results.extend(cursor.fetchall())
                
            elif status == "rejected":
                # Get random rejected submissions
                cursor.execute("""
                SELECT generated_text, target_audience, tone FROM submissions
                WHERE status = 'rejected'
                ORDER BY RANDOM()
                LIMIT ?
                """, (limit,))
                
                results = cursor.fetchall()
                
            else:
                # Get mix of both
                cursor.execute("""
                SELECT published_text, topic, tone FROM past_responses
                ORDER BY RANDOM()
                LIMIT ?
                """, (limit // 2 + 1,))
                
                results = cursor.fetchall()
                
                cursor.execute("""
                SELECT generated_text, target_audience, tone FROM submissions
                WHERE status = 'accepted'
                ORDER BY RANDOM()
                LIMIT ?
                """, (limit // 2,))
                
                results.extend(cursor.fetchall())
            
            conn.close()
            
            # Return list of tuples (text, context/topic, tone)
            return results
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to retrieve past responses: {str(e)}")
            log_error("Get past responses error", e)
            return []
    
    def construct_prompt(self, raw_text, context, audience, tone, accepted_responses, rejected_responses=None):
        """Construct a prompt for the LLM that includes all necessary context"""
        try:
            # Get tone instructions
            tone_instructions = self.get_tone_instructions(tone)
            
            # Format accepted examples
            accepted_examples = ""
            if accepted_responses:
                accepted_examples = "## EXAMPLES TO EMULATE (these showcase the MP's voice and style):\n\n"
                for i, (response, topic, resp_tone) in enumerate(accepted_responses, 1):
                    accepted_examples += f"### Example {i} "
                    if resp_tone and resp_tone != "None":
                        accepted_examples += f"(Tone: {resp_tone})"
                    accepted_examples += f":\n\"{response}\"\n\n"
            
            # Format rejected examples
            rejected_examples = ""
            if rejected_responses and len(rejected_responses) > 0:
                rejected_examples = "## EXAMPLES TO AVOID (these were rejected or don't reflect the MP's voice well):\n\n"
                for i, (response, topic, resp_tone) in enumerate(rejected_responses, 1):
                    rejected_examples += f"### Bad Example {i}:\n\"{response}\"\n\n"
                    rejected_examples += f"Problem: This example doesn't fully capture the MP's voice, uses generic language, or lacks personal connection.\n\n"
            
            # Create the complete prompt
            prompt = f"""# MP STATEMENT REWRITING TASK

## OBJECTIVE:
Transform the government statement below into a personalized communication from the MP that feels authentic, locally relevant, and engaging to the specified audience. The rewritten statement should sound like it comes directly from the MP, incorporating their voice and style while addressing the specific context and audience needs.

## RAW GOVERNMENT STATEMENT: {raw_text} ## LOCAL CONTEXT:
{context}

## TARGET AUDIENCE:
{audience}

## REQUIRED TONE: {tone}
{tone_instructions}

{accepted_examples}

{rejected_examples}

## TRANSFORMATION GUIDELINES:

1. **Authentic Voice**: 
   - Use first-person perspective ("I", "my", "our constituency")
   - Maintain the MP's conversational style shown in the examples
   - Avoid bureaucratic language and generic political phrases

2. **Local Relevance**:
   - Incorporate specific local context provided
   - Reference constituency concerns where appropriate
   - Make national announcements feel relevant to local constituents

3. **Audience Awareness**:
   - Tailor vocabulary and examples to resonate with the target audience
   - Address specific concerns this audience might have
   - Use appropriate level of detail and explanation

4. **Personal Connection**:
   - Include the MP's personal commitment to the issue
   - Reference relevant past work on similar issues when appropriate
   - Show understanding of constituent needs

5. **Clear Communication**:
   - Maintain clarity on key facts and figures from the original statement
   - Structure with clear paragraphs and logical flow
   - Avoid overly complex sentences or jargon

## OUTPUT REQUIREMENTS:
- Produce a complete, polished statement ready for publication
- Length should be appropriate to the complexity of the topic (typically 150-300 words)
- Balance faithfulness to the original information with personalization
- Do not include any explanatory notes, only provide the rewritten statement

## REWRITTEN STATEMENT:
"""
            return prompt
        except Exception as e:
            log_error("Prompt construction error", e)
            raise Exception(f"Failed to construct prompt: {str(e)}")

    def get_tone_instructions(self, tone):
        """Get specific instructions for the selected tone"""
        try:
            tone_map = {
                "Neutral/Balanced": """
Strike a moderate, even-handed tone that acknowledges different perspectives. 
- Use measured language that avoids strong emotional appeals
- Present information in a fair and objective manner
- Acknowledge complexity without taking strong positions
- Use balanced phrasing like "on one hand... on the other hand"
- Convey thoughtfulness and consideration of multiple viewpoints
""",
                "Empathetic/Caring": """
Express genuine concern and understanding for constituents' feelings and experiences.
- Use warm, compassionate language that validates emotions
- Acknowledge difficulties people may be experiencing
- Include phrases like "I understand that..." or "I know many of you are feeling..."
- Demonstrate that you're listening and that constituent concerns matter
- Balance empathy with hope and solutions
""",
                "Authoritative/Confident": """
Project strength, expertise and decisiveness.
- Use clear, direct statements without hedging language
- Emphasize concrete actions and solutions
- Include phrases that demonstrate leadership and conviction
- Maintain a formal, professional tone
- Reference expertise, experience, or past achievements where relevant
""",
                "Optimistic/Positive": """
Focus on opportunities, solutions and positive outcomes.
- Emphasize progress, improvements, and future benefits
- Use uplifting language and hopeful framing
- Highlight what's working well and potential for positive change
- Include forward-looking statements and vision
- Balance optimism with realism to maintain credibility
""",
                "Concerned/Serious": """
Convey appropriate gravity for serious issues while maintaining constructive engagement.
- Use language that acknowledges the seriousness of challenges
- Express appropriate concern without alarming unnecessarily
- Demonstrate that you're taking the issue seriously
- Balance concern with determination to address problems
- Avoid minimizing genuine problems
""",
                "Conversational/Friendly": """
Adopt an approachable, personal tone as if speaking directly to constituents.
- Use relaxed, everyday language rather than formal political speech
- Include occasional contractions and more casual phrasing
- Write as if having a one-to-one conversation
- Create a sense of personal connection and accessibility
- Maintain professionalism while being personable
""",
                "Formal/Professional": """
Maintain a dignified, traditional political communication style.
- Use more formal language and structured sentences
- Maintain appropriate distance and decorum
- Avoid colloquialisms and overly casual expressions
- Project statesmanship and institutional respect
- Focus on precision of language and clarity of message
""",
                "Urgent/Call to Action": """
Convey immediacy and encourage specific responses or engagement.
- Use language that emphasizes timeliness and importance
- Include clear calls to action where appropriate
- Create a sense of momentum and necessary response
- Use slightly more dynamic and energetic language
- Balance urgency with reassurance to avoid causing anxiety
"""
            }
            
            return tone_map.get(tone, "Use a natural, conversational tone that feels personal and authentic.")
        except Exception as e:
            log_error("Get tone instructions error", e)
            return "Use a natural, conversational tone that feels personal and authentic."

    def call_llm_api(self, prompt):
        """Call the OpenAI API with the constructed prompt"""
        try:
            # Get model from config
            config = configparser.ConfigParser()
            config.read('config.ini')
            model = config['API']['MODEL'] if 'API' in config and 'MODEL' in config['API'] else "gpt-4o"  # Updated default
            
            # Make API call to OpenAI
            response = self.openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a skilled political communication specialist who helps transform official government statements into personalized MP communications."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            # Extract and return the generated text
            return response.choices[0].message.content.strip()
        except Exception as e:
            log_error("API call error", e)
            raise Exception(f"API call failed: {str(e)}")

    def log_submission(self, raw_text, context, audience, tone, generated_text, notes=None):
        """Log the submission to the database"""
        try:
            conn = sqlite3.connect('mp_rewriter.db')
            cursor = conn.cursor()
            
            # Insert submission
            cursor.execute("""
            INSERT INTO submissions (original_text, context, target_audience, tone, generated_text, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (raw_text, context, audience, tone, generated_text, "pending", notes))
            
            # Get the inserted row ID
            submission_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            return submission_id
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to log submission: {str(e)}")
            log_error("Log submission error", e)
            return None

    def accept_statement(self):
        """Handle the accept button click event"""
        if not self.current_submission_id:
            messagebox.showwarning("No Submission", "No statement has been generated yet.")
            return
        
        try:
            conn = sqlite3.connect('mp_rewriter.db')
            cursor = conn.cursor()
            
            # Update submission status to 'accepted'
            cursor.execute("""
            UPDATE submissions SET status = 'accepted' WHERE id = ?
            """, (self.current_submission_id,))
            
            # Get the accepted text and metadata to add to past_responses
            cursor.execute("""
            SELECT generated_text, target_audience, tone, context 
            FROM submissions 
            WHERE id = ?
            """, (self.current_submission_id,))
            
            result = cursor.fetchone()
            
            if result:
                generated_text, audience, tone, context = result
                
                # Determine topic from context/audience
                topic = context if context else audience
                
                # Add to past_responses
                cursor.execute("""
                INSERT INTO past_responses (published_text, topic, tone, source)
                VALUES (?, ?, ?, ?)
                """, (generated_text, topic, tone, f"Generated from submission #{self.current_submission_id}"))
            
            conn.commit()
            conn.close()
            
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
            conn = sqlite3.connect('mp_rewriter.db')
            cursor = conn.cursor()
            
            cursor.execute("""
            UPDATE submissions SET status = 'rejected' WHERE id = ?
            """, (self.current_submission_id,))
            
            conn.commit()
            conn.close()
            
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
            prompt = self.construct_refresh_prompt(raw_text, context, audience, tone, good_examples, rejected_examples)
            
            # Call the LLM API with higher temperature
            generated_text = self.call_refresh_llm_api(prompt)
            
            # Log as a new submission
            self.current_submission_id = self.log_submission(raw_text, context, audience, tone, generated_text, notes)
            
            # Update UI
            self.root.after(0, self.update_ui_with_generation, generated_text)
            
        except Exception as e:
            self.root.after(0, lambda: self.handle_error(f"Error during regeneration: {str(e)}"))
            log_error("Process refresh error", e)

    def construct_refresh_prompt(self, raw_text, context, audience, tone, accepted_examples, rejected_examples):
        """Construct a prompt for refreshing with emphasis on diversity"""
        try:
            # Get tone instructions
            tone_instructions = self.get_tone_instructions(tone)
            
            # Format accepted examples
            accepted_content = ""
            if accepted_examples:
                accepted_content = "## EXAMPLES TO EMULATE (these showcase the MP's voice and style):\n\n"
                for i, (response, topic, resp_tone) in enumerate(accepted_examples, 1):
                    accepted_content += f"### Example {i} "
                    if resp_tone and resp_tone != "None":
                        accepted_content += f"(Tone: {resp_tone})"
                    accepted_content += f":\n\"{response}\"\n\n"
            
            # Format rejected examples
            rejected_content = ""
            if rejected_examples and len(rejected_examples) > 0:
                rejected_content = "## EXAMPLES TO AVOID (especially the first one which was your previous attempt):\n\n"
                for i, (response, topic, resp_tone) in enumerate(rejected_examples, 1):
                    label = "Your Previous Attempt" if i == 1 else f"Bad Example {i}"
                    rejected_content += f"### {label}:\n\"{response}\"\n\n"
                    
                    if i == 1:
                        rejected_content += "Problems with this version:\n"
                        rejected_content += "- It didn't fully capture the MP's personal voice\n"
                        rejected_content += "- The local context wasn't sufficiently incorporated\n"
                        rejected_content += "- It may have used generic political language\n"
                        rejected_content += "- The tone wasn't quite right for the audience\n\n"
                    else:
                        rejected_content += "Problem: This example doesn't effectively represent the MP's voice or connect with constituents.\n\n"
            
            # Create the complete prompt with emphasis on diversity
            prompt = f"""# MP STATEMENT REWRITING TASK (SECOND ATTEMPT)

## OBJECTIVE:
Transform the government statement below into a personalized communication from the MP. Your previous attempt was not approved, so this version needs to take a SIGNIFICANTLY DIFFERENT APPROACH while still maintaining the MP's authentic voice.

## RAW GOVERNMENT STATEMENT: {raw_text} ## LOCAL CONTEXT:
{context}

## TARGET AUDIENCE:
{audience}

## REQUIRED TONE: {tone}
{tone_instructions}

{accepted_content}

{rejected_content}

## TRANSFORMATION REQUIREMENTS:

1. **TAKE A COMPLETELY DIFFERENT APPROACH** from your previous attempt:
   - Use a different structure and opening
   - Emphasize different aspects of the information
   - Find a fresh angle or framing for the message
   - Avoid repeating phrases, examples, or analogies from the rejected version

2. **Stronger Local Connection**:
   - More explicitly incorporate the local context provided
   - Make stronger connections to constituency-specific issues
   - Add more geographical or community-specific references
   - Show how national policies directly impact this specific constituency

3. **More Authentic Voice**:
   - Use more natural, conversational language
   - Include more personal commitment ("I am committed to..." "I've been working on...")
   - Avoid political clichés and generic phrases
   - Make it sound like a real person speaking, not a press release

4. **Better Audience Targeting**:
   - Address the specific needs and concerns of this audience more directly
   - Use language, examples, and references that will resonate with them
   - Adjust complexity and detail level to match audience expectations
   - Include specific benefits or impacts relevant to this audience

5. **More Compelling Structure**:
   - Create a stronger opening that immediately engages
   - Ensure a logical flow with clear transitions
   - Include a more memorable conclusion with clear next steps
   - Break up dense information into more digestible parts

## OUTPUT REQUIREMENTS:
- Produce a complete, polished statement ready for publication
- Length should be appropriate to the complexity of the topic (typically 150-300 words)
- Ensure this version is distinctly different from your previous attempt
- Do not include any explanatory notes, only provide the rewritten statement

## REWRITTEN STATEMENT:"""
            return prompt
        except Exception as e:
            log_error("Refresh prompt construction error", e)
            raise Exception(f"Failed to construct refresh prompt: {str(e)}")

    def call_refresh_llm_api(self, prompt):
        """Call the OpenAI API with higher temperature for diversity"""
        try:
            # Get model from config
            config = configparser.ConfigParser()
            config.read('config.ini')
            model = config['API']['MODEL'] if 'API' in config and 'MODEL' in config['API'] else "gpt-4o"  # Updated default
            
            # Make API call to OpenAI with higher temperature for more diversity
            response = self.openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a skilled political communication specialist who excels at creative reframing and finding fresh approaches to political messaging."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,  # Higher temperature for more creativity and diversity
                max_tokens=1500,
                presence_penalty=0.6,  # Encourage new phrasing
                frequency_penalty=0.6   # Discourage repetition of previously used phrases
            )
            
            # Extract and return the generated text
            return response.choices[0].message.content.strip()
        except Exception as e:
            log_error("Refresh API call error", e)
            raise Exception(f"API call failed: {str(e)}")


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


def populate_sample_data():
    """Populate the database with sample past responses if empty"""
    try:
        # First make sure tables exist
        conn = sqlite3.connect('mp_rewriter.db')
        cursor = conn.cursor()
        
        # Check if past_responses table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='past_responses'")
        if not cursor.fetchone():
            # Create table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS past_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                published_text TEXT NOT NULL,
                topic TEXT,
                tone TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                source TEXT,
                tags TEXT
            )
            ''')
            conn.commit()
        
        # Now check if it's empty
        cursor.execute("SELECT COUNT(*) FROM past_responses")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Add sample past responses (good examples) with tones
            sample_responses = [
                ("I've heard from many residents across our constituency about the impact of these changes. While the government's policy aims to address national concerns, I want to assure everyone that I'm working tirelessly to ensure our local needs are properly considered and that no one is left behind. Just last week, I met with the Minister to discuss how this will affect our high street businesses and secured a commitment for additional support.", 
                 "Policy Response", "Empathetic/Caring"),
                
                ("The recent funding announcement is welcome news for our area. I've been lobbying ministers for months to recognize our community's specific needs, and I'm pleased to see that our voice has been heard. This £2.4 million investment will directly benefit families in Millfield, Westpark and Northside, with particular focus on improving the facilities that residents have repeatedly told me are their top priorities. I'll be holding a series of community meetings next month to ensure these funds deliver maximum impact where they're needed most.", 
                 "Funding Announcement", "Optimistic/Positive"),
                
                ("The safety of our community is my top priority. Following the concerning incidents in the town center last month, I've been in regular contact with our local police leadership, and I've secured a commitment for increased patrols in the affected areas. Everyone deserves to feel safe in their neighborhood, and I won't rest until this issue is properly addressed. I've also established a community safety forum that will meet monthly - the first session is on Thursday at the Community Centre, and I encourage anyone concerned to attend and have your voice heard.", 
                 "Community Safety", "Authoritative/Confident"),
                
                ("Our local schools are the backbone of our community, and I'm proud to support the incredible work of our teachers and staff. The challenges they face deserve recognition, which is why I've raised these concerns directly with the Education Secretary and will continue pressing for the resources our children deserve. Having visited all twelve schools in our constituency this term, I've seen firsthand both the remarkable dedication of staff and the urgent need for better funding. This isn't just about buildings or budgets – it's about giving our children the best possible start in life.", 
                 "Education", "Conversational/Friendly")
            ]
            
            cursor.executemany("""
            INSERT INTO past_responses (published_text, topic, tone)
            VALUES (?, ?, ?)
            """, sample_responses)
            
            # Make sure submissions table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='submissions'")
            if not cursor.fetchone():
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_text TEXT NOT NULL,
                    context TEXT,
                    target_audience TEXT,
                    tone TEXT,
                    generated_text TEXT,
                    status TEXT DEFAULT 'pending',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT
                )
                ''')
                conn.commit()
            
            # Check if submissions table has any rejected examples
            cursor.execute("SELECT COUNT(*) FROM submissions WHERE status = 'rejected'")
            rejected_count = cursor.fetchone()[0]
            
            if rejected_count == 0:
                # Add sample rejected submissions to demonstrate what to avoid
                sample_rejected = [
                    ("The Government has announced a new infrastructure plan that will benefit the entire nation. This is good news for everyone. The plan includes funding for various projects across the country and will create jobs. I support this initiative and look forward to seeing the positive impact it will have on our economy.", 
                     "The constituency has several infrastructure projects that need funding, including the bypass road and bridge repairs.", 
                     "Local residents", 
                     "Neutral/Balanced",
                     "The Government has announced a new infrastructure plan that will benefit the entire nation. This is good news for everyone. The plan includes funding for various projects across the country and will create jobs. I support this initiative and look forward to seeing the positive impact it will have on our economy.",
                     "rejected",
                     "Too generic, doesn't mention local context"),
                    
                    ("As your Member of Parliament, I am writing to inform you about the recent announcement regarding education funding. The Department of Education has allocated additional resources to schools across the country. This development aligns with the government's commitment to improving educational standards nationwide. Should you have any queries regarding this matter, please do not hesitate to contact my office.",
                     "Local schools have been facing budget cuts and three schools need urgent repairs to their buildings.",
                     "Parents and teachers",
                     "Formal/Professional",
                     "As your Member of Parliament, I am writing to inform you about the recent announcement regarding education funding. The Department of Education has allocated additional resources to schools across the country. This development aligns with the government's commitment to improving educational standards nationwide. Should you have any queries regarding this matter, please do not hesitate to contact my office.",
                     "rejected",
                     "Too formal and impersonal, doesn't address specific local school issues")
                ]
                
                cursor.executemany("""
                INSERT INTO submissions (original_text, context, target_audience, tone, generated_text, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, sample_rejected)
            
            conn.commit()
        
        conn.close()
    except Exception as e:
        log_error("Sample data population error", e)
        print(f"Error populating sample data: {str(e)}")


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
            from seperate.application_integrator import EnhancedUI
            enhanced_ui = EnhancedUI(app)
        except ImportError:
            messagebox.showwarning("Enhanced UI Unavailable", 
                                  "The EnhancedUI module could not be loaded. The application will run with basic UI.")
            log_error("Enhanced UI Import", Exception("EnhancedUI module not found"))
        except Exception as e:
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
