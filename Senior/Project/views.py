from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Avg, Sum, Count  # Add other imports as needed
from .models import Student, Enrollment , StudentCourse 
import json 
import os
import fnmatch
from .ai_schedule import generate_course_schedule


from django.shortcuts import render
def crash_test(request):
    raise Exception("Simulated server crash")



# Login view
def login_page(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            student = Student.objects.get(email=email, password=password)
            # Save info in session
            request.session['student_id'] = student.student_id
            request.session['student_name'] = student.student_name
            return redirect('home')  # Go to home after login
        except Student.DoesNotExist:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'Project/login.html')



#logout view
def logout_view(request):
    request.session.flush()  # Clears the session (logs the user out)
    return redirect('login')  # Redirect to login page

# Home page view
# Home page view with credit calculation and academic status
def home_page(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('login')

    try:
        student = Student.objects.get(student_id=student_id)
    except Student.DoesNotExist:
        return redirect('login')

    # Get current enrollments
    enrollments = Enrollment.objects.filter(student=student)
    
    # Get completed courses
    completed_courses = StudentCourse.objects.filter(student=student)
    
    # Calculate total completed credits (only count passed courses)
    passing_grades = ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D"]
    completed_credits = 0
    for course in completed_courses:
        if course.grade in passing_grades:
            completed_credits += course.credits
    
    # Calculate currently registered credits
    registered_credits = sum(enrollment.Credits for enrollment in enrollments)
    
    # Determine total required credits based on major
    major = student.major.lower()
    if "cybersecurity" in major:
        total_credits = 132
    elif "network engineering" in major:
        total_credits = 134
    elif "software engineering" in major:
        total_credits = 134
    else:
        # Default if we can't determine the major
        total_credits = 134
    
    # Calculate remaining credits
    remaining_credits = total_credits - completed_credits
    
    # Calculate completion percentage
    completed_percentage = int((completed_credits / total_credits) * 100)
    
    # Determine academic status based on CGPA
    if remaining_credits < 20:
        academic_status = "Senior Student"
    elif student.CGPA >= 3.0:
        academic_status = "Excellent Student"
    elif student.CGPA >= 2.0:
        academic_status = "Normal Student"
    else:
        academic_status = "Under Probation"

    # Process course data
    courses_data = []
    not_found_courses = []

    # JSON course files location
    json_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), 'Data', 'courseSchedule'))

    for enrollment in enrollments:
        course_id = enrollment.course_id.strip()
        section_number = enrollment.section.strip()
        course_info = None

        # Match course files
        for file in os.listdir(json_folder):
            if file.endswith('F.json'):  # First semester files
                file_path = os.path.join(json_folder, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for course in data:
                            if course.get('course_code', '').strip().lower() == course_id.lower():
                                for sec in course.get('sections', []):
                                    if sec.get('section_number', '').strip() == section_number:
                                        course_info = {
                                            'course_code': course.get('course_code', ''),
                                            'course_name': course.get('course_name', ''),
                                            'exam_date': course.get('exam_date', ''),
                                            'section': sec.get('section_number', ''),
                                            'instructor': sec.get('instructor', ''),
                                            'credits': 3,  # Default or you can get from the course data
                                            'classes': sec.get('classes', [])
                                        }
                                        break
                            if course_info:
                                break
                    if course_info:
                        break
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

        # If course was found, add to homepage data
        if course_info:
            courses_data.append(course_info)
        else:
            not_found_courses.append(f"{course_id} - Section {section_number}")

    return render(request, 'Project/Home.html', {
        'student': student,
        'courses': courses_data,
        'not_found_courses': not_found_courses,
        'completed_credits': completed_credits,
        'registered_credits': registered_credits,
        'total_credits': total_credits,
        'remaining_credits': remaining_credits,
        'completed_percentage': completed_percentage,
        'academic_status': academic_status
    })
#------------------------------------------------------------------------------------------------------------
# GPA Calculator page view

def calculate_and_update_gpa(student):
    """
    Calculates and updates the student's CGPA and MGPA in the database
    """
    # Get all completed courses
    student_courses = StudentCourse.objects.filter(student=student)
    
    # Calculate CGPA (all courses)
    total_points = 0
    total_credits = 0
    major_points = 0
    major_credits = 0
    
    for course in student_courses:
        grade_value = GRADE_MAP.get(course.grade, 0)
        if grade_value is not None:
            total_points += grade_value * course.credits
            total_credits += course.credits
            
            if course.is_major_course:
                major_points += grade_value * course.credits
                major_credits += course.credits
    
    # Calculate GPAs
    cgpa = round(total_points / total_credits, 2) if total_credits else 0.0
    mgpa = round(major_points / major_credits, 2) if major_credits else 0.0
    
    # Update student record
    student.CGPA = cgpa
    student.MGPA = mgpa
    student.save()
    
    return cgpa, mgpa

    
GRADE_MAP = {
    "A": 4.00, "A-": 3.67, "B+": 3.33, "B": 3.00, "B-": 2.67,
    "C+": 2.33, "C": 2.00, "C-": 1.67, "D+": 1.33, "D": 1.00, "F": 0.00
}

def gpa_calculator_page(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('login')

    student = Student.objects.get(student_id=student_id)
    enrollments = Enrollment.objects.filter(student=student)
    student_courses = StudentCourse.objects.filter(student=student)
    grade_options = list(GRADE_MAP.keys())

    sgpa = cgpa = mgpa = None

    if request.method == 'POST':
        grades = request.POST.getlist('grade')
        credits = request.POST.getlist('credit')
        majors = request.POST.getlist('major')

        sgpa_points = 0
        sgpa_credits = 0
        total_points = 0
        total_credits = 0
        major_points = 0
        major_credits = 0

        for grade, credit, major in zip(grades, credits, majors):
            try:
                credit = int(credit)
            except ValueError:
                continue  # Skip invalid inputs

            is_major = major == '1'
            gpa_value = GRADE_MAP.get(grade)

            if gpa_value is None:
                continue

            # SGPA (just this semester)
            sgpa_points += gpa_value * credit
            sgpa_credits += credit

            # CGPA
            total_points += gpa_value * credit
            total_credits += credit

            # MGPA
            if is_major:
                major_points += gpa_value * credit
                major_credits += credit

        # Add completed courses from DB
        for course in student_courses:
            gpa_value = GRADE_MAP.get(course.grade)
            if gpa_value is not None:
                total_points += gpa_value * course.credits
                total_credits += course.credits
                if course.is_major_course:
                    major_points += gpa_value * course.credits
                    major_credits += course.credits

        # Final GPA calculations
        sgpa = round(sgpa_points / sgpa_credits, 2) if sgpa_credits else 0.0
        cgpa = round(total_points / total_credits, 2) if total_credits else 0.0
        mgpa = round(major_points / major_credits, 2) if major_credits else 0.0

        return render(request, 'Project/gpa_calculator.html', {
            'student': student,
            'enrollments': enrollments,
            'grade_options': grade_options,
            'grades': grades,
            'sgpa': sgpa,
            'mgpa': mgpa,
            'cgpa': cgpa,
        })

    return render(request, 'Project/gpa_calculator.html', {
        'student': student,
        'enrollments': enrollments,
        'grade_options': grade_options,
    })

#------------------------------------------------------------------------------------------------------------
# GPA Improvement page view
# GPA value mapping
GRADE_MAP = {
    "A": 4.00, "A-": 3.67, "B+": 3.33, "B": 3.00, "B-": 2.67,
    "C+": 2.33, "C": 2.00, "C-": 1.67, "D+": 1.33, "D": 1.00, "F": 0.00
}

# Map GPA values back to letter grades for target recommendations
REVERSE_GRADE_MAP = {
    4.00: "A", 3.67: "A-", 3.33: "B+", 3.00: "B", 2.67: "B-",
    2.33: "C+", 2.00: "C", 1.67: "C-", 1.33: "D+", 1.00: "D", 0.00: "F"
}

def gpa_improvement_page(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('login')

    try:
        student = Student.objects.get(student_id=student_id)
    except Student.DoesNotExist:
        return redirect('login')
    
    # Get student's course history
    student_courses = StudentCourse.objects.filter(student=student).order_by('semester')
    
    # Get current enrollments
    current_enrollments = Enrollment.objects.filter(student=student)
    
    # Add grade value to each course for easier processing
    for course in student_courses:
        course.grade_value = GRADE_MAP.get(course.grade, 0)
    
    # Calculate completed credits (only passed courses)
    passing_grades = ["A", "A-", "B+", "B", "C+", "C", "C-", "D+", "D"]
    completed_credits = sum(course.credits for course in student_courses if course.grade in passing_grades)
    
    # Calculate total points earned
    total_points_earned = sum(course.grade_value * course.credits for course in student_courses)
    
    # Find courses with grades below C (candidates for retaking)
    retake_candidates = [course for course in student_courses if course.grade_value < 2.0]  # Below C
    
    # Calculate potential GPA improvement for each retake candidate
    retake_courses = []
    for course in retake_candidates:
        # Calculate current impact on GPA
        current_contribution = course.grade_value * course.credits
        
        # Calculate potential improvement with a better grade
        # Target at least a C (2.0) or B (3.0) depending on current GPA
        target_grade_value = 3.0 if student.CGPA >= 2.0 else 2.0
        potential_contribution = target_grade_value * course.credits
        
        # Calculate GPA improvement
        improvement = (potential_contribution - current_contribution) / completed_credits
        
        # Find corresponding letter grade
        target_letter_grade = next((grade for grade, value in GRADE_MAP.items() if value >= target_grade_value), "B")
        
        # Add to retake list
        retake_courses.append({
            'course_code': course.course_code,
            'course_name': course.course_name,
            'credits': course.credits,
            'grade': course.grade,
            'grade_value': course.grade_value,
            'target_grade': target_letter_grade,
            'target_grade_value': target_grade_value,
            'improvement': improvement
        })
    
    # Sort retake courses by potential improvement
    retake_courses.sort(key=lambda x: x['improvement'], reverse=True)
    
    # Set target CGPA based on current CGPA
    if student.CGPA < 2.0:
        target_cgpa = 2.0  # Get to good standing
    elif student.CGPA < 3.0:
        target_cgpa = 3.0  # Get to excellent standing
    else:
        target_cgpa = min(4.0, student.CGPA + 0.25)  # Improve by 0.25 or max out at 4.0
    
    # Calculate minimum grades needed for current courses
    
    # Current total points and credits
    current_points = total_points_earned
    current_credits = completed_credits
    
    # Calculate points needed to reach target CGPA
    current_enrollments_credits = sum(enrollment.Credits for enrollment in current_enrollments)
    
    # Total credits after this semester
    future_total_credits = current_credits + current_enrollments_credits
    
    # Total points needed for target CGPA
    target_total_points = target_cgpa * future_total_credits
    
    # Additional points needed this semester
    additional_points_needed = target_total_points - current_points
    
    # Calculate average GPA needed this semester
    if current_enrollments_credits > 0:
        average_gpa_needed = additional_points_needed / current_enrollments_credits
    else:
        average_gpa_needed = 0
    
    # Set minimum grades for each current course
    for enrollment in current_enrollments:
        # If average GPA needed is unrealistic, adjust target
        adjusted_gpa_needed = min(4.0, max(1.0, average_gpa_needed))
        
        # Find the letter grade closest to the needed GPA
        closest_grade_value = min(GRADE_MAP.values(), key=lambda x: abs(x - adjusted_gpa_needed))
        closest_grade = next(grade for grade, value in GRADE_MAP.items() if value == closest_grade_value)
        
        enrollment.min_grade = closest_grade
    
    # Generate semester GPA history for reference
    semester_data = {}
    for course in student_courses:
        if course.semester not in semester_data:
            semester_data[course.semester] = {
                'total_points': 0,
                'total_credits': 0
            }
        
        semester_data[course.semester]['total_points'] += course.grade_value * course.credits
        semester_data[course.semester]['total_credits'] += course.credits
    
    # Calculate semester GPAs
    semesters = []
    cgpa_history = []
    
    for semester, data in sorted(semester_data.items()):
        if data['total_credits'] > 0:
            semester_gpa = data['total_points'] / data['total_credits']
            semesters.append(semester)
            cgpa_history.append(round(semester_gpa, 2))
    
    context = {
        'student': student,
        'student_courses': student_courses,
        'completed_credits': completed_credits,
        'target_cgpa': target_cgpa,
        'retake_courses': retake_courses,
        'current_courses': current_enrollments,
        'semesters': json.dumps(semesters),
        'cgpa_history': json.dumps(cgpa_history)
    }
    
    return render(request, 'Project/gpa_improvement.html', context)
#---------------------------------------------------------------------------------------------------------

# Schedule Suggestions page view


def schedule_suggestions(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('login')  # Redirect to login page if not logged in

    try:
        student = Student.objects.get(student_id=student_id)
    except Student.DoesNotExist:
        return redirect('login')  # Fallback in case student not found

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    schedule_dir = os.path.join(BASE_DIR, 'Data', 'courseSchedule')
    plan_dir = os.path.join(BASE_DIR, 'Data', 'Programs')

    # Generate multiple course schedules
    schedule_options = generate_course_schedule(student, schedule_dir, plan_dir)
    
    # Make sure we always have 3 options (even if some are empty)
    while len(schedule_options) < 3:
        schedule_options.append([])

    return render(request, 'Project/schedule_suggestions.html', {
        'schedule_options': schedule_options,
        'max_allowed': 6,
        'min_allowed': 4
    })