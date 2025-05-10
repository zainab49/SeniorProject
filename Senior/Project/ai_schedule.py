import json
import os
import random
from itertools import combinations, product
from collections import defaultdict
from django.db.models import Q
from Project.models import StudentCourse, Enrollment

# Helper: Load JSON with better error handling
def load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"File not found: {path}")
        return {}
    except json.JSONDecodeError:
        print(f"Invalid JSON in file: {path}")
        return {}
    except Exception as e:
        print(f"Error loading {path}: {str(e)}")
        return {}

# Helper: Flatten taken courses (past + current)

def get_taken_courses(student):
    low_grades = {"C", "C-", "D+", "D", "F"}
    low_grade_courses = set()
    
    all_courses = StudentCourse.objects.filter(student=student)
    completed = set()
    current = set(Enrollment.objects.filter(student=student).values_list('course_id', flat=True))
    
    for course in all_courses:
        completed.add(course.course_code)
        if course.grade in low_grades:
            low_grade_courses.add(course.course_code)
    
    return completed.union(current), low_grade_courses

# Helper: Parse time string to minutes since midnight for easier comparison
def time_to_minutes(time_str):
    if not time_str or not isinstance(time_str, str):
        return 0
    
    try:
        # Handle exam date format: "2025-05-27 - 11:30 - 13:30"
        if ' - ' in time_str:
            parts = time_str.split(' - ')
            if len(parts) >= 2:
                # Use the start time part
                time_str = parts[1]
        
        if ':' in time_str:
            h, m = map(int, time_str.split(':'))
            return h * 60 + m
        elif '.' in time_str:
            h, m = map(int, time_str.split('.'))
            return h * 60 + m
        else:
            # Try to handle military time format
            if len(time_str) == 4:
                h = int(time_str[:2])
                m = int(time_str[2:])
                return h * 60 + m
    except (ValueError, IndexError):
        pass
    
    return 0  # Default to midnight if parsing fails

# Helper: Check time conflicts with more robust time parsing
def has_time_conflict(class1, class2):
    # Check if same day - fast path for different days
    day1 = class1.get('day', '').upper()[:3] if class1.get('day', '') else ''
    day2 = class2.get('day', '').upper()[:3] if class2.get('day', '') else ''
    
    # Map full day names to 3-letter codes
    day_mapping = {
        'SUNDAY': 'SUN', 'MONDAY': 'MON', 'TUESDAY': 'TUE', 
        'WEDNESDAY': 'WED', 'THURSDAY': 'THU', 'FRIDAY': 'FRI', 'SATURDAY': 'SAT'
    }
    
    # Convert full day names to 3-letter codes
    if day1 in day_mapping:
        day1 = day_mapping[day1]
    if day2 in day_mapping:
        day2 = day_mapping[day2]
    
    if not day1 or not day2 or day1 != day2:
        return False
    
    # Fast path - check for common patterns before full conversion
    # If one class ends at exactly the time another starts, they don't conflict
    if class1.get('time_to') == class2.get('time_from') or class2.get('time_to') == class1.get('time_from'):
        return False
    
    # Convert times to minutes for easier comparison
    start1 = time_to_minutes(class1.get('time_from', '0:00'))
    end1 = time_to_minutes(class1.get('time_to', '0:00'))
    start2 = time_to_minutes(class2.get('time_from', '0:00'))
    end2 = time_to_minutes(class2.get('time_to', '0:00'))
    
    # Validate time ranges (end time should be after start time)
    if end1 <= start1:
        end1 = start1 + 60  # Default to 1-hour class
    if end2 <= start2:
        end2 = start2 + 60
    
    # Check for overlap - faster inequality check
    return max(start1, start2) < min(end1, end2)

# Helper: Process exam dates from the format in the sample
def extract_exam_info(exam_date_str):
    """Extract date and time information from exam date strings like '2025-05-27 - 11:30 - 13:30'"""
    if not exam_date_str or not isinstance(exam_date_str, str):
        return {'date': '', 'start': '', 'end': ''}
        
    parts = exam_date_str.split(' - ')
    if len(parts) >= 3:
        return {
            'date': parts[0],
            'start': parts[1],
            'end': parts[2]
        }
    elif len(parts) == 1:
        return {'date': parts[0], 'start': '', 'end': ''}
    else:
        return {'date': '', 'start': '', 'end': ''}

