from django.db import models

class Student(models.Model):
    student_id = models.AutoField(primary_key=True)
    student_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    major = models.CharField(max_length=255)
    CGPA = models.FloatField(default=0.0)
    MCGPA = models.FloatField(default=0.0)

    class Meta:
        db_table = 'Students'


class StudentCourse(models.Model):
    record_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course_code = models.CharField(max_length=100)
    course_name = models.CharField(max_length=255)
    semester = models.CharField(max_length=50)
    credits = models.IntegerField()
    grade = models.CharField(max_length=10)
    is_major_course = models.BooleanField(default=False)
    attempt = models.IntegerField(default=1)
    previous_grade = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'StudentCourses'


class Enrollment(models.Model):
    enrollment_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course_id = models.CharField(max_length=100)
    section = models.CharField(max_length=10, default='01')
    is_major_course = models.BooleanField(default=False)
    semester = models.CharField(max_length=50)

    class Meta:
        db_table = 'Enrollment'
