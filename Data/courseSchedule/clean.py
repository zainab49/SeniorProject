import json
import re

# Load the messy JSON file
file_path = 'CE-2024-25-F.json'

with open(file_path, 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

# Fix encoding manually: replace \\n with real \n
fixed_data = []
for item in raw_data:
    if isinstance(item, str):
        fixed_item = item.replace("\\n", "\n")
        fixed_data.append(fixed_item)
    else:
        fixed_data.append(item)

cleaned_courses = []

current_course = None
current_section = None

# Helper functions
def split_course_block(block):
    """Split a big course block into smaller clean lines."""
    return [line.strip() for line in block.split('\n') if line.strip()]

def extract_course_info(line):
    match = re.match(r'(.*?)\s*\((.*?)\)', line)
    if match:
        code = match.group(1).strip()
        name = match.group(2).strip()
        return code, name
    return None, None

def extract_exam_info(line):
    parts = line.replace('Exam Date:', '').split('-')
    if len(parts) >= 4:
        date = parts[0].strip()
        start = parts[1].strip()
        end = parts[2].strip()
        room = parts[3].strip()
        return date, start, end, room
    return '', '', '', ''

# Start processing
for raw_line in fixed_data:
    lines = split_course_block(raw_line)

    for line in lines:
        if not line:
            continue

        if '(' in line and ')' in line and 'Prereqs:' not in line:
            if current_course:
                cleaned_courses.append(current_course)

            code, name = extract_course_info(line)
            current_course = {
                "course_code": code,
                "course_name": name,
                "prerequisites": "",
                "exam_date": "",
                "exam_time_start": "",
                "exam_time_end": "",
                "exam_room": "",
                "sections": []
            }
            current_section = None

        elif line.startswith('Prereqs:'):
            if current_course:
                current_course['prerequisites'] = line.replace('Prereqs:', '').strip()

        elif line.startswith('Exam Date:'):
            if current_course:
                date, start, end, room = extract_exam_info(line)
                current_course['exam_date'] = date
                current_course['exam_time_start'] = start
                current_course['exam_time_end'] = end
                current_course['exam_room'] = room

        elif line.startswith('Section:'):
            if current_course:
                section_number = line.replace('Section:', '').strip()
                current_section = {
                    "section_number": section_number,
                    "instructor": "",
                    "available_seats": "",
                    "exam_room": "",
                    "section_status": "",
                    "remarks": "",
                    "classes": []
                }
                current_course["sections"].append(current_section)

        elif line.startswith('Instructor:'):
            if current_section:
                instructor_info = line.replace('Instructor:', '').strip()
                current_section['instructor'] = instructor_info

        elif 'Available Seats:' in line:
            if current_section:
                current_section['available_seats'] = line.replace('Available Seats:', '').strip()

        elif 'Exam Room:' in line:
            if current_section:
                current_section['exam_room'] = line.replace('Exam Room:', '').strip()

        elif 'Section Status:' in line:
            if current_section:
                current_section['section_status'] = line.replace('Section Status:', '').strip()

        elif line.startswith('Class Type:'):
            if current_section:
                parts = line.replace('Class Type:', '').split('Day:')
                class_type = parts[0].strip()
                day = parts[1].strip() if len(parts) > 1 else ''

                current_class = {
                    "class_type": class_type,
                    "day": day,
                    "time_from": "",
                    "time_to": "",
                    "location": ""
                }
                current_section['classes'].append(current_class)

        elif line.startswith('Time:'):
            if current_section and current_section['classes']:
                parts = line.replace('Time:', '').split('Location:')
                if len(parts) == 2:
                    time_info = parts[0].strip()
                    location = parts[1].strip()

                    if 'To' in time_info:
                        from_time = time_info.split('To')[0].replace('From', '').strip()
                        to_time = time_info.split('To')[1].strip()

                        current_section['classes'][-1]['time_from'] = from_time
                        current_section['classes'][-1]['time_to'] = to_time
                        current_section['classes'][-1]['location'] = location

# Add last course
if current_course:
    cleaned_courses.append(current_course)

# Save result
output_file = 'fixed_courses.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(cleaned_courses, f, indent=4)

print(f"✅ Done! {len(cleaned_courses)} courses cleaned and saved into {output_file}.")
