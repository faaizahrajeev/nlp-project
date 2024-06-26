"""
signup(name, email, pass_unhashed, repeatpass_unhashed, teacher_flag) -> return userid
login(email, pass-unhashed) -> return userid

TEACHER FUNCTIONS
addcourse(userid, course name) -> return courseid
addassignment(courseid, name, section, duedate) -> return assignmentid
addstudenttocourse(studentuserid, courseid) -> return success/failure
addquestiontoassignment(assignmentid, question, answer) -> return questionid

STUDENT FUNCTIONS
getcourses(userid) -> return list of courses
getassignments(userid, courseid) -> return list of assignments, and separate list of completed assignments incl scores
getquestions(userid, assignmentid) -> return array of questions
makesubmission(assignmentid, answers-list) -> return list of submissionids

BACKEND FUNCTIONS
storereport(submissionid, reportpath, score) -> return success/failure
"""

import sqlite3
import hashlib

# Function to create a connection to the database
def create_connection(db_file="database.db"):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except sqlite3.Error as e:
        print(e)
    
    return conn

# Function to execute SQL commands
def execute_sql(conn, sql):
    try:
        c = conn.cursor()
        c.execute(sql)
        conn.commit()
        print("Command executed successfully")
    except sqlite3.Error as e:
        print(e)

# Function to hash the password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to create tables
def create_tables(conn):
    try:
        create_users_table = """
            CREATE TABLE IF NOT EXISTS Users (
                UserID INTEGER PRIMARY KEY AUTOINCREMENT,
                Name TEXT NOT NULL,
                Email TEXT UNIQUE NOT NULL,
                Password TEXT NOT NULL,
                IsTeacher INTEGER DEFAULT 0 CHECK (IsTeacher IN (0, 1))
            )
        """
        create_courses_table = """
            CREATE TABLE IF NOT EXISTS Courses (
                CourseID INTEGER PRIMARY KEY AUTOINCREMENT,
                UserID INTEGER,
                CourseName TEXT NOT NULL,
                FOREIGN KEY (UserID) REFERENCES Users(UserID)
            )
        """
        create_assignments_table = """
            CREATE TABLE IF NOT EXISTS Assignments (
                AssignmentID INTEGER PRIMARY KEY AUTOINCREMENT,
                CourseID INTEGER,
                Name TEXT NOT NULL,
                Section TEXT,
                DueDate DATE,
                FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
            )
        """
        create_questions_table = """
            CREATE TABLE IF NOT EXISTS Questions (
                QuestionID INTEGER PRIMARY KEY AUTOINCREMENT,
                AssignmentID INTEGER,
                Question TEXT NOT NULL,
                Answer TEXT NOT NULL,
                FOREIGN KEY (AssignmentID) REFERENCES Assignments(AssignmentID)
            )
        """
        create_submissions_table = """
            CREATE TABLE IF NOT EXISTS Submissions (
                SubmissionID INTEGER PRIMARY KEY AUTOINCREMENT,
                AssignmentID INTEGER,
                UserID INTEGER,
                SubmissionDate DATE DEFAULT CURRENT_DATE,
                ReportPath TEXT DEFAULT NULL,
                AnswerText TEXT,
                Score INTEGER DEFAULT 0,
                FOREIGN KEY (AssignmentID) REFERENCES Assignments(AssignmentID),
                FOREIGN KEY (UserID) REFERENCES Users(UserID)
            )
        """
        create_enrollment_table = """
            CREATE TABLE IF NOT EXISTS Enrollments (
                EnrollmentID INTEGER PRIMARY KEY AUTOINCREMENT,
                StudentUserID INTEGER,
                CourseID INTEGER,
                FOREIGN KEY (StudentUserID) REFERENCES Users(UserID),
                FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
            )
        """
        execute_sql(conn, create_users_table)
        execute_sql(conn, create_courses_table)
        execute_sql(conn, create_assignments_table)
        execute_sql(conn, create_questions_table)
        execute_sql(conn, create_submissions_table)
        execute_sql(conn, create_enrollment_table)

    except sqlite3.Error as e:
        print(e)

