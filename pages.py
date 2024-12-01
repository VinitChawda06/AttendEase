import streamlit as st
import cv2
import numpy as np
import pandas as pd
import io
from datetime import datetime, timedelta
from auth import login, create_user, get_all_users
from database import (
    get_all_students, add_student, update_student, delete_student,
    get_all_classes, add_class, update_class, delete_class,
    get_attendance_report, get_students_in_class, assign_student_to_class,
    record_attendance
)
import face_recognition
from face_recognition_utils import process_image

def login_page():
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = login(username, password)
        if user:
            st.session_state['user'] = user
            st.success("Logged in successfully!")
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")

def upload_attendance_page():
    st.header("Upload Class Image")
    classes = get_all_classes()
    selected_class = st.selectbox("Select Class", [c[1] for c in classes])
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = cv2.imdecode(np.frombuffer(uploaded_file.read(), np.uint8), 1)
        st.image(image, caption="Uploaded Image", use_column_width=True)
        
        if st.button("Process Attendance"):
            attendance, face_count = process_image(image)
            
            st.write(f"Detected {face_count} faces.")
            st.write("Attendance:")
            students = get_students_in_class(selected_class)
            for student in students:
                status = attendance.get(student[0], "Absent")
                st.write(f"{student[1]}: {status}")
            
            record_attendance(attendance, selected_class)
            st.success("Attendance recorded successfully!")

def manage_students_page():
    st.header("Manage Students")
    
    # Add new student
    st.subheader("Add New Student")
    name = st.text_input("Student Name")
    classes = get_all_classes()
    selected_class = st.selectbox("Assign to Class", [c[1] for c in classes])
    uploaded_file = st.file_uploader("Choose a clear face photo...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None and st.button("Add Student"):
        image = cv2.imdecode(np.frombuffer(uploaded_file.read(), np.uint8), 1)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        face_encodings = face_recognition.face_encodings(rgb_image)
        
        if len(face_encodings) > 0:
            face_encoding = face_encodings[0]
            student_id = add_student(name, face_encoding.tobytes())
            assign_student_to_class(student_id, selected_class)
            st.success(f"Successfully added {name} to the database and assigned to {selected_class}!")
        else:
            st.error("No face detected in the image. Please try again with a clear face photo.")
    
    # List and manage existing students
    st.subheader("Existing Students")
    students = get_all_students()
    for student in students:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"ID: {student[0]}, Name: {student[1]}")
        with col2:
            if st.button(f"Edit {student[1]}", key=f"edit_{student[0]}"):
                st.session_state.editing = student[0]
        with col3:
            if st.button(f"Delete {student[1]}", key=f"delete_{student[0]}"):
                st.session_state.deleting = student[0]
    
    if hasattr(st.session_state, 'editing'):
        edit_student(students)
    
    if hasattr(st.session_state, 'deleting'):
        confirm_delete_student(students)

def edit_student(students):
    st.subheader("Edit Student")
    student_to_edit = next((s for s in students if s[0] == st.session_state.editing), None)
    if student_to_edit:
        new_name = st.text_input("New Name", value=student_to_edit[1])
        classes = get_all_classes()
        new_class = st.selectbox("Assign to Class", [c[1] for c in classes])
        new_photo = st.file_uploader("New Photo (optional)", type=["jpg", "jpeg", "png"])
        if st.button("Update Student"):
            if new_photo:
                image = cv2.imdecode(np.frombuffer(new_photo.read(), np.uint8), 1)
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                face_encodings = face_recognition.face_encodings(rgb_image)
                if len(face_encodings) > 0:
                    update_student(student_to_edit[0], new_name, face_encodings[0].tobytes())
                else:
                    st.error("No face detected in the new image. Student not updated.")
            else:
                update_student(student_to_edit[0], new_name)
            assign_student_to_class(student_to_edit[0], new_class)
            st.success(f"Updated student {new_name} and assigned to {new_class}")
            del st.session_state.editing
            st.experimental_rerun()

