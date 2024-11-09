import threading
import numpy as np

class FaceDataStorage:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(FaceDataStorage, cls).__new__(cls)
                    cls._instance.known_face_encodings = []
                    cls._instance.known_names = []
                    cls._instance.is_criminal_list = []
        return cls._instance

    def update_data(self, encodings, names, is_criminal):
        with self._lock:
            self.known_face_encodings = encodings
            self.known_names = names
            self.is_criminal_list = is_criminal

face_data_storage = FaceDataStorage()