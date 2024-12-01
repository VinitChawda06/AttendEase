import cv2
import face_recognition
from database import get_all_students
import logging

logger = logging.getLogger(__name__)

def process_image(image):
    try:
        # Load known faces from the database
        students = get_all_students()
        known_face_ids = [student[0] for student in students]
        known_face_names = [student[1] for student in students]
        known_face_encodings = [student[2] for student in students]

        # Resize image
        image = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        
        # Convert to RGB (face_recognition uses RGB)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Detect faces
        face_locations = face_recognition.face_locations(rgb_image)
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
        
        # Recognize faces
        attendance = {id: "Absent" for id in known_face_ids}  # Initialize all as absent
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            
            if True in matches:
                first_match_index = matches.index(True)
                student_id = known_face_ids[first_match_index]
                attendance[student_id] = "Present"
        
        return attendance, len(face_locations)
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return {}, 0