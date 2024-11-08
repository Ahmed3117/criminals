import base64

from django.shortcuts import render
import cv2
import dlib
import numpy as np
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Criminal
import json
from django.contrib.auth.decorators import user_passes_test



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
    criminals = Criminal.objects.all()
    known_encodings = []
    known_names = []
    is_criminal_list = []

    for criminal in criminals:
        img_path = criminal.image.path
        if os.path.exists(img_path):
            img = cv2.imread(img_path)
            encoding = get_face_encoding(img)
            if encoding is not None:
                known_encodings.append(encoding)
                known_names.append(criminal.name)
                is_criminal_list.append(criminal.is_criminal)
    return known_encodings, known_names, is_criminal_list

def get_face_encoding(image):
    faces = face_detector(image)
    if len(faces) == 0:
        return None
    shape = shape_predictor(image, faces[0])
    face_descriptor = face_recognizer.compute_face_descriptor(image, shape)
    return np.array(face_descriptor)

known_face_encodings, known_names, is_criminal_list = load_known_faces()

def compare_faces(known_encodings, face_encoding, tolerance=0.6):
    distances = np.linalg.norm(known_encodings - face_encoding, axis=1)
    return distances <= tolerance

@csrf_exempt
def process_image(request):
    """Process the captured image to detect faces and return the results."""
    if request.method == 'POST':
        try:
            # Decode the incoming JSON data
            data = json.loads(request.body)
            image_data = data.get('image')

            # Check if image data is present
            if not image_data:
                print("No image data provided")
                return JsonResponse({'error': 'No image data provided'}, status=400)

            # Decode the base64 image
            header, encoded = image_data.split(',', 1)
            img_bytes = base64.b64decode(encoded)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            # Ensure the frame is valid
            if frame is None:
                print("Failed to decode the image")
                return JsonResponse({'error': 'Failed to decode the image'}, status=400)

            # Detect faces in the frame
            faces = face_detector(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            faces_data = []

            for face in faces:
                shape = shape_predictor(frame, face)
                face_encoding = np.array(face_recognizer.compute_face_descriptor(frame, shape))
                matches = compare_faces(known_face_encodings, face_encoding)

                if matches.any():
                    match_index = np.argmax(matches)
                    is_criminal = is_criminal_list[match_index]
                    label = 'criminal' if is_criminal else 'non-criminal'
                else:
                    label = 'unknown'

                # Prepare the response data with face coordinates
                top, right, bottom, left = face.top(), face.right(), face.bottom(), face.left()
                faces_data.append({
                    'top': top,
                    'right': right,
                    'bottom': bottom,
                    'left': left,
                    'label': label
                })

            # Return the detection results
            return JsonResponse({'faces': faces_data})

        except Exception as e:
            print(f"Error processing image: {e}")
            return JsonResponse({'error': 'Failed to process image', 'details': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)




def is_superuser(user):
    """Check if the user is a superuser."""
    return user.is_superuser

@user_passes_test(is_superuser, login_url='/admin/login/')
def home(request):
    """Render the home page for superusers only."""
    return render(request, 'about/home.html')


