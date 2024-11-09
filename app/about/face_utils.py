import cv2
import dlib
import numpy as np
import os
from django.conf import settings

# Load Dlib models
face_detector = dlib.get_frontal_face_detector()
face_recognizer = dlib.face_recognition_model_v1(
    os.path.join(settings.MEDIA_ROOT, 'models/dlib_face_recognition_resnet_model_v1.dat')
)
shape_predictor = dlib.shape_predictor(
    os.path.join(settings.MEDIA_ROOT, 'models/shape_predictor_68_face_landmarks.dat')
)

def get_face_encoding(image):
    faces = face_detector(image)
    if len(faces) == 0:
        return None
    shape = shape_predictor(image, faces[0])
    face_descriptor = face_recognizer.compute_face_descriptor(image, shape)
    return np.array(face_descriptor)

def compare_faces(known_encodings, face_encoding, tolerance=0.6):
    if len(known_encodings) == 0:
        return np.array([])
    distances = np.linalg.norm(np.array(known_encodings) - face_encoding, axis=1)
    return distances <= tolerance