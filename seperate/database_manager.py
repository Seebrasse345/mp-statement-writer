import sqlite3
from tkinter import messagebox
from error_handler import log_error

def initialize_database():
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
        return True
    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to initialize database: {str(e)}")
        log_error("Database initialization error", e)
        return False

def log_submission(raw_text, context, audience, tone, generated_text, notes=None):
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

def get_past_responses(status=None, limit=3):
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

def update_submission_status(submission_id, status):
    """Update the status of a submission"""
    try:
        conn = sqlite3.connect('mp_rewriter.db')
        cursor = conn.cursor()
        
        cursor.execute("""
        UPDATE submissions SET status = ? WHERE id = ?
        """, (status, submission_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log_error("Update submission status error", e)
        return False

def get_submission_by_id(submission_id):
    """Get a submission by ID"""
    try:
        conn = sqlite3.connect('mp_rewriter.db')
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT original_text, context, target_audience, tone, generated_text, notes
        FROM submissions
        WHERE id = ?
        """, (submission_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result
    except Exception as e:
        log_error("Get submission by ID error", e)
        return None

def save_accepted_statement(submission_id, generated_text, topic, tone):
    """Save an accepted statement to past_responses"""
    try:
        conn = sqlite3.connect('mp_rewriter.db')
        cursor = conn.cursor()
        
        # Add to past_responses
        cursor.execute("""
        INSERT INTO past_responses (published_text, topic, tone, source)
        VALUES (?, ?, ?, ?)
        """, (generated_text, topic, tone, f"Generated from submission #{submission_id}"))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log_error("Save accepted statement error", e)
        return False

def get_submission_details(submission_id):
    """Get detailed information about a submission"""
    try:
        conn = sqlite3.connect('mp_rewriter.db')
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT original_text, context, target_audience, tone, generated_text, status, timestamp, notes
        FROM submissions
        WHERE id = ?
        """, (submission_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result
    except Exception as e:
        log_error("Get submission details error", e)
        return None

def get_approved_statement_details(statement_id):
    """Get details of an approved statement"""
    try:
        conn = sqlite3.connect('mp_rewriter.db')
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT published_text, topic, tone, timestamp, source, tags
        FROM past_responses
        WHERE id = ?
        """, (statement_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result
    except Exception as e:
        log_error("Get approved statement details error", e)
        return None