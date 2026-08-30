import pickle
import cv2
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DETECTION_MODEL = (
    BASE_DIR
    / "models"
    / "face_detection_yunet_2026may.onnx"
)

RECOGNITION_MODEL = (
    BASE_DIR
    / "models"
    / "face_recognition_sface_2021dec.onnx"
)


# ============================================================
# SETTINGS
# ============================================================

DETECTION_CONFIDENCE = 0.80

MIN_FACE_WIDTH = 80
MIN_FACE_HEIGHT = 80

MATCH_THRESHOLD = 0.55


# ============================================================
# FACE SYSTEM
# ============================================================

class FaceSystem:

    def __init__(self):

        if not DETECTION_MODEL.exists():

            raise FileNotFoundError(
                f"YuNet model not found:\n"
                f"{DETECTION_MODEL}"
            )

        if not RECOGNITION_MODEL.exists():

            raise FileNotFoundError(
                f"SFace model not found:\n"
                f"{RECOGNITION_MODEL}"
            )

        # ----------------------------------------------------
        # YuNet
        # ----------------------------------------------------

        self.detector = cv2.FaceDetectorYN.create(

            str(DETECTION_MODEL),

            "",

            (320, 320),

            DETECTION_CONFIDENCE,

            0.3,

            5000
        )

        # ----------------------------------------------------
        # SFace
        # ----------------------------------------------------

        self.recognizer = cv2.FaceRecognizerSF.create(

            str(RECOGNITION_MODEL),

            ""
        )

    # ========================================================
    # DETECTION
    # ========================================================

    def detect(self, frame):

        height, width = frame.shape[:2]

        self.detector.setInputSize(
            (width, height)
        )

        _, faces = self.detector.detect(
            frame
        )

        if faces is None:

            return []

        valid_faces = []

        for face in faces:

            x, y, w, h = face[:4]

            confidence = face[-1]

            if w < MIN_FACE_WIDTH:
                continue

            if h < MIN_FACE_HEIGHT:
                continue

            if confidence < DETECTION_CONFIDENCE:
                continue

            valid_faces.append(face)

        return valid_faces

    # ========================================================
    # FEATURE
    # ========================================================

    def get_feature(
        self,
        frame,
        face
    ):

        aligned = self.recognizer.alignCrop(
            frame,
            face
        )

        feature = self.recognizer.feature(
            aligned
        )

        return feature

    # ========================================================
    # COMPARE
    # ========================================================

    def compare(
        self,
        feature1,
        feature2
    ):

        return self.recognizer.match(
            feature1,
            feature2,
            cv2.FaceRecognizerSF_FR_COSINE
        )


# ============================================================
# LOAD DATABASE FACES
# ============================================================

def load_registered_faces():

    from database.database import (
        get_face_embeddings
    )

    records = get_face_embeddings()

    registered = []

    for record in records:

        (
            employee_id,
            employee_code,
            name,
            department,
            pose,
            embedding_data
        ) = record

        try:

            feature = pickle.loads(
                embedding_data
            )

        except Exception:

            continue

        registered.append({

            "employee_id": employee_id,

            "employee_code": employee_code,

            "name": name,

            "department": department,

            "pose": pose,

            "feature": feature
        })

    return registered


# ============================================================
# RECOGNIZE
# ============================================================

def recognize_face(
    face_system,
    live_feature,
    registered_faces
):

    if not registered_faces:

        return None, -1

    best_match = None
    best_score = -1

    for person in registered_faces:

        score = face_system.compare(
            live_feature,
            person["feature"]
        )

        if score > best_score:

            best_score = score
            best_match = person

    if best_score < MATCH_THRESHOLD:

        return None, best_score

    return best_match, best_score


# ============================================================
# DRAW
# ============================================================

def draw_face(
    frame,
    face,
    color=(0, 255, 0)
):

    x, y, w, h = face[:4]

    x = int(x)
    y = int(y)
    w = int(w)
    h = int(h)

    cv2.rectangle(
        frame,
        (x, y),
        (x + w, y + h),
        color,
        2
    )

    confidence = face[-1]

    cv2.putText(
        frame,
        f"Face {confidence:.2f}",
        (x, max(y - 10, 20)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        color,
        2
    )

    return frame