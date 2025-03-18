import tkinter as tk
from tkinter import ttk, scrolledtext
import os
from error_handler import log_error
from utils import get_tone_options

def setup_styles():
    """Set up ttk styles for better UI appearance"""
    try:
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
    except Exception as e:
        log_error("Setup styles error", e)

def create_menu(root, callbacks):
    """Create the application menu"""
    try:
        menubar = tk.Menu(root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New", command=callbacks['clear_all_fields'])
        file_menu.add_command(label="Export Statement", command=callbacks['export_statement'])
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Submission History", command=callbacks['open_history'])
        view_menu.add_command(label="Past Approved Statements", command=callbacks['view_approved_statements'])
        menubar.add_cascade(label="View", menu=view_menu)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Import Past Statements", command=callbacks['import_past_statements'])
        tools_menu.add_command(label="Settings", command=callbacks['open_settings'])
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="User Guide", command=callbacks['show_user_guide'])
        help_menu.add_command(label="About", command=callbacks['show_about'])
        menubar.add_cascade(label="Help", menu=help_menu)
        
        root.config(menu=menubar)
        return menubar
    except Exception as e:
        log_error("Menu creation error", e)
        return None

def create_input_panel(parent, app_vars, callbacks):
    """Set up the input panel with all needed fields"""
    try:
        # Frame for input fields
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Raw Statement
        ttk.Label(input_frame, text="Raw Government Statement:", style='Header.TLabel').grid(row=0, column=0, sticky=tk.W, pady=(10, 5))
        ttk.Label(input_frame, text="Enter the original statement that needs to be rewritten", style='Subheader.TLabel').grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        raw_statement = scrolledtext.ScrolledText(input_frame, height=10, wrap=tk.WORD)
        raw_statement.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))
        raw_statement.bind('<KeyRelease>', lambda event: callbacks['update_raw_word_count']())
        
        # Word count for raw statement
        ttk.Label(input_frame, textvariable=app_vars['raw_word_count']).grid(row=3, column=0, sticky=tk.E, pady=(0, 10))
        
        # Context
        ttk.Label(input_frame, text="Local Context:", style='Header.TLabel').grid(row=4, column=0, sticky=tk.W, pady=(10, 5))
        ttk.Label(input_frame, text="Include relevant local issues, constituency concerns, or personal campaign history", style='Subheader.TLabel').grid(row=5, column=0, sticky=tk.W, pady=(0, 5))
        
        context = ttk.Entry(input_frame, width=50)
        context.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Target Audience
        ttk.Label(input_frame, text="Target Audience:", style='Header.TLabel').grid(row=7, column=0, sticky=tk.W, pady=(10, 5))
        ttk.Label(input_frame, text="Specify who will be reading this communication", style='Subheader.TLabel').grid(row=8, column=0, sticky=tk.W, pady=(0, 5))
        
        target_audience = ttk.Entry(input_frame, width=50)
        target_audience.grid(row=9, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Tone Selection
        ttk.Label(input_frame, text="Communication Tone:", style='Header.TLabel').grid(row=10, column=0, sticky=tk.W, pady=(10, 5))
        ttk.Label(input_frame, text="Select the appropriate tone for this message", style='Subheader.TLabel').grid(row=11, column=0, sticky=tk.W, pady=(0, 5))
        
        tone_var = tk.StringVar()
        tone_dropdown = ttk.Combobox(input_frame, textvariable=tone_var, values=get_tone_options(), state="readonly")
        tone_dropdown.current(0)  # Set default tone
        tone_dropdown.grid(row=12, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Notes/Tags
        ttk.Label(input_frame, text="Additional Notes (optional):", style='Header.TLabel').grid(row=13, column=0, sticky=tk.W, pady=(10, 5))
        
        notes = ttk.Entry(input_frame, width=50)
        notes.grid(row=14, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Submit Button
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=15, column=0, sticky=tk.E, pady=20)
        
        clear_button = ttk.Button(button_frame, text="Clear Form", command=callbacks['clear_all_fields'], style='Secondary.TButton')
        clear_button.pack(side=tk.LEFT, padx=5)
        
        submit_button = ttk.Button(button_frame, text="Generate Rewritten Statement", command=callbacks['submit'], style='Primary.TButton')
        submit_button.pack(side=tk.LEFT)
        
        # Configure grid weights
        input_frame.grid_columnconfigure(0, weight=1)
        for i in range(16):
            input_frame.grid_rowconfigure(i, weight=0)
        input_frame.grid_rowconfigure(2, weight=3)  # Give more weight to raw statement
        
        # Return the widgets that will be accessed by the main application
        return {
            'raw_statement': raw_statement,
            'context': context,
            'target_audience': target_audience,
            'tone_dropdown': tone_dropdown,
            'tone_var': tone_var,
            'notes': notes,
            'submit_button': submit_button,
            'clear_button': clear_button
        }
    except Exception as e:
        log_error("Input panel configuration error", e)
        return None

def create_output_panel(parent, app_vars, callbacks):
    """Set up the output panel with the generated text and action buttons"""
    try:
        # Frame for output and buttons
        output_frame = ttk.Frame(parent)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Generated Statement
        ttk.Label(output_frame, text="Rewritten Statement:", style='Header.TLabel').grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        ttk.Label(output_frame, text="AI-generated response in the MP's voice", style='Subheader.TLabel').grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        
        generated_statement = scrolledtext.ScrolledText(output_frame, height=20, wrap=tk.WORD)
        generated_statement.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))
        generated_statement.bind('<KeyRelease>', lambda event: callbacks['update_generated_word_count']())
        
        # Word count for generated statement
        ttk.Label(output_frame, textvariable=app_vars['generated_word_count']).grid(row=3, column=0, sticky=tk.W, pady=(0, 10))
        
        # Feedback section
        ttk.Label(output_frame, text="Feedback on Generated Statement:", style='Header.TLabel').grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        
        # Progress bar for generation
        progress = ttk.Progressbar(output_frame, orient=tk.HORIZONTAL, length=100, mode='indeterminate')
        progress.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress.grid_remove()  # Hide initially
        
        # Action Buttons
        button_frame = ttk.Frame(output_frame)
        button_frame.grid(row=6, column=0, columnspan=3, sticky=tk.E, pady=10)
        
        edit_button = ttk.Button(button_frame, text="Edit", command=callbacks['enable_editing'], state=tk.DISABLED)
        edit_button.pack(side=tk.LEFT, padx=5)
        
        refresh_button = ttk.Button(button_frame, text="Regenerate", command=callbacks['refresh_statement'], state=tk.DISABLED)
        refresh_button.pack(side=tk.LEFT, padx=5)
        
        accept_button = ttk.Button(button_frame, text="Accept & Save", command=callbacks['accept_statement'], state=tk.DISABLED, style='Primary.TButton')
        accept_button.pack(side=tk.LEFT, padx=5)
        
        # Copy button
        copy_button = ttk.Button(button_frame, text="Copy to Clipboard", command=callbacks['copy_to_clipboard'], state=tk.DISABLED)
        copy_button.pack(side=tk.LEFT, padx=5)
        
        # Configure grid weights
        output_frame.grid_columnconfigure(0, weight=1)
        output_frame.grid_columnconfigure(1, weight=1)
        output_frame.grid_columnconfigure(2, weight=1)
        
        for i in range(7):
            output_frame.grid_rowconfigure(i, weight=0)
        output_frame.grid_rowconfigure(2, weight=1)  # Give more weight to generated statement
        
        # Return the widgets that will be accessed by the main application
        return {
            'generated_statement': generated_statement,
            'progress': progress,
            'edit_button': edit_button,
            'refresh_button': refresh_button,
            'accept_button': accept_button,
            'copy_button': copy_button
        }
    except Exception as e:
        log_error("Output panel configuration error", e)
        return None

def create_status_bar(root, status_var):
    """Create the status bar at the bottom of the application"""
    try:
        status_frame = ttk.Frame(root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        status_bar = ttk.Label(status_frame, textvariable=status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Version info
        version_label = ttk.Label(status_frame, text="v1.2.0", relief=tk.SUNKEN, anchor=tk.E)
        version_label.pack(side=tk.RIGHT, padx=5)
        
        return status_frame
    except Exception as e:
        log_error("Status bar creation error", e)
        return None