# Helper: Check schedule conflicts between courses
def has_conflict(existing_sections, new_section):
    # First check if it's the same course code (can't register for multiple sections of same course)
    new_course_code = new_section.get('course_code', '').strip()
    for existing in existing_sections:
        if existing.get('course_code', '').strip() == new_course_code:
            # Same course code - we can't have multiple sections
            return True
    
    # Handle the new exam date format
    new_exam_date_full = new_section.get('exam_date', '')
    new_exam_info = extract_exam_info(new_exam_date_full)
    new_exam_date = new_exam_info['date']
    
    # Quick check for exam date conflicts first (faster than class time checks)
    if new_exam_date:
        for sec in existing_sections:
            sec_exam_date_full = sec.get('exam_date', '')
            sec_exam_info = extract_exam_info(sec_exam_date_full)
            sec_exam_date = sec_exam_info['date']
            
            if sec_exam_date == new_exam_date:
                # We found a conflict with exam dates - no need to check class times
                return True
    
    # Optimize class time conflict check by using day buckets
    new_classes_by_day = {}
    for cls in new_section.get('classes', []):
        day = cls.get('day', '').upper()[:3] if cls.get('day', '') else ''
        if day:
            if day not in new_classes_by_day:
                new_classes_by_day[day] = []
            new_classes_by_day[day].append(cls)
    
    # Now only check classes that share days
    for sec in existing_sections:
        for cls1 in sec.get('classes', []):
            day1 = cls1.get('day', '').upper()[:3] if cls1.get('day', '') else ''
            if not day1 or day1 not in new_classes_by_day:
                continue
                
            # Only check classes on this day
            for cls2 in new_classes_by_day[day1]:
                if has_time_conflict(cls1, cls2):
                    return True
    
    return False

# Helper: Get plan file name from major
def get_plan_filename(major):
    major = major.strip().lower()
    if "cybersecurity" in major:
        if "2021" in major:
            return "Cy-2021.json"
        else:
            # Try other possible cybersecurity plan files
            return "Cy-2021.json"  # Default to 2021 version
    elif "network engineering" in major:
        if "2017" in major:
            return "NE-2017.json"
        else:
            return "NE-2017.json"  # Default to 2017 version
    elif "software engineering" in major:
        if "2024" in major:
            return "SE-2024.json"
        else:
            return "SE-2024.json"  # Default to 2024 version
    else:
        # Default to SE if unknown major
        print(f"Unknown major: {major}, defaulting to Software Engineering plan")
        return "SE-2024.json"

# Helper: Analyze student performance to determine strengths
def analyze_student_performance(student):
    """Analyze student's historical performance to determine strengths."""
    strengths = defaultdict(float)
    
    # Get course performance history
    courses = StudentCourse.objects.filter(student=student)
    
    # Extract course prefixes (e.g., ITNET, ITCS) and calculate average grade
    for course in courses:
        prefix = course.course_code.split(' ')[0] if ' ' in course.course_code else course.course_code[:4]
        
        # Convert letter grade to GPA value
        grade_map = {
            "A": 4.0, "A-": 3.67, "B+": 3.33, "B": 3.0, "B-": 2.67,
            "C+": 2.33, "C": 2.0, "C-": 1.67, "D+": 1.33, "D": 1.0, "F": 0.0
        }
        
        grade_value = grade_map.get(course.grade, 0)
        
        # Update running average for this subject area
        current_count = strengths.get(f"{prefix}_count", 0)
        current_total = strengths.get(prefix, 0) * current_count
        
        strengths[f"{prefix}_count"] = current_count + 1
        strengths[prefix] = (current_total + grade_value) / (current_count + 1)
    
    return strengths

# Helper: Check if a course is an internship course
def is_internship_course(course_name, course_code):
    """Check if a course is an internship-related course."""
    # Check course name for internship keywords
    internship_keywords = ['internship', 'practicum', 'field placement', 'co-op', 'cooperative education']
    
    # Check if any keyword appears in the course name (case-insensitive)
    if course_name and any(keyword.lower() in course_name.lower() for keyword in internship_keywords):
        return True
    
    # Also check course code for common internship course codes (e.g. INTP, INT)
    internship_codes = ['INTP', 'INT ', 'PRAC', 'COOP']
    if course_code and any(code in course_code for code in internship_codes):
        return True
    
    return False