def confirm_delete_student(students):
    st.subheader("Confirm Delete Student")
    student_to_delete = next((s for s in students if s[0] == st.session_state.deleting), None)
    if student_to_delete:
        st.write(f"Are you sure you want to delete {student_to_delete[1]}?")
        if st.button("Confirm Delete"):
            delete_student(student_to_delete[0])
            st.success(f"Deleted student {student_to_delete[1]}")
            del st.session_state.deleting
            st.experimental_rerun()

def attendance_reports_page():
    st.header("Attendance Reports")
    
    classes = get_all_classes()
    selected_class = st.selectbox("Select Class", [c[1] for c in classes])
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=7))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    
    if start_date > end_date:
        st.error("Error: End date must be after start date.")
        return
    
    report_data = get_attendance_report(selected_class, start_date, end_date)
    
    if report_data:
        df = pd.DataFrame(report_data, columns=["Student ID", "Name", "Date", "Status"])
        
        st.subheader("Summary Statistics")
        total_records = len(df)
        present_count = len(df[df['Status'] == 'Present'])
        absent_count = len(df[df['Status'] == 'Absent'])
        
        st.write(f"Total Records: {total_records}")
        st.write(f"Present: {present_count}")
        st.write(f"Absent: {absent_count}")
        
        st.subheader("Detailed Report")
        st.dataframe(df)
        
        st.subheader("Export Report")
        export_format = st.selectbox("Choose export format:", ["CSV", "Excel"])
        if st.button("Export"):
            if export_format == "CSV":
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"attendance_report_{selected_class}_{start_date}_{end_date}.csv",
                    mime="text/csv",
                )
            elif export_format == "Excel":
                excel_file = io.BytesIO()
                with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
                    df.to_excel(writer, sheet_name="Attendance Report", index=False)
                excel_file.seek(0)
                st.download_button(
                    label="Download Excel",
                    data=excel_file,
                    file_name=f"attendance_report_{selected_class}_{start_date}_{end_date}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
    else:
        st.info("No attendance data available for the selected class and date range.")

def manage_classes_page():
    st.header("Manage Classes")
    
    # Add new class
    st.subheader("Add New Class")
    class_name = st.text_input("Class Name")
    if st.button("Add Class"):
        add_class(class_name)
        st.success(f"Successfully added class: {class_name}")
    
    # List and manage existing classes
    st.subheader("Existing Classes")
    classes = get_all_classes()
    for class_info in classes:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"ID: {class_info[0]}, Name: {class_info[1]}")
        with col2:
            if st.button(f"Edit {class_info[1]}", key=f"edit_class_{class_info[0]}"):
                st.session_state.editing_class = class_info[0]
        with col3:
            if st.button(f"Delete {class_info[1]}", key=f"delete_class_{class_info[0]}"):
                st.session_state.deleting_class = class_info[0]
    
    if hasattr(st.session_state, 'editing_class'):
        edit_class(classes)
    
    if hasattr(st.session_state, 'deleting_class'):
        confirm_delete_class(classes)

def edit_class(classes):
    st.subheader("Edit Class")
    class_to_edit = next((c for c in classes if c[0] == st.session_state.editing_class), None)
    if class_to_edit:
        new_name = st.text_input("New Class Name", value=class_to_edit[1])
        if st.button("Update Class"):
            update_class(class_to_edit[0], new_name)
            st.success(f"Updated class name to {new_name}")
            del st.session_state.editing_class
            st.experimental_rerun()

def confirm_delete_class(classes):
    st.subheader("Confirm Delete Class")
    class_to_delete = next((c for c in classes if c[0] == st.session_state.deleting_class), None)
    if class_to_delete:
        st.write(f"Are you sure you want to delete the class {class_to_delete[1]}?")
        if st.button("Confirm Delete"):
            delete_class(class_to_delete[0])
            st.success(f"Deleted class {class_to_delete[1]}")
            del st.session_state.deleting_class
            st.experimental_rerun()

def user_management_page():
    st.header("User Management")
    
    # Add new user
    st.subheader("Add New User")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["admin", "teacher", "student"])
    if st.button("Add User"):
        if create_user(username, password, role):
            st.success(f"Successfully added user: {username} with role: {role}")
        else:
            st.error("Failed to add user. Username may already exist.")

    # List existing users
    st.subheader("Existing Users")
    users = get_all_users()
    for user in users:
        st.write(f"Username: {user['username']}, Role: {user['role']}")