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