# Helper: Check if prerequisites are met for a course
def are_prerequisites_met(course_code, prereq_str, taken_courses):
    """Advanced prerequisite checking that handles multiple prerequsite formats."""
    if not prereq_str or prereq_str == '---':
        return True  # No prerequisites
        
    # Normalize course codes by removing spaces
    taken_normalized = {course.replace(" ", "") for course in taken_courses}
    
    # Handle comma-separated format (e.g., "COURSE1, COURSE2")
    if ',' in prereq_str:
        prereq_list = [p.strip().replace(" ", "") for p in prereq_str.split(',')]
        # Check if any prereq is met (OR relationship)
        return any(prereq in taken_normalized for prereq in prereq_list)
    
    # Handle AND operator
    elif ' AND ' in prereq_str.upper():
        prereq_parts = [p.strip().replace(" ", "") for p in prereq_str.upper().split(' AND ')]
        # Check if all prerequs are met (AND relationship)
        return all(prereq in taken_normalized for prereq in prereq_parts)
    
    # Handle OR operator
    elif ' OR ' in prereq_str.upper():
        prereq_parts = [p.strip().replace(" ", "") for p in prereq_str.upper().split(' OR ')]
        # Check if any prereq is met (OR relationship)
        return any(prereq in taken_normalized for prereq in prereq_parts)
    
    # Simple single prerequisite
    return prereq_str.replace(" ", "") in taken_normalized

# Helper: Calculate a score for an individual course
def calculate_individual_course_score(course, student_strengths, is_in_academic_plan):
    """Calculate priority score for a single course."""
    score = 0

    # Major courses get high priority
    if course.get('is_major', False):
        score += 30
    
    # Courses in academic plan get extra priority
    if is_in_academic_plan:
        score += 40
    else:
        # Significant penalty for courses not in academic plan
        score -= 50

    # Higher credit courses get priority
    score += course.get('credits', 3) * 5

    # Consider student's historical performance
    code = course.get('course_code', '')
    prefix = code.split(' ')[0] if ' ' in code else code[:4]
    if prefix in student_strengths:
        # Boost score for areas where student has performed well
        if student_strengths[prefix] > 3.0:
            score += 10
        # Lower priority for areas where student has struggled
        elif student_strengths[prefix] < 2.0:
            score -= 8

    # Courses with prerequisites met get priority (they're likely more advanced/important)
    if course.get('prerequisite', ''):
        score += 5

    return score

# Helper: Calculate a score for a potential schedule
def calculate_schedule_score(courses, student_strengths):
    score = 0
    
    # Factor 1: Number of courses (more is better, up to 4)
    score += min(len(courses), 4) * 5
    
    # Factor 2: Major requirement courses
    major_courses = sum(1 for c in courses if c.get('is_major', False))
    score += major_courses * 10
    
    # Factor 3: Balanced schedule across days
    days_used = set()
    for course in courses:
        for class_meeting in course.get('classes', []):
            day = class_meeting.get('day', '')[:3].upper()
            if day:
                days_used.add(day)
    
    # Prefer schedules that use 3-4 days rather than 5+ days
    if 3 <= len(days_used) <= 4:
        score += 15
    else:
        score += 5
    
    # Factor 4: Student's historical performance in similar courses
    for course in courses:
        code = course.get('course_code', '')
        prefix = code.split(' ')[0] if ' ' in code else code[:4]
        if prefix in student_strengths:
            # Boost score for areas where student has performed well (> 3.0 GPA)
            if student_strengths[prefix] > 3.0:
                score += 8
            # Limit courses in areas where student has struggled (< 2.0 GPA)
            elif student_strengths[prefix] < 2.0:
                score -= 5
    
    return score

# Helper: Calculate diversity score between two schedules
def calculate_diversity(schedule1, schedule2):
    """Calculate how different two schedules are (higher is more diverse)"""
    if not schedule1 or not schedule2:
        return 100  # Maximum diversity if one schedule is empty
        
    # Extract course codes from both schedules
    codes1 = set(c.get('course_code', '').strip() for c in schedule1)
    codes2 = set(c.get('course_code', '').strip() for c in schedule2)
    
    # Count unique courses in each schedule
    total_unique = len(codes1.union(codes2))
    common_courses = len(codes1.intersection(codes2))
    
    # Calculate diversity percentage (0-100)
    if total_unique == 0:
        return 0
    
    diversity = 100 * (1 - (common_courses / total_unique))
    return diversity

