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
             student_name TEXT NOT NULL,
             email TEXT UNIQUE NOT NULL,
             password TEXT NOT NULL,  -- Store hashed passwords
             major TEXT NOT NULL,
             CGPA REAL DEFAULT 0.0,
             MCGPA REAL DEFAULT 0.0)''')

     
    # Student Courses Table
    c.execute('''CREATE TABLE IF NOT EXISTS StudentCourses (
                 record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                 student_id INTEGER NOT NULL,
                 course_code TEXT NOT NULL,
                 course_name TEXT NOT NULL,
                 semester TEXT NOT NULL,
                 credits INTEGER NOT NULL,
                 grade TEXT NOT NULL,
                 is_major_course BOOLEAN DEFAULT FALSE,
                 attempt INTEGER DEFAULT 1,
                 previous_grade REAL DEFAULT NULL,
                 FOREIGN KEY (student_id) REFERENCES Students(student_id))''')

                     # Enrollment Table
    c.execute('''CREATE TABLE IF NOT EXISTS Enrollment (
                 enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                 student_id INTEGER NOT NULL,
                 course_id TEXT NOT NULL,
                 semester TEXT NOT NULL,
                 grade TEXT CHECK(grade IN ('A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'F')),
                 FOREIGN KEY (student_id) REFERENCES Students(student_id))''')



    conn.commit()
    conn.close()

# Example usage
if __name__ == "__main__":
    create_database()
    print("Database created successfully!")

    # Test: Add a student with hashed password
    conn = sqlite3.connect('student_scheduler.db')  # Fixed indentation
    with open('insert_students.sql', 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()