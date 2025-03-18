import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sqlite3
import datetime
from error_handler import log_error
from utils import format_timestamp, truncate_text

def create_history_window(root, callbacks):
    """Create and manage the history window"""
    try:
        history_window = tk.Toplevel(root)
        history_window.title("Submission History")
        history_window.geometry("900x600")
        history_window.minsize(800, 500)
        
        # Create treeview for submissions
        frame = ttk.Frame(history_window, padding=10)
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
        
        ttk.Button(search_frame, text="Search", 
                command=lambda: callbacks['search_submissions'](tree, search_entry.get(), search_by.get())
                ).pack(side=tk.LEFT, padx=5)
                
        ttk.Button(search_frame, text="Clear", 
                command=lambda: [search_entry.delete(0, tk.END), callbacks['load_submissions'](tree)]
                ).pack(side=tk.LEFT)
        
        # Buttons frame
        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(buttons_frame, text="View Details", 
                command=lambda: callbacks['view_submission_details'](tree.item(tree.focus())['values'][0] if tree.focus() else None)
                ).pack(side=tk.LEFT, padx=5)
                
        ttk.Button(buttons_frame, text="Load to Editor", 
                command=lambda: callbacks['load_submission_to_editor'](tree.item(tree.focus())['values'][0] if tree.focus() else None)
                ).pack(side=tk.LEFT, padx=5)
                
        ttk.Button(buttons_frame, text="Refresh", 
                command=lambda: callbacks['load_submissions'](tree)
                ).pack(side=tk.LEFT, padx=5)
                
        ttk.Button(buttons_frame, text="Close", command=history_window.destroy).pack(side=tk.RIGHT)
        
        # Load submissions
        callbacks['load_submissions'](tree)
        
        # Double-click to view details
        tree.bind("<Double-1>", lambda event: callbacks['view_submission_details'](
            tree.item(tree.focus())['values'][0] if tree.focus() else None)
        )
        
        return history_window, tree
    
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open history: {str(e)}")
        log_error("Open history error", e)
        return None, None

def load_submissions(tree):
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
            formatted_time = format_timestamp(timestamp)
            
            # Preview of original text (first 50 chars)
            preview = truncate_text(original, 50)
            
            tree.insert('', tk.END, values=(id, formatted_time, status, audience, tone, preview))
            
        conn.close()
        
    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to load submissions: {str(e)}")
        log_error("Load submissions error", e)

def search_submissions(tree, search_text, search_field):
    """Search submissions based on criteria"""
    try:
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
            
        if not search_text:
            load_submissions(tree)
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
            formatted_time = format_timestamp(timestamp)
            
            # Preview of original text (first 50 chars)
            preview = truncate_text(original, 50)
            
            tree.insert('', tk.END, values=(id, formatted_time, status, audience, tone, preview))
            
        conn.close()
        
    except Exception as e:
        messagebox.showerror("Search Error", f"Failed to search submissions: {str(e)}")
        log_error("Search submissions error", e)

def view_submission_details(root, submission_id):
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
        detail_window = tk.Toplevel(root)
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
        
        # Create callbacks dictionary
        callbacks = {
            'load_submission': lambda sid: None,  # Will be replaced by caller
            'copy_to_clipboard': lambda: None     # Will be replaced by caller
        }
        
        # Define a closure to capture the current submission_id
        def load_and_close():
            callbacks['load_submission'](submission_id)
            detail_window.destroy()
            
        ttk.Button(button_frame, text="Load to Editor", 
                  command=load_and_close).pack(side=tk.LEFT, padx=5)
                  
        ttk.Button(button_frame, text="Copy to Clipboard", 
                  command=lambda: [root.clipboard_clear(), root.clipboard_append(generated), 
                  messagebox.showinfo("Copied", "Generated text copied to clipboard")]).pack(side=tk.LEFT, padx=5)
                  
        ttk.Button(button_frame, text="Close", command=detail_window.destroy).pack(side=tk.RIGHT, padx=5)
        
        return detail_window, callbacks
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load submission details: {str(e)}")
        log_error("View submission details error", e)
        return None, None

def create_approved_statements_window(root, callbacks):
    """View all approved past statements"""
    try:
        # Create window
        approved_window = tk.Toplevel(root)
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
        
        # Load data from database
        load_approved_statements(tree)
        
        # Add search frame
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(search_frame, text="Filter by:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(search_frame, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        search_by = tk.StringVar()
        search_by.set("All Fields")
        ttk.OptionMenu(search_frame, search_by, "All Fields", "Content", "Topic", "Tone").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(search_frame, text="Search", 
                  command=lambda: callbacks['search_approved'](tree, search_entry.get(), search_by.get())).pack(side=tk.LEFT, padx=5)
        
        # Add buttons
        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(buttons_frame, text="View Full Statement", 
                  command=lambda: callbacks['view_approved_details'](tree.item(tree.focus())['values'][0] if tree.focus() else None)).pack(side=tk.LEFT, padx=5)
                  
        ttk.Button(buttons_frame, text="Close", command=approved_window.destroy).pack(side=tk.RIGHT)
        
        # Double-click to view details
        tree.bind("<Double-1>", lambda event: callbacks['view_approved_details'](tree.item(tree.focus())['values'][0] if tree.focus() else None))
        
        return approved_window, tree
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load approved statements: {str(e)}")
        log_error("View approved statements error", e)
        return None, None

def load_approved_statements(tree):
    """Load approved statements into the treeview"""
    try:
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
            
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
            formatted_time = format_timestamp(timestamp, "%d %b %Y")
            
            # Preview of text
            preview = truncate_text(text, 50)
            
            tree.insert('', tk.END, values=(id, formatted_time, topic or "General", tone or "Not specified", preview))
            
        conn.close()
        
    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to load approved statements: {str(e)}")
        log_error("Load approved statements error", e)

def search_approved_statements(tree, search_text, search_field):
    """Search approved statements based on criteria"""
    try:
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
            
        if not search_text:
            # Reload all
            load_approved_statements(tree)
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
            formatted_time = format_timestamp(timestamp, "%d %b %Y")
            
            # Preview of text
            preview = truncate_text(text, 50)
            
            tree.insert('', tk.END, values=(id, formatted_time, topic or "General", tone or "Not specified", preview))
            
        conn.close()
        
    except Exception as e:
        messagebox.showerror("Search Error", f"Failed to search statements: {str(e)}")
        log_error("Search approved statements error", e)

def view_approved_statement_details(root, statement_id, callbacks):
    """View details of an approved statement"""
    try:
        if not statement_id:
            messagebox.showwarning("No Selection", "Please select a statement to view.")
            return None
            
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
            return None
            
        text, topic, tone, timestamp, source, tags = result
        
        # Create detail window
        detail_window = tk.Toplevel(root)
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
        
        def use_template_and_close():
            callbacks['use_as_template'](text)
            detail_window.destroy()
        
        ttk.Button(button_frame, text="Use as Template", 
                  command=use_template_and_close).pack(side=tk.LEFT, padx=5)
                  
        ttk.Button(button_frame, text="Copy to Clipboard", 
                  command=lambda: [root.clipboard_clear(), root.clipboard_append(text), 
                  messagebox.showinfo("Copied", "Statement copied to clipboard")]).pack(side=tk.LEFT, padx=5)
                  
        ttk.Button(button_frame, text="Close", command=detail_window.destroy).pack(side=tk.RIGHT, padx=5)
        
        return detail_window
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load statement details: {str(e)}")
        log_error("View approved details error", e)
        return None