# Main Function
def generate_course_schedule(student, schedule_dir, plan_dir):
    print(f"Generating schedule for student: {student.student_name}, Major: {student.major}")
    
    # Check directory paths
    if not os.path.exists(schedule_dir):
        print(f"Schedule directory not found: {schedule_dir}")
        return [], []
        
    if not os.path.exists(plan_dir):
        print(f"Plan directory not found: {plan_dir}")
        return [], []
    
    # Get student's strengths based on past performance
    student_strengths = analyze_student_performance(student)
    
    # Get plan filename
    plan_filename = get_plan_filename(student.major)
    if not plan_filename:
        print("No academic plan found for student's major")
        return [], []

    major_file = os.path.join(plan_dir, plan_filename)
    plan_data = load_json(major_file)
    
    # Print actual plan data for debugging
    print(f"Plan data keys: {list(plan_data.keys() if isinstance(plan_data, dict) else ['<not a dict>'])}")
    
    # Try different possible structures for academic plan
    academic_plan = None
    
    # Option 1: Standard structure from original code
    if 'program' in plan_data and 'study_plan' in plan_data.get('program', {}):
        academic_plan = plan_data.get('program', {}).get('study_plan', {})
    # Option 2: Direct study_plan at root
    elif 'study_plan' in plan_data:
        academic_plan = plan_data.get('study_plan', {})
    # Option 3: Courses are in a 'courses' field
    elif 'courses' in plan_data:
        academic_plan = plan_data.get('courses', {})
    # Option 4: Look for any field that might contain course data
    else:
        # Try to find any key that might contain a list of courses or structured data
        for key, value in plan_data.items() if isinstance(plan_data, dict) else []:
            if isinstance(value, (dict, list)) and key not in ['metadata', 'version', 'info']:
                academic_plan = value
                break
        # If still not found, use plan data itself
        if not academic_plan:
            academic_plan = plan_data
    
    if not academic_plan:
        print(f"No study plan found in {major_file}")
        return []  # Return single empty list instead of tuple
        
    print(f"Academic plan structure type: {type(academic_plan)}")

    # Flatten all courses from the academic plan and create a set of course codes for quick lookup
    all_plan_courses = []
    plan_course_codes = set()
    
    # Debug info
    if isinstance(academic_plan, dict):
        print(f"Academic plan keys: {list(academic_plan.keys())}")
    
    # Handle different possible structures of academic_plan
    try:
        # Structure option 1: dictionary with years as keys and dictionaries as values
        if isinstance(academic_plan, dict):
            for year_key, year in academic_plan.items():
                print(f"Examining year '{year_key}', type: {type(year)}")
                
                # Each year could be a dict with semesters as keys
                if isinstance(year, dict):
                    for sem_key, semester_courses in year.items():
                        print(f"  Examining semester '{sem_key}', type: {type(semester_courses)}")
                        if isinstance(semester_courses, list):
                            all_plan_courses.extend(semester_courses)
                            # Add normalized course codes (without spaces) to the set for quick lookup
                            for course in semester_courses:
                                if isinstance(course, dict) and 'course_code' in course:
                                    plan_course_codes.add(course['course_code'].replace(" ", ""))
                                    print(f"    Added course: {course['course_code']}")
                # Or year could be a list of courses directly
                elif isinstance(year, list):
                    all_plan_courses.extend(year)
                    for course in year:
                        if isinstance(course, dict) and 'course_code' in course:
                            plan_course_codes.add(course['course_code'].replace(" ", ""))
                            print(f"    Added course: {course['course_code']}")
                            
        # Structure option 2: list of courses directly in academic_plan
        elif isinstance(academic_plan, list):
            all_plan_courses.extend(academic_plan)
            for course in academic_plan:
                if isinstance(course, dict) and 'course_code' in course:
                    plan_course_codes.add(course['course_code'].replace(" ", ""))
                    print(f"    Added course: {course['course_code']}")
                    
        # Special case: maybe the plan is a single dictionary containing all courses with codes as keys
        if isinstance(academic_plan, dict) and len(plan_course_codes) == 0:
            for key, value in academic_plan.items():
                if isinstance(value, dict) and 'course_code' in value:
                    all_plan_courses.append(value)
                    plan_course_codes.add(value['course_code'].replace(" ", ""))
                    print(f"    Added course via direct lookup: {value['course_code']}")
                # The key itself might be a course code
                elif isinstance(value, dict):
                    # Create a synthetic course entry
                    synthetic_course = value.copy()
                    synthetic_course['course_code'] = key
                    all_plan_courses.append(synthetic_course)
                    plan_course_codes.add(key.replace(" ", ""))
                    print(f"    Added course using key as code: {key}")
                            
    except Exception as e:
        print(f"Error parsing academic plan: {str(e)}")
        print(f"Academic plan structure: {type(academic_plan)}")
        # Fallback: try to extract courses from any recognizable structure
        try:
            for item in academic_plan:
                if isinstance(item, dict) and 'course_code' in item:
                    all_plan_courses.append(item)
                    plan_course_codes.add(item['course_code'].replace(" ", ""))
                    print(f"    Added course in fallback mode: {item['course_code']}")
        except Exception as e2:
            print(f"Fallback extraction also failed: {str(e2)}")
    
    # Final fallback: if we still have no courses, look for any course-like structures 
    # in the entire plan data recursively
    if len(plan_course_codes) == 0:
        print("No courses found using standard methods. Performing deep search...")
        
        def find_courses_recursive(data, depth=0, max_depth=3):
            if depth > max_depth:
                return []
                
            found_courses = []
            
            if isinstance(data, dict):
                # Check if this dict looks like a course
                if 'course_code' in data and isinstance(data['course_code'], str):
                    found_courses.append(data)
                    return found_courses
                
                # Otherwise search all its values
                for key, value in data.items():
                    # If key looks like a course code and value is a dict, treat it as a course
                    if isinstance(key, str) and isinstance(value, dict):
                        if re.match(r'[A-Z]{2,4}\s*\d{3,4}', key):
                            course_data = value.copy()
                            course_data['course_code'] = key
                            found_courses.append(course_data)
                    
                    # Recursively search values
                    found_courses.extend(find_courses_recursive(value, depth + 1, max_depth))
                    
            elif isinstance(data, list):
                for item in data:
                    found_courses.extend(find_courses_recursive(item, depth + 1, max_depth))
            
            return found_courses
        
        try:
            import re
            deep_found_courses = find_courses_recursive(plan_data)
            
            # Add any found courses
            for course in deep_found_courses:
                if 'course_code' in course:
                    all_plan_courses.append(course)
                    plan_course_codes.add(course['course_code'].replace(" ", ""))
                    print(f"    Deep search found course: {course['course_code']}")
        except Exception as e:
            print(f"Deep search failed: {str(e)}")
    
    
    # If no courses in plan were found, we might need to just allow all courses
    if len(plan_course_codes) == 0:
        print("WARNING: No courses found in academic plan. Using fallback mode to accept all courses.")
        allow_all_courses = True
    else:
        allow_all_courses = False
        
    print(f"Found {len(plan_course_codes)} courses in academic plan")

    taken, low_grades = get_taken_courses(student)
    print(f"Student has completed {len(taken)} courses")

    # Load ONLY Spring semester course schedule files (ending with S.json)
    # Group sections by course code
    course_sections = defaultdict(list)  # key: course_code, value: list of sections
    
    # First quickly scan files to prioritize processing
    file_course_counts = {}
    total_courses = 0
    
    for file in os.listdir(schedule_dir):
        # Only process Spring semester files
        if file.endswith('S.json'):
            file_path = os.path.join(schedule_dir, file)
            try:
                # Just check file size and get a count without full parsing
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    file_course_counts[file] = len(data)
                    total_courses += len(data)
            except Exception as e:
                print(f"Error scanning {file}: {str(e)}")
                file_course_counts[file] = 0
    
    # Set a global limit on courses to process
    MAX_TOTAL_COURSES = 1000
    
    # If we have too many total courses, allocate proportionally
    if total_courses > MAX_TOTAL_COURSES:
        reduction_factor = MAX_TOTAL_COURSES / total_courses
        for file in file_course_counts:
            file_course_counts[file] = int(file_course_counts[file] * reduction_factor)
    
    # Now process files with their allocated course counts
    for file in os.listdir(schedule_dir):
        # Only process Spring semester files
        if file.endswith('S.json'):
            file_path = os.path.join(schedule_dir, file)
            data = load_json(file_path)

            # Use the calculated limit for this file
            max_courses = file_course_counts.get(file, 100)
            if len(data) > max_courses:
                print(f"Limiting {file} to {max_courses} courses (from {len(data)})")
                # Use random sampling instead of just taking the first N
                data = random.sample(data, max_courses)

            for course in data:
                # Skip entries with empty 'sections'
                if not course.get('sections'):
                    continue

                course_code = course.get('course_code', '').strip()
                course_name = course.get('course_name', '')
                
                # Skip if this course has already been taken and not failed
                if course_code in taken and course_code not in low_grades:

                    continue
                
                # Skip internship courses
                if is_internship_course(course_name, course_code):
                    continue
                
                # Check if course is in academic plan by comparing normalized codes
                normalized_code = course_code.replace(" ", "")
                is_in_plan = normalized_code in plan_course_codes
                
                # Skip courses that are not in the academic plan
                if not is_in_plan and not allow_all_courses:
                    continue

                # Find matching course in academic plan
                plan_course = None
                for pc in all_plan_courses:
                    pc_code = pc.get('course_code', '').replace(" ", "")
                    if pc_code == normalized_code:
                        plan_course = pc
                        break

                # If no matching course in plan, skip it (shouldn't happen with the previous check)
                if not plan_course:
                    continue

                # Check prerequisites
                prereq = plan_course.get('prerequisite', course.get('prerequisites', '')).strip()
                
                # Use the enhanced prerequisite check
                prereq_met = are_prerequisites_met(course_code, prereq, taken)
                
                if not prereq_met:
                    continue

                # Process each section and group by course code
                for section in course.get('sections', []):
                    # Skip sections with empty 'classes'
                    if not section.get('classes'):
                        continue

                    section_data = {
                        'course_code': course_code,
                        'course_name': course_name,
                        'section': section.get('section_number', ''),
                        'instructor': section.get('instructor', ''),
                        'exam_date': course.get('exam_date', ''),
                        'exam_start': '',  # Will be extracted from exam_date if needed
                        'exam_end': '',    # Will be extracted from exam_date if needed
                        'classes': section.get('classes', []),
                        'credits': plan_course.get('credits', 3),
                        'prerequisite': prereq,
                        'is_major': 'MR' in plan_course.get('course_type', ''),
                        'semester': file.replace('.json', ''),
                        'is_in_plan': is_in_plan
                    }
                    
                    # Group by course code
                    course_sections[course_code].append(section_data)
    
    # Get unique course codes
    unique_courses = list(course_sections.keys())
    print(f"Found {len(unique_courses)} unique courses with {sum(len(sections) for sections in course_sections.values())} total sections")
    
    # If we have too many unique courses, prioritize major courses
    if len(unique_courses) > 50:  # Reasonable limit for combinations
        # Score each course (using first section's data for scoring)
        course_scores = []
        for course_code in unique_courses:
            first_section = course_sections[course_code][0]  # Use first section for scoring
            is_in_plan = first_section.get('is_in_plan', False)
            score = calculate_individual_course_score(first_section, student_strengths, is_in_plan)
            course_scores.append((course_code, score))
        
        # Sort by score (descending)
        course_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Take top 50 courses
        unique_courses = [code for code, _ in course_scores[:50]]
        
        # Rebuild course_sections with only selected courses
        filtered_sections = defaultdict(list)
        for course_code in unique_courses:
            filtered_sections[course_code] = course_sections[course_code]
        course_sections = filtered_sections
    
    if not unique_courses:
        print("No valid courses found")
        return []  # Return a single empty list instead of tuple

    # Generate multiple schedules (3 total)
    schedules = []
    min_diversity_threshold = 100  # At least 50% different courses between schedules
    
    # Target exactly 4 different courses for each schedule
    target_course_count = 4
    print(f"Finding best schedules with {target_course_count} courses each")
    
    # If we have fewer than target courses, adjust
    if len(unique_courses) < target_course_count:
        target_course_count = len(unique_courses)
    
    # Number of schedules to generate
    num_schedules = 3
    max_attempts = 200  # Maximum number of attempts to find diverse schedules
    
    # Function to generate one schedule
    def generate_single_schedule(excluded_courses=None):
        excluded_courses = excluded_courses or set()
        available_courses = [c for c in unique_courses if c not in excluded_courses]
        
        if len(available_courses) < target_course_count:
            # Not enough courses left for a full schedule
            return None
            
        # Cap the number of combinations to try
        max_course_combinations = 400
        
        # Generate course combinations (not section combinations yet)
        all_course_combos = list(combinations(available_courses, target_course_count))
        
        # If too many combinations, sample a subset
        if len(all_course_combos) > max_course_combinations:
            all_course_combos = random.sample(all_course_combos, max_course_combinations)
        
        print(f"Evaluating {len(all_course_combos)} course combinations")
        
        best_schedule = []
        best_score = -float('inf')
        
        # Track how many valid schedules we've found
        valid_schedules_found = 0
        max_valid_to_check = 10  # Limit to improve performance
        
        # Evaluate each course combination
        for course_combo in all_course_combos:
            # Get all possible section combinations
            section_options = [course_sections[course] for course in course_combo]
            
            # Limit sections per course to speed things up if there are many
            MAX_SECTIONS_PER_COURSE = 3
            limited_section_options = []
            for sections in section_options:
                if len(sections) > MAX_SECTIONS_PER_COURSE:
                    # Score each section
                    section_scores = [(section, calculate_individual_course_score(
                        section, 
                        student_strengths, 
                        section.get('is_in_plan', False)
                    )) for section in sections]
                    # Take the top sections by score
                    section_scores.sort(key=lambda x: x[1], reverse=True)
                    limited_section_options.append([s for s, _ in section_scores[:MAX_SECTIONS_PER_COURSE]])
                else:
                    limited_section_options.append(sections)
            
            # Generate all possible combinations of sections (one from each course)
            section_combos = list(product(*limited_section_options))
            
            # Cap the number of section combinations to try
            MAX_SECTION_COMBOS = 30
            if len(section_combos) > MAX_SECTION_COMBOS:
                section_combos = random.sample(section_combos, MAX_SECTION_COMBOS)
            
            # Check each section combination for conflicts
            for sections in section_combos:
                conflict = False
                schedule = []
                
                # Build schedule one course at a time, checking for conflicts
                for section in sections:
                    if any(has_conflict([existing], section) for existing in schedule):
                        conflict = True
                        break
                    schedule.append(section)
                
                if not conflict:
                    # Valid schedule found!
                    valid_schedules_found += 1
                    
                    # Score this schedule
                    score = calculate_schedule_score(schedule, student_strengths)
                    
                    if score > best_score:
                        best_score = score
                        best_schedule = schedule
                    
                    # Early exit if we found enough valid schedules
                    if valid_schedules_found >= max_valid_to_check or score > 80:
                        print(f"Found excellent schedule with score {score}, stopping early")
                        break
            
            # Exit early if we found a good schedule
            if best_schedule and best_score > 80:
                break
        
        # Try fallback approaches if needed
        if not best_schedule:
            # Try a different approach - build schedule course by course
            relaxed_schedule = []
            
            # Sort courses by score
            course_scores = []
            for course_code in available_courses:
                first_section = course_sections[course_code][0]  # Use first section for scoring
                is_in_plan = first_section.get('is_in_plan', False)
                score = calculate_individual_course_score(first_section, student_strengths, is_in_plan)
                course_scores.append((course_code, score))
            
            # Sort by score (descending)
            course_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Try to add courses one by one
            for course_code, _ in course_scores:
                if len(relaxed_schedule) >= target_course_count:
                    break
                    
                # Try each section of this course
                sections = course_sections[course_code]
                best_section = None
                best_section_conflicts = float('inf')
                
                for section in sections:
                    # Count conflicts with current schedule
                    conflict_count = sum(1 for existing in relaxed_schedule 
                                       if has_conflict([existing], section))
                    
                    # Select section with fewest conflicts
                    if conflict_count < best_section_conflicts:
                        best_section_conflicts = conflict_count
                        best_section = section
                
                # Add this section if it has at most 1 conflict
                if best_section and best_section_conflicts <= 1:
                    relaxed_schedule.append(best_section)
            
            if relaxed_schedule:
                print(f"Found relaxed schedule with {len(relaxed_schedule)} courses")
                best_schedule = relaxed_schedule
        
        # Last resort - just take top N courses with no conflict checking
        if not best_schedule:
            print("Using emergency fallback - selecting best sections regardless of conflicts")
            
            emergency_schedule = []
            course_scores = []
            
            # Score all courses
            for course_code in available_courses:
                # Find best section for each course
                best_section = max(
                    course_sections[course_code], 
                    key=lambda s: calculate_individual_course_score(
                        s, 
                        student_strengths, 
                        s.get('is_in_plan', False)
                    )
                )
                is_in_plan = best_section.get('is_in_plan', False)
                score = calculate_individual_course_score(best_section, student_strengths, is_in_plan)
                course_scores.append((best_section, score))
            
            # Take top courses
            course_scores.sort(key=lambda x: x[1], reverse=True)
            emergency_schedule = [section for section, _ in course_scores[:target_course_count]]
            
            if emergency_schedule:
                print(f"Emergency fallback returned {len(emergency_schedule)} courses")
                best_schedule = emergency_schedule
        
        # If we found a schedule, ensure it's properly sorted
        if best_schedule:
            # Sort by priority: major first, then credits
            best_schedule.sort(key=lambda c: (
                0 if c.get('is_major', False) else 1,  # Major courses first
                -c.get('credits', 3)  # Higher credits next
            ))
        
        return best_schedule
    
    # Generate first schedule (best overall)
    best_schedule = generate_single_schedule()
    if best_schedule:
        schedules.append(best_schedule)
        print(f"Generated schedule 1 with {len(best_schedule)} courses")
    
    # Generate additional schedules with diversity
    attempts = 0
    excluded_courses = set()
    
    # Try to exclude some courses from the first schedule to ensure diversity
    if best_schedule:
        # Exclude up to half of the courses from the first schedule
        excluded_count = min(len(best_schedule) // 2, 2)  # Exclude at most 2 courses
        for course in best_schedule[:excluded_count]:
            excluded_courses.add(course.get('course_code', ''))
    
    # Generate second schedule
    while len(schedules) < 2 and attempts < max_attempts:
        attempts += 1
        next_schedule = generate_single_schedule(excluded_courses)
        
        if not next_schedule:
            # Reset exclusions if we can't find a schedule
            excluded_courses = set()
            continue
            
        # Check diversity with existing schedules
        is_diverse = True
        for existing_schedule in schedules:
            diversity = calculate_diversity(existing_schedule, next_schedule)
            if diversity < min_diversity_threshold:
                is_diverse = False
                break
        
        if is_diverse:
            schedules.append(next_schedule)
            print(f"Generated schedule {len(schedules)} with {len(next_schedule)} courses")
            
            # Update excluded courses for the next schedule
            for course in next_schedule[:2]:
                excluded_courses.add(course.get('course_code', ''))
    
    # Generate third schedule
    attempts = 0
    while len(schedules) < 3 and attempts < max_attempts:
        attempts += 1
        next_schedule = generate_single_schedule(excluded_courses)
        
        if not next_schedule:
            # Reset exclusions if we can't find a schedule
            excluded_courses = set()
            continue
            
        # Check diversity with existing schedules
        is_diverse = True
        for existing_schedule in schedules:
            diversity = calculate_diversity(existing_schedule, next_schedule)
            if diversity < min_diversity_threshold:
                is_diverse = False
                break
        
        if is_diverse:
            schedules.append(next_schedule)
            print(f"Generated schedule {len(schedules)} with {len(next_schedule)} courses")
    
    # If we couldn't generate diverse schedules, just create more using random selections
    while len(schedules) < 3:
        # Try completely random approach
        random_courses = random.sample(unique_courses, min(target_course_count * 2, len(unique_courses)))
        random_excluded = set(unique_courses) - set(random_courses)
        
        next_schedule = generate_single_schedule(random_excluded)
        if next_schedule:
            schedules.append(next_schedule)
            print(f"Generated schedule {len(schedules)} with {len(next_schedule)} courses (random approach)")
    
    # Return the generated schedules
    return schedules  # Return single list instead of tuple

# Helper: Format schedule as HTML table
def format_schedule_as_table(schedule, option_number):
    """Format a schedule as an HTML table"""
    if not schedule:
        return f"<h3>Option {option_number}</h3><p>No courses available for this option.</p>"
    
    html = f"""
    <div class="schedule-option">
        <h3>Schedule Option {option_number}</h3>
        <table class="course-table">
            <thead>
                <tr>
                    <th>Course Code</th>
                    <th>Course Name</th>
                    <th>Section</th>
                    <th>Instructor</th>
                    <th>Class Times</th>
                    <th>Exam Date</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for course in schedule:
        # Format class times
        class_times = []
        for cls in course.get('classes', []):
            day = cls.get('day', '')
            time_from = cls.get('time_from', '')
            time_to = cls.get('time_to', '')
            location = cls.get('location', '')
            class_type = cls.get('class_type', '')
            
            if day and time_from and time_to:
                class_time = f"{day} {time_from}-{time_to}"
                if location:
                    class_time += f" ({location})"
                if class_type:
                    class_time += f" {class_type}"
                class_times.append(class_time)
        
        class_times_str = "<br>".join(class_times) if class_times else "Not specified"
        
        # Format exam date
        exam_date = course.get('exam_date', 'Not specified')
        
        html += f"""
            <tr>
                <td>{course.get('course_code', '')}</td>
                <td>{course.get('course_name', '')}</td>
                <td>{course.get('section', '')}</td>
                <td>{course.get('instructor', '')}</td>
                <td>{class_times_str}</td>
                <td>{exam_date}</td>
            </tr>
        """
    
    html += """
            </tbody>
        </table>
    </div>
    """
    
    return html