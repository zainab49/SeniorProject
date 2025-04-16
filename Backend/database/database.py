import sqlite3
import hashlib

# Create database and tables
def create_database():
    conn = sqlite3.connect('student_scheduler.db')
    c = conn.cursor()

    # Enable foreign key support
    c.execute("PRAGMA foreign_keys = ON")

    # Students Table with Password
    c.execute('''CREATE TABLE IF NOT EXISTS Students (
                 student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                 first_name TEXT NOT NULL,
                 last_name TEXT NOT NULL,
                 email TEXT UNIQUE NOT NULL,
                 password TEXT NOT NULL,  -- Store hashed passwords
                 major TEXT NOT NULL,
                 current_gpa REAL DEFAULT 0.0,
                 major_gpa REAL DEFAULT 0.0,
                 academic_status TEXT DEFAULT 'Active',
                 total_credits_earned INTEGER DEFAULT 0)''')

    # Student Courses Table
    c.execute('''CREATE TABLE IF NOT EXISTS StudentCourses (
                 record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                 student_id INTEGER NOT NULL,
                 course_code TEXT NOT NULL,
                 course_name TEXT NOT NULL,
                 semester TEXT NOT NULL,
                 credits INTEGER NOT NULL,
                 grade REAL NOT NULL,
                 is_major_course BOOLEAN DEFAULT FALSE,
                 FOREIGN KEY (student_id) REFERENCES Students(student_id))''')

    # Academic Standing Table
    c.execute('''CREATE TABLE IF NOT EXISTS AcademicStanding (
                 standing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                 status_name TEXT UNIQUE NOT NULL,
                 min_gpa REAL NOT NULL,
                 min_credits INTEGER NOT NULL)''')

    # Insert initial academic standing rules
    c.execute('''INSERT OR IGNORE INTO AcademicStanding 
                 (status_name, min_gpa, min_credits)
                 VALUES 
                 ('Good Standing', 2.0, 12),
                 ('Probation', 1.5, 9),
                 ('Academic Alert', 2.3, 15)''')

    conn.commit()
    conn.close()

# Example usage
if __name__ == "__main__":
    create_database()
    print("Database created successfully!")

    # Test: Add a student with hashed password
    conn = sqlite3.connect('student_scheduler.db')
    c = conn.cursor()
    
    
    conn.commit()
    conn.close()
   