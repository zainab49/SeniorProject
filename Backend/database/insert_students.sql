-- Student 1: Second Year Cybersecurity, CGPA 1.8
INSERT INTO Students (student_id, student_name, email, password, major, CGPA, MCGPA)
VALUES (
    '202108899', 
    'Al Mohamed Hasan Mansoori', 
    '2020108899@stu.uob.edu.bh', 
    'hashed_ali123',  -- Hash of "Student123"
    'B.Sc. in Cybersecurity 2021', 
    1.8, 
    1.9
);

-- Completed Courses (Year 1 Cybersecurity)
INSERT INTO StudentCourses (student_id, course_code, course_name, semester, credits, grade, is_major_course)
VALUES
(1, 'ITCS 113', 'Computer Programming I', 'Year 1 Semester 1', 3, 1.7, 1),
(1, 'ITNE 110', 'Intro to Computer & Network Tech', 'Year 1 Semester 1', 3, 2.0, 1),
(1, 'MATHS 101', 'Calculus I', 'Year 1 Semester 1', 3, 1.3, 0),
(1, 'ITCS 114', 'Computer Programming II', 'Year 1 Semester 2', 3, 2.3, 1);

-- Current Enrollment
INSERT INTO Enrollment (student_id, course_id, semester, grade)
VALUES
(1, 'ITCS 214', 'Year 2 Semester 3', NULL),
(1, 'ITNE 231', 'Year 2 Semester 3', NULL);

-- ------------------------------------------------------------
-- Student 2: Senior Network Engineering, CGPA 2.3/MCGPA 1.8
INSERT INTO Students (first_name, last_name, email, password, major, CGPA, MCGPA)
VALUES (
    'Fatima', 
    'Al-Khalifa', 
    'fatima.khalifa@example.com', 
    'hashed_fatima456',  -- Hash of "Student456"
    'B.Sc. in Network Engineering 2017', 
    2.3, 
    1.8
);

-- Completed Courses (Mixed grades)
INSERT INTO StudentCourses (student_id, course_code, course_name, semester, credits, grade, is_major_course)
VALUES
(2, 'ITNE 231', 'Computer Networks I', 'Year 2 Semester 3', 3, 1.0, 1),
(2, 'ITCS 214', 'Data Structures', 'Year 2 Semester 3', 3, 1.7, 1),
(2, 'ENGL 219', 'Technical Report Writing', 'Year 2 Semester 4', 3, 3.0, 0),
(2, 'PHYCS 101', 'General Physics I', 'Year 1 Semester 1', 4, 2.7, 0);

-- Current Enrollment (Year 4 Courses)
INSERT INTO Enrollment (student_id, course_id, semester, grade)
VALUES
(2, 'ITNE 480', 'Year 4 Semester 8', NULL),
(2, 'ITNE 481', 'Year 4 Semester 8', NULL);

-- ------------------------------------------------------------
-- Student 3: Third Year Software Engineering, CGPA 3.3
INSERT INTO Students (first_name, last_name, email, password, major, CGPA, MCGPA)
VALUES (
    'Ahmed', 
    'Al-Jasim', 
    'ahmed.jasim@example.com', 
    'hashed_ahmed789',  -- Hash of "Student789"
    'B.Sc. in Software Engineering 2024', 
    3.3, 
    3.5
);

-- Completed Courses (Excellent grades)
INSERT INTO StudentCourses (student_id, course_code, course_name, semester, credits, grade, is_major_course)
VALUES
(3, 'ITCS 214', 'Data Structures', 'Year 2 Semester 3', 3, 3.7, 1),
(3, 'ITSE 201', 'Intro to Software Engineering', 'Year 2 Semester 3', 3, 4.0, 1),
(3, 'ITCS 285', 'Database Management Systems', 'Year 2 Semester 4', 3, 3.3, 1),
(3, 'MATHS 205', 'Differential Equations', 'Year 3 Semester 5', 3, 3.0, 0);

-- Current Enrollment (Year 3 Courses)
INSERT INTO Enrollment (student_id, course_id, semester, grade)
VALUES
(3, 'ITCS 347', 'Year 3 Semester 6', NULL),
(3, 'ITSE 306', 'Year 3 Semester 6', NULL);