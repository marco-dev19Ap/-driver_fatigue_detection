import mediapipe as mp
import numpy as np #para tipar las entradas a nuestros metodos y operaciones matematicas
import cv2 #para visión de computadora
from typing import Tuple, Any, List, Dict #tipar todos nuestros métodos


class FaceMeshInference:
    def __init__(self, min_detection_confidence=0.6, min_tracking_confidence=0.6):
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False, #si estamos procesando imagenes o videos, como es en tiempo real, queda false
            max_num_faces=1, #cantidad de rostros
            refine_landmarks=True, #refinar puntos faciales, para que agregue los puntos adiciones al rostro
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
#Recibir una imagen y devolver la malla facial en caso de que haya una cara
    def process(self, image: np.ndarray) -> Tuple[bool, Any]:
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        face_mesh = self.face_mesh.process(rgb_image)
        return bool(face_mesh.multi_face_landmarks), face_mesh


class FaceMeshExtractor:
    def __init__(self):
        self.points: dict = {
            'eyes': {'distances': []},
            'mouth': {'distances': []},
            'pitch': {'distances': []}
        }

    def extract_points(self, face_image: np.ndarray, face_mesh_info: Any) -> List[List[int]]:
        h, w, _ = face_image.shape
        mesh_points = [
            [i, int(pt.x * w), int(pt.y * h)]
            for face in face_mesh_info.multi_face_landmarks
            for i, pt in enumerate(face.landmark)
        ]
        return mesh_points

    def extract_feature_points(self, face_points: List[List[int]], feature_indices: dict):
        for feature, indices in feature_indices.items():
            for sub_feature, sub_indices in indices.items():
                self.points[feature][sub_feature] = [face_points[i][1:] for i in sub_indices]

    def get_eyes_points(self, face_points: List[List[int]]) -> Dict[str, List[List[int]]]:
        feature_indices = {
            'eyes': {
                'distances': [159, 145, 385, 374, 145, 230, 374, 450],
            }
        }
        self.extract_feature_points(face_points, feature_indices)
        return self.points['eyes']

    def get_mouth_points(self, face_points: List[List[int]]) -> Dict[str, List[List[int]]]:
        feature_indices = {
            'mouth': {
                'distances': [13, 14, 17, 199]
            }
        }
        self.extract_feature_points(face_points, feature_indices)
        return self.points['mouth']

    def get_pitch_points(self, face_points: List[List[int]]) -> Dict[str, List[List[int]]]:
        feature_indices = {
            'pitch': {
                'distances': [1, 0, 9, 51]
            }
        }
        self.extract_feature_points(face_points, feature_indices)
        return self.points['pitch']



class FaceMeshDrawer: #dibujar los puntos de la malla facial
    def __init__(self, color: Tuple[int, int, int] = (255, 255, 0)):
        self.mp_draw = mp.solutions.drawing_utils
        self.config_draw = self.mp_draw.DrawingSpec(color=color, thickness=1, circle_radius=1)

    def draw(self, face_image: np.ndarray, face_mesh_info: Any):
        for face_mesh in face_mesh_info.multi_face_landmarks:
            self.mp_draw.draw_landmarks(face_image, face_mesh, mp.solutions.face_mesh.FACEMESH_TESSELATION,
                                        self.config_draw, self.config_draw)

class FaceMeshProcessor:
    def __init__(self):
        self.inference = FaceMeshInference() #poder usar la camara y reconocer los rostros
        self.extractor = FaceMeshExtractor() #extrae los puntos faciales
        self.drawer = FaceMeshDrawer() #dibujar la malla facial

    def process(self, face_image: np.ndarray, draw: bool = True) -> Tuple[dict, bool, np.ndarray]:
        original_image = face_image.copy()
        success, face_mesh_info = self.inference.process(face_image)
        if not success:
            return {}, success, original_image

        face_points = self.extractor.extract_points(face_image, face_mesh_info)
        points = {
            'eyes': self.extractor.get_eyes_points(face_points),
            'mouth': self.extractor.get_mouth_points(face_points),
            'pitch': self.extractor.get_pitch_points(face_points),
        }

        if draw:
            self.drawer.draw(face_image, face_mesh_info)
            return points, success, face_image



        return points, success, original_image