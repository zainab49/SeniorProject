from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Student, Enrollment
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

# Home page view
def home_page(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('login')

    try:
        student = Student.objects.get(student_id=student_id)
    except Student.DoesNotExist:
        return redirect('login')

    # Get all enrollments for this student
    enrollments = Enrollment.objects.filter(student=student)

    # Prepare real course data list
    courses_data = []

    for enrollment in enrollments:
        if enrollment.semester.lower() == 'first':
            course_id = enrollment.course_id.strip()
            course_info = None

            # Search all F-ending JSON files in courseSchedule
            json_folder = os.path.join(os.path.dirname(__file__), '..', 'Data', 'courseSchedule')
            json_folder = os.path.abspath(json_folder)

            for file in os.listdir(json_folder):
                if fnmatch.fnmatch(file, '*-F.json'):  # Match all first semester files
                    file_path = os.path.join(json_folder, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        try:
                            data = json.load(f)
                            for course in data:
                                if course.get('course_code', '').strip() == course_id:
                                    course_info = course
                                    break
                        except Exception as e:
                            print(f"Error reading {file_path}: {e}")
                if course_info:
                    break

            if course_info:
                courses_data.append({
                    'course_code': course_info['course_code'],
                    'course_name': course_info['course_name'],
                    'exam_date': course_info.get('exam_date', ''),
                    'exam_start': course_info.get('exam_time_start', ''),
                    'exam_end': course_info.get('exam_time_end', ''),
                    'section': course_info['sections'][0]['section_number'] if course_info.get('sections') else '',
                    'instructor': course_info['sections'][0]['instructor'] if course_info.get('sections') else '',
                    'credits': 3,  # Optional: change if you have real credit data
                })
   
    return render(request, 'Project/Home.html', {
         'student': student,
         'courses': courses_data})

# GPA Calculator page view
def gpa_calculator_page(request):
    return render(request, 'Project/gpa_calculator.html')

# GPA Improvement page view
def gpa_improvement_page(request):
    return render(request, 'Project/gpa_improvement.html')

# Schedule Suggestions page view
def schedule_suggestions_page(request):
    return render(request, 'Project/schedule_suggestions.html')
