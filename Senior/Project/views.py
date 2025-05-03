from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Student, Enrollment , StudentCourse
import json 
import os
import fnmatch

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
def home_page(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('login')

    try:
        student = Student.objects.get(student_id=student_id)
    except Student.DoesNotExist:
        return redirect('login')

    enrollments = Enrollment.objects.filter(student=student)
    courses_data = []
    not_found_courses = []


    # JSON course files location
    json_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), 'Data', 'courseSchedule'))


    for enrollment in enrollments:
        course_id = enrollment.course_id.strip()
        section_number = enrollment.section.strip()
        course_info = None

        # Match only first semester JSON files
        for file in os.listdir(json_folder):
            if file.endswith('F.json'):
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
                                            'credits': 3,
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
        'not_found_courses': not_found_courses
    })

# GPA Calculator page view
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

        # Calculate SGPA (from Enrollment using user-selected grades)
        sgpa_points = 0
        sgpa_credits = 0

        for i, enrollment in enumerate(enrollments):
            grade = grades[i]
            gpa_value = GRADE_MAP.get(grade)
            if gpa_value is None:
                continue

            credit = enrollment.Credits
            sgpa_points += gpa_value * credit
            sgpa_credits += credit

        sgpa = round(sgpa_points / sgpa_credits, 2) if sgpa_credits else 0.0

        # Calculate CGPA (all student courses)
        total_points = 0
        total_credits = 0
        for course in student_courses:
            gpa_value = GRADE_MAP.get(course.grade)
            if gpa_value is not None:
                total_points += gpa_value * course.credits
                total_credits += course.credits
        cgpa = round(total_points / total_credits, 2) if total_credits else 0.0

        # Calculate MGPA (only major courses)
        major_points = 0
        major_credits = 0
        for course in student_courses:
            if course.is_major_course:
                gpa_value = GRADE_MAP.get(course.grade)
                if gpa_value is not None:
                    major_points += gpa_value * course.credits
                    major_credits += course.credits
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


# GPA Improvement page view
def gpa_improvement_page(request):
    return render(request, 'Project/gpa_improvement.html')

# Schedule Suggestions page view
def schedule_suggestions_page(request):
    return render(request, 'Project/schedule_suggestions.html')
