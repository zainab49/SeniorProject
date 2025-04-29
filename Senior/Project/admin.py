from django.contrib import admin
from .models import Student, StudentCourse, Enrollment

admin.site.register(Student)
admin.site.register(StudentCourse)
admin.site.register(Enrollment)