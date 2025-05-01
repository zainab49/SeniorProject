import json
import re

def parse_course_data(raw_data):
    courses = []
    current_course = None
    current_section = None
    current_class = None
    expecting_exam_date = False  # Track if next line contains exam details

    for entry in raw_data:
        entry = entry.strip()
        if not entry:
            continue

        # --- New Course Detection ---
        if re.match(r'^[A-Z]+\d+.*\(.*\)', entry):
            if current_course:
                courses.append(current_course)
            code, name = re.match(r'^([A-Z]+\d+)\s*\((.*?)\)', entry).groups()
            current_course = {
                "course_code": code.strip(),
                "course_name": name.strip(),
                "prerequisites": "",
                "exam_date": "",
                "exam_room": "-- No Room (LEC)",
                "sections": []
            }
            expecting_exam_date = False
            continue

        # --- Handle Exam Date ---
        if expecting_exam_date:
            # This line contains the actual exam date and room
            parts = entry.split(" - ")
            if len(parts) >= 4:
                current_course["exam_date"] = " - ".join(parts[:3]).strip()
                current_course["exam_room"] = parts[3].strip()
            expecting_exam_date = False
            continue

        if entry.startswith("Exam Date:"):
            # Next line will have the actual exam details
            expecting_exam_date = True
            continue
        # --- Sections ---
        if entry.startswith("Section:"):
            if current_course:
                current_section = {
                    "section_number": entry.split(":", 1)[1].strip(),
                    "instructor": "",
                    "available_seats": "-",
                    "exam_room": "-- No Room (LEC)",
                    "section_status": "OPEN",
                    "remarks": "",
                    "classes": []
                }
                current_course["sections"].append(current_section)
            continue

        # --- Class Parsing ---
        if current_section:
            if entry.startswith("Instructor:"):
                current_section["instructor"] = entry.split(":", 1)[1].strip()
            
            elif entry.startswith("Class Type:"):
                # Start new class
                current_class = {
                    "class_type": "",
                    "day": "",
                    "time_from": "",
                    "time_to": "",
                    "location": ""
                }
                current_section["classes"].append(current_class)
                _parse_class_line(entry, current_class)  # Fixed: Removed 'self.'
            
            elif current_class:
                # Continue parsing multi-line class info
                _parse_class_line(entry, current_class)  # Fixed: Removed 'self.'

    # Add the last course
    if current_course:
        courses.append(current_course)
    
    return courses

def _parse_class_line(line, current_class):  # Fixed: No 'self' parameter
    """Helper to parse class information from any line"""
    # Class Type
    if "Class Type:" in line:
        current_class["class_type"] = re.search(r'Class Type: (\w+)', line).group(1)
    
    # Day
    if "Day:" in line:
        current_class["day"] = re.search(r'Day: (\w+)', line).group(1)
    
    # Time
    if "From" in line and "To" in line:
        time_match = re.search(r'From (.*?) To (.*?)( Location:|$)', line)
        if time_match:
            current_class["time_from"] = time_match.group(1).strip()
            current_class["time_to"] = time_match.group(2).strip()
    
    # Location
    if "Location:" in line:
        current_class["location"] = line.split("Location:", 1)[1].strip()

# Usage remains the same
with open('CE-2024-25-F.json', 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

processed_data = []
for item in raw_data:
    if isinstance(item, str):
        processed_data.extend(item.replace('\\n', '\n').split('\n'))

courses = parse_course_data(processed_data)

with open('structured_courses_fixed.json', 'w', encoding='utf-8') as f:
    json.dump(courses, f, indent=4, ensure_ascii=False)

print(f"Success! Generated {len(courses)} courses.")