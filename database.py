import sqlite3
import pickle
from datetime import datetime
from config import DATABASE_NAME

def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  face_encoding BLOB NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS attendance
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  student_id INTEGER,
                  date TEXT,
                  status TEXT,
                  FOREIGN KEY (student_id) REFERENCES students(id))''')
    conn.commit()
    conn.close()

def add_student(name, face_encoding):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO students (name, face_encoding) VALUES (?, ?)",
              (name, pickle.dumps(face_encoding)))
    conn.commit()
    conn.close()

def get_all_students():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT id, name, face_encoding FROM students")
    students = [(id, name, pickle.loads(face_encoding)) for id, name, face_encoding in c.fetchall()]
    conn.close()
    return students

def update_student(id, name, face_encoding=None):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    if face_encoding is not None:
        c.execute("UPDATE students SET name = ?, face_encoding = ? WHERE id = ?",
                  (name, pickle.dumps(face_encoding), id))
    else:
        c.execute("UPDATE students SET name = ? WHERE id = ?", (name, id))
    conn.commit()
    conn.close()

def delete_student(id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM students WHERE id = ?", (id,))
    conn.commit()
    conn.close()

def record_attendance(attendance_data):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d")
    for student_id, status in attendance_data.items():
        c.execute("INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?)",
                  (student_id, date, status))
    conn.commit()
    conn.close()

def get_attendance_report(start_date, end_date):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT a.student_id, s.name, a.date, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE a.date BETWEEN ? AND ?
        ORDER BY a.date, s.name
    """, (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
    report_data = c.fetchall()
    conn.close()
    return report_data