# Function to sign up a user
def signup(conn, name, email, password, repeat_password, is_teacher):
    if password != repeat_password:
        print("Passwords do not match.")
        return None
    
    hashed_password = hash_password(password)
    
    try:
        sql = "INSERT INTO Users (Name, Email, Password, IsTeacher) VALUES (?, ?, ?, ?)"
        cursor = conn.cursor()
        cursor.execute(sql, (name, email, hashed_password, is_teacher))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(e)
        return None

# Function to log in a user
def login(conn, email, password):
    try:
        hashed_password = hash_password(password)
        sql = "SELECT UserID FROM Users WHERE Email = ? AND Password = ?"
        cursor = conn.cursor()
        cursor.execute(sql, (email, hashed_password))
        row = cursor.fetchone()
        if row:
            sql = f"SELECT UserID, IsTeacher, name FROM Users WHERE UserID = {row[0]}"
            cursor.execute(sql)
            return cursor.fetchone()
        else:
            return None
    except sqlite3.Error as e:
        print(e)
        return None

# Function to add a course
def add_course(conn, user_id, course_name):
    try:
        sql = "INSERT INTO Courses (UserID, CourseName) VALUES (?, ?)"
        cursor = conn.cursor()
        cursor.execute(sql, (user_id, course_name))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(e)
        return None

# Function to add an assignment
def add_assignment(conn, course_id, name, section, due_date):
    try:
        sql = "INSERT INTO Assignments (CourseID, Name, Section, DueDate) VALUES (?, ?, ?, ?)"
        cursor = conn.cursor()
        cursor.execute(sql, (course_id, name, section, due_date))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(e)
        return None

def get_student_user_id(conn, email):
    try:
        sql = "SELECT UserID FROM Users WHERE Email = ? and IsTeacher = 0"
        cursor = conn.cursor()
        cursor.execute(sql, (email,))
        row = cursor.fetchone()
        if row is None:
            return None
        return row[0]
    except sqlite3.Error as e:
        print(e)
        return None

