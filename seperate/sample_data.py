import sqlite3
from error_handler import log_error

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