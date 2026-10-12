import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'catalog.db')

def create_tables(conn):
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT UNIQUE NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS instructors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            office TEXT,
            department_id INTEGER NOT NULL,
            FOREIGN KEY (department_id) REFERENCES departments(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            credits INTEGER NOT NULL,
            instructor_id INTEGER,
            department_id INTEGER NOT NULL,
            FOREIGN KEY (instructor_id) REFERENCES instructors(id),
            FOREIGN KEY (department_id) REFERENCES departments(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prerequisites (
            course_id INTEGER NOT NULL,
            prerequisite_id INTEGER NOT NULL,
            PRIMARY KEY (course_id, prerequisite_id),
            FOREIGN KEY (course_id) REFERENCES courses(id),
            FOREIGN KEY (prerequisite_id) REFERENCES courses(id)
        )
    ''')
    
    conn.commit()

def seed_data(conn):
    cursor = conn.cursor()
    
    # Check if already seeded
    cursor.execute('SELECT COUNT(*) FROM departments')
    if cursor.fetchone()[0] > 0:
        print("Database already seeded, skipping...")
        return
    
    # Departments
    departments = [
        ('Computer Science', 'CS'),
        ('Mathematics', 'MATH'),
        ('Physics', 'PHYS'),
    ]
    for name, code in departments:
        cursor.execute('INSERT INTO departments (name, code) VALUES (?, ?)', (name, code))
    
    # Get department IDs
    cursor.execute('SELECT id, code FROM departments')
    dept_map = {code: id for id, code in cursor.fetchall()}
    
    # Instructors
    instructors = [
        ('Dr. Alice Smith', 'alice.smith@university.edu', 'CS-101', dept_map['CS']),
        ('Dr. Bob Johnson', 'bob.johnson@university.edu', 'CS-102', dept_map['CS']),
        ('Dr. Carol Williams', 'carol.williams@university.edu', 'MATH-101', dept_map['MATH']),
        ('Dr. David Brown', 'david.brown@university.edu', 'PHYS-101', dept_map['PHYS']),
        ('Dr. Eve Davis', 'eve.davis@university.edu', 'CS-103', dept_map['CS']),
    ]
    for name, email, office, dept_id in instructors:
        cursor.execute(
            'INSERT INTO instructors (name, email, office, department_id) VALUES (?, ?, ?, ?)',
            (name, email, office, dept_id)
        )
    
    # Get instructor IDs
    cursor.execute('SELECT id, name FROM instructors')
    instructor_map = {name: id for id, name in cursor.fetchall()}
    
    # Courses
    courses = [
        ('CS101', 'Introduction to Programming', 'A foundational course on programming principles using Python.', 3, instructor_map['Dr. Alice Smith'], dept_map['CS']),
        ('CS102', 'Data Structures and Algorithms', 'Covers fundamental data structures and algorithm design techniques.', 4, instructor_map['Dr. Bob Johnson'], dept_map['CS']),
        ('CS201', 'Database Systems', 'Introduction to database design, SQL, and transaction management.', 3, instructor_map['Dr. Eve Davis'], dept_map['CS']),
        ('CS301', 'Operating Systems', 'Concepts of operating systems including processes, memory, and file systems.', 4, instructor_map['Dr. Bob Johnson'], dept_map['CS']),
        ('MATH101', 'Calculus I', 'Limits, derivatives, and integrals of functions of one variable.', 4, instructor_map['Dr. Carol Williams'], dept_map['MATH']),
        ('MATH201', 'Linear Algebra', 'Vector spaces, linear transformations, eigenvalues, and eigenvectors.', 3, instructor_map['Dr. Carol Williams'], dept_map['MATH']),
        ('PHYS101', 'General Physics I', 'Mechanics, thermodynamics, and waves.', 4, instructor_map['Dr. David Brown'], dept_map['PHYS']),
        ('PHYS201', 'General Physics II', 'Electricity, magnetism, and optics.', 4, instructor_map['Dr. David Brown'], dept_map['PHYS']),
        ('CS250', 'Software Engineering', 'Software development lifecycle, design patterns, and testing.', 3, instructor_map['Dr. Alice Smith'], dept_map['CS']),
        ('CS401', 'Machine Learning', 'Introduction to machine learning algorithms and applications.', 4, instructor_map['Dr. Eve Davis'], dept_map['CS']),
    ]
    for course_code, title, desc, credits, instructor_id, dept_id in courses:
        cursor.execute(
            'INSERT INTO courses (course_code, title, description, credits, instructor_id, department_id) VALUES (?, ?, ?, ?, ?, ?)',
            (course_code, title, desc, credits, instructor_id, dept_id)
        )
    
    # Get course IDs
    cursor.execute('SELECT id, course_code FROM courses')
    course_map = {code: id for id, code in cursor.fetchall()}
    
    # Prerequisites
    prerequisites = [
        (course_map['CS102'], course_map['CS101']),  # CS102 requires CS101
        (course_map['CS201'], course_map['CS101']),  # CS201 requires CS101
        (course_map['CS301'], course_map['CS102']),  # CS301 requires CS102
        (course_map['CS250'], course_map['CS102']),  # CS250 requires CS102
        (course_map['CS401'], course_map['CS201']),  # CS401 requires CS201
        (course_map['CS401'], course_map['MATH201']), # CS401 requires MATH201
        (course_map['MATH201'], course_map['MATH101']), # MATH201 requires MATH101
        (course_map['PHYS201'], course_map['PHYS101']), # PHYS201 requires PHYS101
    ]
    for course_id, prereq_id in prerequisites:
        cursor.execute(
            'INSERT INTO prerequisites (course_id, prerequisite_id) VALUES (?, ?)',
            (course_id, prereq_id)
        )
    
    conn.commit()
    print("Database seeded successfully!")

def main():
    conn = sqlite3.connect(DB_PATH)
    create_tables(conn)
    seed_data(conn)
    conn.close()

if __name__ == '__main__':
    main()