# Function to add a student to a course
def add_student_to_course(conn, student_user_id, course_id):
    try:
        sql = "INSERT INTO Enrollments (StudentUserID, CourseID) VALUES (?, ?)"
        cursor = conn.cursor()
        cursor.execute(sql, (student_user_id, course_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(e)
        return False

# Function to add a question to an assignment
def add_question_to_assignment(conn, assignment_id, question, answer, score):
    try:
        sql = "INSERT INTO Questions (AssignmentID, Question, Answer, Score) VALUES (?, ?, ?, ?)"
        cursor = conn.cursor()
        cursor.execute(sql, (assignment_id, question, answer, score))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(e)
        return None
    
def get_students(conn, course_id):
    try:
        sql = "SELECT UserID, Name, Email FROM Users WHERE UserID IN (SELECT StudentUserID FROM Enrollments WHERE CourseID = ?)"
        cursor = conn.cursor()
        cursor.execute(sql, (course_id,))
        rows = cursor.fetchall()
        rows = [list(row) for row in rows]
        sql = "SELECT SUM(Score) FROM Questions WHERE AssignmentID IN (SELECT AssignmentID FROM Assignments WHERE CourseID = ?)"
        cursor.execute(sql, (course_id,))
        total = cursor.fetchone()
        if total[0] is None:
            total = (0,)
        for row in rows:
            sql = "SELECT SUM(Score) FROM Submissions WHERE UserID = ? AND QuestionID in (SELECT QuestionID FROM Questions WHERE AssignmentID IN (SELECT AssignmentID FROM Assignments WHERE CourseID = ?))"
            cursor.execute(sql, (row[0], course_id))
            score = cursor.fetchone()
            if score[0] is None:
                score = (0,)
            row.append(f"{round(float(score[0]),2)}/{round(float(total[0]),2)}")
        return rows
    except sqlite3.Error as e:
        print(e)
        return None

def get_course_name(conn, course_id):
    try:
        sql = "SELECT CourseName FROM Courses WHERE CourseID = ?"
        cursor = conn.cursor()
        cursor.execute(sql, (course_id,))
        row = cursor.fetchone()
        return row[0]
    except sqlite3.Error as e:
        print(e)
        return None

# Function to get courses of a user
def get_courses(conn, user_id):
    try:
        sql = "SELECT CourseID, CourseName FROM Courses WHERE UserID = ?"
        cursor = conn.cursor()
        cursor.execute(sql, (user_id,))
        rows = cursor.fetchall()
        return rows
    except sqlite3.Error as e:
        print(e)
        return None

def get_student_courses(conn, user_id):
    try:
        sql = "SELECT CourseID, CourseName FROM Courses WHERE CourseID IN (SELECT CourseID FROM Enrollments WHERE StudentUserID = ?)"
        cursor = conn.cursor()
        cursor.execute(sql, (user_id,))
        rows = cursor.fetchall()
        return rows
    except sqlite3.Error as e:
        print(e)
        return None

# Function to get assignments of a course
def get_assignments(conn, course_id):
    try:
        sql = "SELECT AssignmentID, Name, Section, DueDate FROM Assignments WHERE CourseID = ?"
        cursor = conn.cursor()
        cursor.execute(sql, (course_id,))
        rows = cursor.fetchall()
        return rows
    except sqlite3.Error as e:
        print(e)
        return None

def get_incomplete_assignments(conn, course_id, student_id):
    try:
        sql = "SELECT AssignmentID, Name, Section, DueDate FROM Assignments WHERE CourseID = ? AND AssignmentID NOT IN (SELECT AssignmentID from Questions where QuestionID in (SELECT QuestionID FROM Submissions WHERE UserID = ?))"
        cursor = conn.cursor()
        cursor.execute(sql, (course_id, student_id))
        rows = cursor.fetchall()
        return rows
    except sqlite3.Error as e:
        print(e)
        return None

import json
def get_submissions(conn, assignment_id, student_id):
    try:
        sql = "SELECT SubmissionID, ReportData FROM Submissions WHERE UserID = ? AND QuestionID in (SELECT QuestionID from Questions where AssignmentID = ?)"
        cursor = conn.cursor()
        cursor.execute(sql, (student_id, assignment_id))
        rows = cursor.fetchall()
        rows = [list(row) for row in rows]
        for row in rows:
            row[1] = json.loads(row[1])
            sql = "SELECT Question FROM Questions WHERE QuestionID IN (SELECT QuestionID FROM Submissions WHERE SubmissionID = ?)"
            cursor.execute(sql, (row[0],))
            question = cursor.fetchone()
            row.append(question[0])
        return rows
    except sqlite3.Error as e:
        print(e)
        return None

def get_completed_assignments(conn, course_id, student_id):
    try:
        sql = "SELECT AssignmentID, Name, Section, DueDate FROM Assignments WHERE CourseID = ? AND AssignmentID IN (SELECT AssignmentID from Questions where QuestionID in (SELECT QuestionID FROM Submissions WHERE UserID = ?))"
        cursor = conn.cursor()
        cursor.execute(sql, (course_id, student_id))
        rows = cursor.fetchall()
        rows = [list(row) for row in rows]
        for row in rows:
            sql = "SELECT AVG(Score) FROM Submissions WHERE UserID = ? AND QuestionID in (SELECT QuestionID from Questions where AssignmentID = ?)"
            cursor.execute(sql, (student_id, row[0]))
            score = cursor.fetchone()
            row.append(round(float(score[0]),2))
        return rows
    except sqlite3.Error as e:
        print(e)
        return None

def get_all_reports(conn, assignment_id, student_id):
    try:
        sql = "SELECT ReportPath FROM Submissions WHERE UserID = ? AND QuestionID in (SELECT QuestionID from Questions where AssignmentID = ?)"
        cursor = conn.cursor()
        cursor.execute(sql, (student_id, assignment_id))
        rows = cursor.fetchall()
        rows = [row[0] for row in rows]
        return rows
    except sqlite3.Error as e:
        print(e)
        return None

def get_question(conn, questionid):
    try:
        sql = "SELECT Question, Answer, Score FROM Questions WHERE QuestionID = ?"
        cursor = conn.cursor()
        cursor.execute(sql, (questionid,))
        row = cursor.fetchone()
        return row
    except sqlite3.Error as e:
        print(e)
        return None

import zipfile
import uuid
def zip_all_reports(reportpathlist):
    if len(reportpathlist) == 1:
        return reportpathlist[0]
    path = f'{uuid.uuid4()}.zip'
    with zipfile.ZipFile("static/data/"+path, 'w') as z:
        for reportpath in reportpathlist:
            z.write("static/data/"+reportpath, reportpath)
    return path

def get_teacher_name(conn, assignment_id):
    try:
        sql = "SELECT Name FROM Users WHERE UserID IN (SELECT UserID FROM Courses WHERE CourseID IN (SELECT CourseID FROM Assignments WHERE AssignmentID = ?))"
        cursor = conn.cursor()
        cursor.execute(sql, (assignment_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return row[0]
    except sqlite3.Error as e:
        print(e)
        return None

def get_assignment_details(conn, assignment_id):
    try:
        sql = "SELECT Name, CourseID FROM Assignments WHERE AssignmentID = ?"
        cursor = conn.cursor()
        cursor.execute(sql, (assignment_id,))
        row = cursor.fetchone()
        return row
    except sqlite3.Error as e:
        print(e)
        return None

def delete_all_questions(conn, assignment_id):
    try:
        sql = "DELETE FROM Questions WHERE AssignmentID = ?"
        cursor = conn.cursor()
        cursor.execute(sql, (assignment_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(e)
        return False
    
# Function to get questions of an assignment
def get_questions(conn, assignment_id):
    try:
        sql = "SELECT QuestionID, Question, Answer, Score FROM Questions WHERE AssignmentID = ?"
        cursor = conn.cursor()
        cursor.execute(sql, (assignment_id,))
        rows = cursor.fetchall()
        return rows
    except sqlite3.Error as e:
        print(e)
        return None

def get_assignment(conn, assignment_id):
    try:
        sql = "SELECT CourseID, Name, Section, DueDate FROM Assignments WHERE AssignmentID = ?"
        cursor = conn.cursor()
        cursor.execute(sql, (assignment_id,))
        row = cursor.fetchone()
        return row
    except sqlite3.Error as e:
        print(e)
        return None

# Function to make a submission
def make_submission(conn, questionid, user_id, answer):
    try:
        sql = "INSERT INTO Submissions (QuestionID, UserID, AnswerText) VALUES (?, ?, ?)"
        cursor = conn.cursor()
        cursor.execute(sql, (questionid, user_id, answer))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(e)
        return None

# Function to store a report
def store_report_data(conn, submission_id, data, score):
    try:
        sql = "UPDATE Submissions SET ReportData = ?, Score = ? WHERE SubmissionID = ?"
        cursor = conn.cursor()
        cursor.execute(sql, (data, score, submission_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(e)
        return False

def main():
    database = "database.db"
    conn = create_connection(database)
    with conn:
        # Create tables
        # create_tables(conn)

        user_id = signup(conn, "John Doe", "john@example.com", "password", "password", 0)
        if user_id:
            print("User signed up successfully. UserID:", user_id)

        # Test login
        logged_in_user_id = login(conn, "john@example.com", "password")
        if logged_in_user_id:
            print("User logged in successfully. UserID:", logged_in_user_id)

        # Test add_course
        course_id = add_course(conn, logged_in_user_id, "Mathematics")
        if course_id:
            print("Course added successfully. CourseID:", course_id)

        # Test add_assignment
        assignment_id = add_assignment(conn, course_id, "Assignment 1", "Section A", "2024-05-05")
        if assignment_id:
            print("Assignment added successfully. AssignmentID:", assignment_id)

        # Test add_question_to_assignment
        question_id = add_question_to_assignment(conn, assignment_id, "What is 2+2?", "4")
        if question_id:
            print("Question added successfully. QuestionID:", question_id)

        # Test get_courses
        courses = get_courses(conn, logged_in_user_id)
        if courses:
            print("Courses:")
            for course in courses:
                print(course)

        # Test get_assignments
        assignments = get_assignments(conn, logged_in_user_id, course_id)
        if assignments:
            print("Assignments:")
            for assignment in assignments:
                print(assignment)

        # Test get_questions
        questions = get_questions(conn, assignment_id)
        if questions:
            print("Questions:")
            for question in questions:
                print(question)

        # Test make_submission
        submission_ids = make_submission(conn, assignment_id, logged_in_user_id, ["4"])
        if submission_ids:
            print("Submission made successfully. SubmissionIDs:", submission_ids)

        # Test store_report
        if submission_ids:
            for submission_id in submission_ids:
                success = store_report(conn, submission_id, "/path/to/report.pdf", 90)
                if success:
                    print("Report stored successfully for SubmissionID:", submission_id)
                else:
                    print("Failed to store report for SubmissionID:", submission_id)

if __name__ == '__main__':
    main()
    