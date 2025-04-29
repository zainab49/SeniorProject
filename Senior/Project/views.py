from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Student

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
            return redirect('home')  # go to home after login
        except Student.DoesNotExist:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'Project/login.html')

# Home page view
def home_page(request):
    student_name = request.session.get('student_name', 'Guest')  # Default to Guest if no session
    return render(request, 'Project/Home.html', {'student_name': student_name})
def gpa_calculator_page(request):
    return render(request, 'Project/gpa_calculator.html')

def gpa_improvement_page(request):
    return render(request, 'Project/gpa_improvement.html')

def schedule_suggestions_page(request):
    return render(request, 'Project/schedule_suggestions.html')
