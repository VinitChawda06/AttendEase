import streamlit as st
import cv2
import numpy as np
import face_recognition
from database import init_db, add_student, get_all_students, update_student, delete_student, record_attendance, get_attendance_report
from face_recognition_utils import process_image
import logging
import pandas as pd
import io
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    st.set_page_config(page_title="Facial Recognition Attendance System")
    st.title("Facial Recognition Attendance System")

    try:
        # Initialize database
        init_db()

        # Sidebar navigation
        page = st.sidebar.selectbox("Choose a page", ["Upload Attendance", "Add New Student", "Manage Students", "Attendance Reports"])

        if page == "Upload Attendance":
            upload_attendance_page()
        elif page == "Add New Student":
            add_new_student_page()
        elif page == "Manage Students":
            manage_students_page()
        elif page == "Attendance Reports":
            attendance_reports_page()

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        st.error("An unexpected error occurred. Please try again later.")

def upload_attendance_page():
    st.header("Upload Class Image")
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = cv2.imdecode(np.frombuffer(uploaded_file.read(), np.uint8), 1)
        st.image(image, caption="Uploaded Image", use_column_width=True)
        
        if st.button("Process Attendance"):
            attendance, face_count = process_image(image)
            
            st.write(f"Detected {face_count} faces.")
            st.write("Attendance:")
            students = get_all_students()
            for student in students:
                status = attendance.get(student[0], "Absent")
                st.write(f"{student[1]}: {status}")
            
            record_attendance(attendance)
            st.success("Attendance recorded successfully!")

def add_new_student_page():
    st.header("Add New Student")
    name = st.text_input("Student Name")
    uploaded_file = st.file_uploader("Choose a clear face photo...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = cv2.imdecode(np.frombuffer(uploaded_file.read(), np.uint8), 1)
        st.image(image, caption="Uploaded Image", use_column_width=True)
        
        if st.button("Add Student"):
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            face_encodings = face_recognition.face_encodings(rgb_image)
            
            if len(face_encodings) > 0:
                face_encoding = face_encodings[0]
                add_student(name, face_encoding)
                st.success(f"Successfully added {name} to the database!")
            else:
                st.error("No face detected in the image. Please try again with a clear face photo.")

def manage_students_page():
    st.header("Manage Students")
    students = get_all_students()
    
    for student in students:
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.write(f"ID: {student[0]}, Name: {student[1]}")
        with col2:
            if st.button(f"Edit {student[1]}", key=f"edit_{student[0]}"):
                st.session_state.editing = student[0]
        with col3:
            if st.button(f"Delete {student[1]}", key=f"delete_{student[0]}"):
                st.session_state.deleting = student[0]
        with col4:
            if st.session_state.get('editing') == student[0] or st.session_state.get('deleting') == student[0]:
                if st.button("Cancel", key=f"cancel_{student[0]}"):
                    if hasattr(st.session_state, 'editing'):
                        del st.session_state.editing
                    if hasattr(st.session_state, 'deleting'):
                        del st.session_state.deleting
                    st.experimental_rerun()
    
    if hasattr(st.session_state, 'editing'):
        edit_student(students)
    
    if hasattr(st.session_state, 'deleting'):
        confirm_delete_student(students)

def edit_student(students):
    st.subheader("Edit Student")
    student_to_edit = next((s for s in students if s[0] == st.session_state.editing), None)
    if student_to_edit:
        new_name = st.text_input("New Name", value=student_to_edit[1])
        new_photo = st.file_uploader("New Photo (optional)", type=["jpg", "jpeg", "png"])
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update Student"):
                if new_photo:
                    image = cv2.imdecode(np.frombuffer(new_photo.read(), np.uint8), 1)
                    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    face_encodings = face_recognition.face_encodings(rgb_image)
                    if len(face_encodings) > 0:
                        update_student(student_to_edit[0], new_name, face_encodings[0])
                    else:
                        st.error("No face detected in the new image. Student not updated.")
                else:
                    update_student(student_to_edit[0], new_name)
                st.success(f"Updated student {new_name}")
                del st.session_state.editing
                st.experimental_rerun()
        with col2:
            if st.button("Cancel Edit"):
                del st.session_state.editing
                st.experimental_rerun()

def confirm_delete_student(students):
    st.subheader("Confirm Delete Student")
    student_to_delete = next((s for s in students if s[0] == st.session_state.deleting), None)
    if student_to_delete:
        st.write(f"Are you sure you want to delete {student_to_delete[1]}?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Confirm Delete"):
                delete_student(student_to_delete[0])
                st.success(f"Deleted student {student_to_delete[1]}")
                del st.session_state.deleting
                st.experimental_rerun()
        with col2:
            if st.button("Cancel Delete"):
                del st.session_state.deleting
                st.experimental_rerun()

def attendance_reports_page():
    st.header("Attendance Reports")
    
    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=7))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    
    if start_date > end_date:
        st.error("Error: End date must be after start date.")
        return
    
    # Get report data
    report_data = get_attendance_report(start_date, end_date)
    
    if report_data:
        # Convert to DataFrame for easy manipulation
        df = pd.DataFrame(report_data, columns=["Student ID", "Name", "Date", "Status"])
        
        # Display summary statistics
        st.subheader("Summary Statistics")
        total_records = len(df)
        present_count = len(df[df['Status'] == 'Present'])
        absent_count = len(df[df['Status'] == 'Absent'])
        
        st.write(f"Total Records: {total_records}")
        st.write(f"Present: {present_count}")
        st.write(f"Absent: {absent_count}")
        
        # Display detailed report
        st.subheader("Detailed Report")
        st.dataframe(df)
        
        # Export options
        st.subheader("Export Report")
        export_format = st.selectbox("Choose export format:", ["CSV", "Excel"])
        if st.button("Export"):
            if export_format == "CSV":
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"attendance_report_{start_date}_{end_date}.csv",
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
                    file_name=f"attendance_report_{start_date}_{end_date}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
    else:
        st.info("No attendance data available for the selected date range.")

if __name__ == "__main__":
    main()