from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Criminal
import cv2
import os
from .storage import face_data_storage
from .face_utils import get_face_encoding

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
    
    face_data_storage.update_data(known_encodings, known_names, is_criminal_list)

@receiver([post_save, post_delete], sender=Criminal)
def update_face_data(sender, instance=None, **kwargs):
    """Signal handler to reload face data when Criminal model is modified"""
    load_known_faces()

# Initial load
load_known_faces()