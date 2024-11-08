from django.shortcuts import render
from django.http import StreamingHttpResponse
from django.conf import settings
import cv2
import dlib
import numpy as np
import os
from .models import Criminal

# Load Dlib models
face_detector = dlib.get_frontal_face_detector()
face_recognizer = dlib.face_recognition_model_v1(
    os.path.join(settings.MEDIA_ROOT, 'models/dlib_face_recognition_resnet_model_v1.dat')
)
shape_predictor = dlib.shape_predictor(
    os.path.join(settings.MEDIA_ROOT, 'models/shape_predictor_68_face_landmarks.dat')
)


# Load known faces from the database
def load_known_faces():
    """Load known faces from the database."""
    criminals = Criminal.objects.all()
    known_encodings = []
    known_names = []
    is_criminal_list = []

    for criminal in criminals:
        img_path = criminal.image.path
        print(f"Loading image: {img_path}")
        
        if os.path.exists(img_path):
            img = cv2.imread(img_path)
            encoding = get_face_encoding(img)
            
            # Check if the encoding was successful
            if encoding is not None:
                known_encodings.append(encoding)
                known_names.append(criminal.name)
                is_criminal_list.append(criminal.is_criminal)
                print(f"Loaded encoding for: {criminal.name}")
            else:
                print(f"Failed to extract encoding for image: {img_path}")
        else:
            print(f"Image file not found: {img_path}")
    
    print(f"Total known faces loaded: {len(known_encodings)}")
    return known_encodings, known_names, is_criminal_list


def get_face_encoding(image):
    """Get face encoding for a given image."""
    faces = face_detector(image)
    
    if len(faces) == 0:
        print("No faces detected in the image.")
        return None
    
    shape = shape_predictor(image, faces[0])
    face_descriptor = face_recognizer.compute_face_descriptor(image, shape)
    return np.array(face_descriptor)



# Load known faces data
known_face_encodings, known_names, is_criminal_list = load_known_faces()

def compare_faces(known_encodings, face_encoding, tolerance=0.6):
    """Compare the given face encoding with known encodings."""
    if len(known_encodings) == 0:
        print("No known face encodings available for comparison.")
        return []
    
    # Calculate distances between known encodings and the current face encoding
    distances = np.linalg.norm(known_encodings - face_encoding, axis=1)
    print(f"Distances: {distances}")
    return distances <= tolerance


def detect_faces(frame):
    """Detect faces in the frame and mark them based on known data."""
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces = face_detector(rgb_frame)

    if not faces:
        print("No faces detected in the frame.")
        return frame

    face_encodings = []
    for face in faces:
        shape = shape_predictor(rgb_frame, face)
        face_encoding = np.array(face_recognizer.compute_face_descriptor(rgb_frame, shape))
        face_encodings.append(face_encoding)

    for face, face_encoding in zip(faces, face_encodings):
        matches = compare_faces(np.array(known_face_encodings), face_encoding)
        
        # Handle the case where matches is an array
        if matches.any():  # Check if there's at least one match
            match_index = np.argmax(matches)  # Get the index of the first True match
            is_criminal = is_criminal_list[match_index]
            color = (0, 0, 255) if is_criminal else (0, 255, 0)
            name = known_names[match_index]
        else:
            # If no match found, mark the face as unknown
            color = (255, 255, 255)
            name = "Unknown"

        # Draw a rectangle around the face
        top, right, bottom, left = face.top(), face.right(), face.bottom(), face.left()
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    return frame


def gen_frames():
    """Generate frames from the webcam for the video feed."""
    cap = cv2.VideoCapture(0)
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Failed to capture frame from camera.")
            break

        # Detect faces in the frame
        frame = detect_faces(frame)

        # Encode the frame as JPEG
        if frame is not None:
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    cap.release()





def video_feed(request):
    """Stream the video feed."""
    return StreamingHttpResponse(gen_frames(), content_type='multipart/x-mixed-replace; boundary=frame')



from django.contrib.auth.decorators import user_passes_test


def is_superuser(user):
    """Check if the user is a superuser."""
    return user.is_superuser

@user_passes_test(is_superuser, login_url='/admin/login/')
def home(request):
    """Render the home page for superusers only."""
    return render(request, 'about/home.html')