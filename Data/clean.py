import json
import re

def parse_course_data(raw_data):
    courses = []
    current_course = None
    current_section = None
    current_class = None
    exam_date_next_line = False  # Flag to track if next line contains exam date

    for line in raw_data:
        line = line.strip()
        if not line:
            continue

        # New Course Detection
        if re.match(r'^[A-Z]+\d+.*\(.*\)', line):
            if current_course:
                courses.append(current_course)
            code, name = re.match(r'^([A-Z]+\d+)\s*\((.*?)\)', line).groups()
            current_course = {
                "course_code": code.strip(),
                "course_name": name.strip(),
                "prerequisites": "",
                "exam_date": "",
                "exam_room": "-- No Room (LEC)",
                "sections": []
            }
            exam_date_next_line = False
            continue

        # Handle Exam Date
        if exam_date_next_line:
            # This is the line containing the actual exam date
            exam_parts = [part.strip() for part in line.split(' - ') if part.strip()]
            if len(exam_parts) >= 3:
                current_course["exam_date"] = ' - '.join(exam_parts[:3])
                if len(exam_parts) >= 4:
                    current_course["exam_room"] = exam_parts[3]
            exam_date_next_line = False
            continue

        if line.startswith("Exam Date:"):
            exam_date_next_line = True
            continue

        # Prerequisites
        if line.startswith("Prereqs:"):
            if current_course:
                current_course["prerequisites"] = line.split(":", 1)[1].strip()
            continue

        # Sections
        if line.startswith("Section:"):
            if current_course:
                current_section = {
                    "section_number": line.split(":", 1)[1].strip(),
                    "instructor": "",
                    "available_seats": "-",
                    "exam_room": "-- No Room (LEC)",
                    "section_status": "OPEN",
                    "remarks": "",
                    "classes": []
                }
                current_course["sections"].append(current_section)
            continue

        # Class Parsing
        if current_section:
            if line.startswith("Instructor:"):
                current_section["instructor"] = line.split(":", 1)[1].strip()
            
            elif line.startswith("Class Type:"):
                current_class = {
                    "class_type": "",
                    "day": "",
                    "time_from": "",
                    "time_to": "",
                    "location": ""
                }
                current_section["classes"].append(current_class)
                _parse_class_line(line, current_class)
            
            elif current_class:
                _parse_class_line(line, current_class)

    if current_course:
        courses.append(current_course)
    
    return courses

def _parse_class_line(line, current_class):
    """Helper to parse class information from any line"""
    if "Class Type:" in line:
        match = re.search(r'Class Type: (\w+)', line)
        if match:
            current_class["class_type"] = match.group(1)
    
    if "Day:" in line:
        match = re.search(r'Day: (\w+)', line)
        if match:
            current_class["day"] = match.group(1)
    
    if "From" in line and "To" in line:
        time_match = re.search(r'From (.*?) To (.*?)( Location:|$)', line)
        if time_match:
            current_class["time_from"] = time_match.group(1).strip()
            current_class["time_to"] = time_match.group(2).strip()
    
    if "Location:" in line:
        current_class["location"] = line.split("Location:", 1)[1].strip()

# Load and process the data
with open('CE-2024-25-S.json', 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

# Pre-process the data to split into individual lines
processed_data = []
for item in raw_data:
    if isinstance(item, str):
        # Split by newlines and add each line separately
        lines = item.replace('\\n', '\n').split('\n')
        processed_data.extend([line.strip() for line in lines if line.strip()])

courses = parse_course_data(processed_data)

with open('structured_courses_fixed.json', 'w', encoding='utf-8') as f:
    json.dump(courses, f, indent=4, ensure_ascii=False)

print(f"Success! Generated {len(courses)} courses.")
print("Example exam date from first course:", courses[0].get("exam_date", "Not found"))