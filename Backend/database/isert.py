import sqlite3
import pandas as pd
import os

script_dir = os.path.dirname(os.path.abspath(__file__))

files = [
    os.path.join(script_dir, '../../Data/student/Ahmed.xlsx'),
    os.path.join(script_dir, '../../Data/student/Ali.xlsx'),
    os.path.join(script_dir, '../../Data/student/Fatima.xlsx')
]

# Connect to database with absolute path
db_path = os.path.join(script_dir, 'student_scheduler.db')
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
c = conn.cursor()

# Check if Students table exists (critical for foreign key)
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Students'")
if not c.fetchone():
    print(" Missing Students table - create this first!")
    exit()

# Rest of table creation code...

for file in files:
    resolved_path = os.path.normpath(file)
    print(f"\nProcessing: {resolved_path}")
    
    if not os.path.exists(resolved_path):
        print(f" File not found: {resolved_path}")
        continue

    try:
        df = pd.read_excel(resolved_path)
        print("Sample data:")
        print(df.head(2))  # Show first 2 rows for verification
        
        success_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                c.execute('''
                    INSERT INTO StudentCourses (
                        student_id, course_code, course_name, semester, 
                        credits, grade, is_major_course, attempt, previous_grade
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    int(row['student_id']),
                    str(row['course_code']).strip(),
                    str(row['course_name']).strip(),
                    str(row['semester']).strip(),
                    int(row['credits']),
                    str(row['grade']).strip().upper(),
                    bool(row['is_major_course']),
                    int(row['attempt']),
                    str(row['previous_grade']).strip().upper() if pd.notna(row['previous_grade']) else None
                ))
                success_count += 1
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")  # +2 for Excel row numbers (header + 1-based)
        
        conn.commit()  # Commit after each file
        print(f"✅ Inserted {success_count}/{len(df)} rows")
        
        if errors:
            print(f"❌ Errors in {len(errors)} rows:")
            for error in errors[:3]:  # Show first 3 errors
                print(f"  - {error}")
                
    except Exception as e:
        print(f"❌ File processing failed: {str(e)}")
        conn.rollback()

conn.close()
print("\nOperation completed. Database location:", db_path)