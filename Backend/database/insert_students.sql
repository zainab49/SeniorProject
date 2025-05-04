-- Student 1: Second Year Cybersecurity, CGPA 1.8
INSERT INTO Students (student_id, student_name, email, password, major, CGPA, MCGPA)
VALUES (
    '202108899', 
    'Ali Mohamed Hasan Mansoori', 
    '2020108899@stu.uob.edu.bh', 
    '1234',  -- Hash of "Student123"
    'B.Sc. in Cybersecurity 2021', 
    1.8, 
    1.9
);

-- ------------------------------------------------------------
-- Student 2: Senior Network Engineering, CGPA 2.3/MCGPA 1.8
INSERT INTO Students (student_id, student_name, email, password, major, CGPA, MCGPA)
VALUES (
    '202004477', 
    'Fatima Amjed Salman Khalifa', 
    '202004477@stu.uob.edu.bh', 
    '1234',  -- Hash of "Student456"
    'B.Sc. in Network Engineering 2017', 
    2.3, 
    1.8
);

-- ------------------------------------------------------------
-- Student 3: Third Year Software Engineering, CGPA 3.3
INSERT INTO Students (student_id, student_name, email, password, major, CGPA, MCGPA)
VALUES (
    '202308888',
    'Ahmed Ali Jasim Aqeel', 
    '202308888@stu.uob.edu.bh', 
    '1234',  -- Hash of "Student789"
    'B.Sc. in Software Engineering 2024', 
    3.3, 
    3.5
);

-- #Admin :
-- # username: admin
-- # email:admin@uob.edu.bh
-- # password: 12345678
-- #http://127.0.0.1:8000/admin/



-- class AcademicProgram(models.Model):
--     title = models.CharField(max_length=255)
--     year = models.CharField(max_length=10)
--     total_credits = models.IntegerField()
    
--     class Meta:
--         db_table = 'AcademicPrograms'
--         unique_together = ('title', 'year')  # Each program/year combination is unique

--     def __str__(self):
--         return f"{self.title} ({self.year})"

-- class ProgramComponent(models.Model):
--     COMPONENT_TYPES = [
--         ('UR', 'University Requirement'),
--         ('CR', 'College Requirement'),
--         ('MR', 'Major Requirement'),
--         ('ME', 'Major Elective'),
--         ('GSE', 'General Studies Elective'),
--     ]
    
--     program = models.ForeignKey(AcademicProgram, on_delete=models.CASCADE, related_name='components')
--     component_type = models.CharField(max_length=3, choices=COMPONENT_TYPES)
--     credits = models.IntegerField()
--     percentage = models.CharField(max_length=10)
--     notes = models.TextField(blank=True, null=True)
    
--     class Meta:
--         db_table = 'ProgramComponents'

-- class ProgramCourse(models.Model):
--     program = models.ForeignKey(AcademicProgram, on_delete=models.CASCADE, related_name='courses')
--     course_code = models.CharField(max_length=20)
--     course_title = models.CharField(max_length=255)
--     lecture_hours = models.IntegerField()
--     practical_hours = models.IntegerField()
--     credits = models.IntegerField()
--     course_type = models.CharField(max_length=3, choices=ProgramComponent.COMPONENT_TYPES)
--     prerequisite = models.CharField(max_length=255, blank=True, null=True)
--     major_gpa = models.BooleanField(default=False)
--     year = models.IntegerField()  # 1, 2, 3, or 4
--     semester = models.IntegerField()  # 1 or 2
    
--     class Meta:
--         db_table = 'ProgramCourses'
--         ordering = ['year', 'semester', 'course_code']