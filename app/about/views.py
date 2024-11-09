import base64
from django.shortcuts import render
import cv2
import numpy as np
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
import json
from .storage import face_data_storage
from .face_utils import face_detector, shape_predictor, face_recognizer, compare_faces

@csrf_exempt
def process_image(request):
    """Process the captured image to detect faces and return the results."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_data = data.get('image')

            if not image_data:
                print("No image data provided")
                return JsonResponse({'error': 'No image data provided'}, status=400)

            # Decode the base64 image
            header, encoded = image_data.split(',', 1)
            img_bytes = base64.b64decode(encoded)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if frame is None:
                print("Failed to decode the image")
                return JsonResponse({'error': 'Failed to decode the image'}, status=400)

            # Convert frame to RGB for dlib compatibility
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect faces in the frame
            faces = face_detector(rgb_frame)
            faces_data = []

            for face in faces:
                shape = shape_predictor(rgb_frame, face)
                face_encoding = np.array(face_recognizer.compute_face_descriptor(rgb_frame, shape))

                # Compare with known encodings
                distances = np.linalg.norm(face_data_storage.known_face_encodings - face_encoding, axis=1)
                tolerance = 0.6
                matches = distances <= tolerance

                if matches.any():
                    match_index = np.argmin(distances)  # Get the best match
                    is_criminal = face_data_storage.is_criminal_list[match_index]
                    label = 'criminal' if is_criminal else 'non-criminal'
                else:
                    label = 'unknown'

                # Prepare the response with face coordinates and label
                top, right, bottom, left = face.top(), face.right(), face.bottom(), face.left()
                faces_data.append({
                    'top': top,
                    'right': right,
                    'bottom': bottom,
                    'left': left,
                    'label': label
                })

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
