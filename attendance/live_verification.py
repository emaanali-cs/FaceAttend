import cv2
import time
import numpy as np
import tkinter as tk

from recognition.face_recognition import (
    FaceSystem,
    load_registered_faces,
    recognize_face
)


# ============================================================
# SETTINGS
# ============================================================

CAMERA_ID = 0

# ------------------------------------------------------------
# Camera resolution
# ------------------------------------------------------------

CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

# ------------------------------------------------------------
# Display resolution
# ------------------------------------------------------------
# Keeps the camera in a normal 16:9 ratio and leaves enough
# space around the window so the complete interface is visible.

DISPLAY_WIDTH = 1200
DISPLAY_HEIGHT = 675

# ------------------------------------------------------------
# Recognition
# ------------------------------------------------------------

MATCH_THRESHOLD = 0.55

# ------------------------------------------------------------
# Pose verification
# ------------------------------------------------------------

POSE_STABLE_TIME = 0.8

YAW_THRESHOLD = 0.18

CHALLENGE_TIME_LIMIT = 15

RECOGNITION_STABILITY_FRAMES = 5

DIRECTION_STABILITY_FRAMES = 5


# ============================================================
# COLORS - BGR
# ============================================================

WHITE = (255, 255, 255)

GREEN = (60, 220, 100)

RED = (60, 60, 230)

YELLOW = (40, 220, 255)

CYAN = (255, 220, 80)

GRAY = (170, 170, 170)

DARK = (15, 23, 42)

PANEL = (25, 38, 60)


# ============================================================
# GET SCREEN SIZE
# ============================================================

def get_screen_size():

    root = tk.Tk()

    root.withdraw()

    width = root.winfo_screenwidth()

    height = root.winfo_screenheight()

    root.destroy()

    return width, height


# ============================================================
# CENTER WINDOW
# ============================================================

def center_window(
    window_name,
    window_width,
    window_height
):

    screen_width, screen_height = (
        get_screen_size()
    )

    x = max(
        0,
        int(
            (screen_width - window_width) / 2
        )
    )

    y = max(
        0,
        int(
            (screen_height - window_height) / 2
        )
    )

    cv2.moveWindow(
        window_name,
        x,
        y
    )


# ============================================================
# HEAD DIRECTION
# ============================================================

def get_head_direction(face):

    try:

        right_eye = np.array([
            float(face[4]),
            float(face[5])
        ])

        left_eye = np.array([
            float(face[6]),
            float(face[7])
        ])

        nose = np.array([
            float(face[8]),
            float(face[9])
        ])

    except (
        IndexError,
        ValueError,
        TypeError
    ):

        return "UNKNOWN"

    eye_center = (
        right_eye + left_eye
    ) / 2

    eye_distance = np.linalg.norm(
        right_eye - left_eye
    )

    if eye_distance < 1:

        return "UNKNOWN"

    yaw = (
        nose[0] - eye_center[0]
    ) / eye_distance

    # --------------------------------------------------------
    # Camera image
    # --------------------------------------------------------

    if yaw > YAW_THRESHOLD:

        return "RIGHT"

    if yaw < -YAW_THRESHOLD:

        return "LEFT"

    return "CENTER"


# ============================================================
# DRAW CAMERA INTERFACE
# ============================================================

def draw_interface(
    frame,
    mode,
    status,
    status_color,
    recognized_name=None,
    score=None,
    required_pose=None,
    detected_pose=None,
    progress=0
):

    height, width = frame.shape[:2]

    # ========================================================
    # HEADER
    # ========================================================

    header_height = 100

    cv2.rectangle(
        frame,
        (0, 0),
        (width, header_height),
        DARK,
        -1
    )

    cv2.putText(
        frame,
        f"EMPLOYEE {mode}",
        (35, 42),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.82,
        WHITE,
        2,
        cv2.LINE_AA
    )

    cv2.putText(
        frame,
        "LIVE BIOMETRIC VERIFICATION",
        (35, 77),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        GRAY,
        1,
        cv2.LINE_AA
    )

    # ========================================================
    # STATUS PANEL
    # ========================================================

    panel_margin = 25

    panel_top = 115

    panel_bottom = 210

    cv2.rectangle(
        frame,
        (
            panel_margin,
            panel_top
        ),
        (
            width - panel_margin,
            panel_bottom
        ),
        PANEL,
        -1
    )

    cv2.putText(
        frame,
        status,
        (
            panel_margin + 25,
            panel_top + 43
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.68,
        status_color,
        2,
        cv2.LINE_AA
    )

    # ========================================================
    # RECOGNITION INFORMATION
    # ========================================================

    if recognized_name:

        score_text = ""

        if score is not None:

            score_text = (
                f"   Match: {score:.2f}"
            )

        cv2.putText(
            frame,
            (
                f"Employee: "
                f"{recognized_name}"
                f"{score_text}"
            ),
            (
                panel_margin + 25,
                panel_top + 78
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.50,
            WHITE,
            1,
            cv2.LINE_AA
        )

    # ========================================================
    # POSE INFORMATION
    # ========================================================

    if required_pose:

        cv2.putText(
            frame,
            f"Required: {required_pose}",
            (
                width - 240,
                panel_top + 35
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            YELLOW,
            1,
            cv2.LINE_AA
        )

    if detected_pose:

        cv2.putText(
            frame,
            f"Detected: {detected_pose}",
            (
                width - 240,
                panel_top + 70
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            CYAN,
            1,
            cv2.LINE_AA
        )

    # ========================================================
    # PROGRESS BAR
    # ========================================================

    # Keep the progress bar safely inside the frame.

    bar_x1 = 40

    bar_x2 = width - 40

    bar_y1 = height - 38

    bar_y2 = height - 20

    # --------------------------------------------------------
    # Background
    # --------------------------------------------------------

    cv2.rectangle(
        frame,
        (
            bar_x1,
            bar_y1
        ),
        (
            bar_x2,
            bar_y2
        ),
        (70, 70, 70),
        -1
    )

    # --------------------------------------------------------
    # Clamp progress
    # --------------------------------------------------------

    progress = max(
        0.0,
        min(
            1.0,
            progress
        )
    )

    progress_width = int(
        (
            bar_x2 - bar_x1
        ) * progress
    )

    # --------------------------------------------------------
    # Progress
    # --------------------------------------------------------

    if progress_width > 0:

        cv2.rectangle(
            frame,
            (
                bar_x1,
                bar_y1
            ),
            (
                bar_x1 + progress_width,
                bar_y2
            ),
            GREEN,
            -1
        )

    # ========================================================
    # CANCEL TEXT
    # ========================================================

    cv2.putText(
        frame,
        "Press Q to cancel",
        (
            40,
            height - 48
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.40,
        GRAY,
        1,
        cv2.LINE_AA
    )


# ============================================================
# STABLE VALUE
# ============================================================

def get_stable_value(
    history,
    value,
    max_length
):

    history.append(value)

    if len(history) > max_length:

        history.pop(0)

    if len(history) < max_length:

        return None

    if all(
        item == history[0]
        for item in history
    ):

        return history[0]

    return None


# ============================================================
# LIVE VERIFICATION
# ============================================================

def run_live_verification(
    mode="CHECK-IN"
):

    face_system = FaceSystem()

    registered_faces = (
        load_registered_faces()
    )

    # ========================================================
    # NO REGISTERED EMPLOYEES
    # ========================================================

    if not registered_faces:

        return {
            "success": False,
            "reason":
                "No registered employees found.",
            "person": None
        }

    # ========================================================
    # OPEN CAMERA
    # ========================================================

    camera = cv2.VideoCapture(
        CAMERA_ID
    )

    camera.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        CAMERA_WIDTH
    )

    camera.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        CAMERA_HEIGHT
    )

    camera.set(
        cv2.CAP_PROP_BUFFERSIZE,
        1
    )

    if not camera.isOpened():

        return {
            "success": False,
            "reason":
                "Could not open camera.",
            "person": None
        }

    # ========================================================
    # CHALLENGE
    # ========================================================

    challenge = [
        "CENTER",
        "LEFT",
        "RIGHT"
    ]

    challenge_index = 0

    stable_start = None

    verification_start = None

    recognized_person = None

    best_score = None

    recognition_history = []

    direction_history = []

    last_direction = "WAITING"

    # ========================================================
    # OPENCV WINDOW
    # ========================================================

    window_name = (
        f"Employee {mode.title()}"
    )

    # --------------------------------------------------------
    # NORMAL WINDOW
    # --------------------------------------------------------
    # Do NOT maximize this window.
    # The frame will be displayed at a fixed 16:9 size.

    cv2.namedWindow(
        window_name,
        cv2.WINDOW_NORMAL
    )

    cv2.resizeWindow(
        window_name,
        DISPLAY_WIDTH,
        DISPLAY_HEIGHT
    )

    center_window(
        window_name,
        DISPLAY_WIDTH,
        DISPLAY_HEIGHT
    )

    # ========================================================
    # MAIN LOOP
    # ========================================================

    while True:

        success, frame = camera.read()

        if not success:

            continue

        # ====================================================
        # MIRROR CAMERA
        # ====================================================

        frame = cv2.flip(
            frame,
            1
        )

        # ====================================================
        # KEEP CAMERA FRAME 16:9
        # ====================================================

        frame = cv2.resize(
            frame,
            (
                DISPLAY_WIDTH,
                DISPLAY_HEIGHT
            ),
            interpolation=cv2.INTER_AREA
        )

        # ====================================================
        # FACE DETECTION
        # ====================================================

        faces = face_system.detect(
            frame
        )

        # ====================================================
        # NO FACE
        # ====================================================

        if len(faces) == 0:

            stable_start = None

            recognition_history.clear()

            direction_history.clear()

            draw_interface(
                frame,
                mode,
                "POSITION YOUR FACE IN THE CAMERA",
                YELLOW,
                progress=(
                    challenge_index /
                    len(challenge)
                )
            )

        # ====================================================
        # MULTIPLE FACES
        # ====================================================

        elif len(faces) > 1:

            stable_start = None

            recognition_history.clear()

            direction_history.clear()

            draw_interface(
                frame,
                mode,
                "ONLY ONE PERSON ALLOWED",
                RED,
                progress=(
                    challenge_index /
                    len(challenge)
                )
            )

        # ====================================================
        # ONE FACE
        # ====================================================

        else:

            face = faces[0]

            x, y, w, h = face[:4]

            x = int(x)

            y = int(y)

            w = int(w)

            h = int(h)

            # ------------------------------------------------
            # FACE BOX
            # ------------------------------------------------

            cv2.rectangle(
                frame,
                (
                    x,
                    y
                ),
                (
                    x + w,
                    y + h
                ),
                GREEN,
                2
            )

            # ------------------------------------------------
            # RECOGNITION FEATURE
            # ------------------------------------------------

            feature = (
                face_system.get_feature(
                    frame,
                    face
                )
            )

            person, score = (
                recognize_face(
                    face_system,
                    feature,
                    registered_faces
                )
            )

            # =================================================
            # RECOGNIZED
            # =================================================

            if (
                person is not None
                and
                score >= MATCH_THRESHOLD
            ):

                # ------------------------------------------------
                # Start timeout after recognition
                # ------------------------------------------------

                if verification_start is None:

                    verification_start = (
                        time.time()
                    )

                # ------------------------------------------------
                # Recognition stability
                # ------------------------------------------------

                stable_person_id = (
                    get_stable_value(
                        recognition_history,
                        person["employee_id"],
                        RECOGNITION_STABILITY_FRAMES
                    )
                )

                if stable_person_id is not None:

                    recognized_person = person

                    best_score = score

                # ------------------------------------------------
                # Head direction
                # ------------------------------------------------

                direction = (
                    get_head_direction(
                        face
                    )
                )

                last_direction = direction

                stable_direction = (
                    get_stable_value(
                        direction_history,
                        direction,
                        DIRECTION_STABILITY_FRAMES
                    )
                )

                required = challenge[
                    challenge_index
                ]

                # =================================================
                # CORRECT POSE
                # =================================================

                if (
                    stable_direction ==
                    required
                ):

                    if stable_start is None:

                        stable_start = (
                            time.time()
                        )

                    held_time = (
                        time.time()
                        - stable_start
                    )

                    pose_progress = min(
                        held_time /
                        POSE_STABLE_TIME,
                        1.0
                    )

                    overall_progress = (
                        challenge_index
                        + pose_progress
                    ) / len(challenge)

                    draw_interface(
                        frame,
                        mode,
                        f"HOLD {required} POSITION",
                        GREEN,
                        (
                            recognized_person["name"]
                            if recognized_person
                            else person["name"]
                        ),
                        (
                            best_score
                            if best_score is not None
                            else score
                        ),
                        required,
                        stable_direction,
                        overall_progress
                    )

                    # --------------------------------------------
                    # POSE COMPLETED
                    # --------------------------------------------

                    if (
                        held_time >=
                        POSE_STABLE_TIME
                    ):

                        challenge_index += 1

                        stable_start = None

                        direction_history.clear()

                        # ----------------------------------------
                        # VERIFICATION COMPLETE
                        # ----------------------------------------

                        if (
                            challenge_index >=
                            len(challenge)
                        ):

                            camera.release()

                            cv2.destroyWindow(
                                window_name
                            )

                            cv2.destroyAllWindows()

                            return {
                                "success": True,
                                "reason":
                                    "LIVE VERIFICATION PASSED",
                                "person":
                                    (
                                        recognized_person
                                        or person
                                    )
                            }

                # =================================================
                # WRONG POSE
                # =================================================

                else:

                    stable_start = None

                    draw_interface(
                        frame,
                        mode,
                        f"TURN HEAD: {required}",
                        CYAN,
                        (
                            recognized_person["name"]
                            if recognized_person
                            else person["name"]
                        ),
                        (
                            best_score
                            if best_score is not None
                            else score
                        ),
                        required,
                        last_direction,
                        (
                            challenge_index /
                            len(challenge)
                        )
                    )

            # ====================================================
            # FACE NOT RECOGNIZED
            # ====================================================

            else:

                verification_start = None

                recognition_history.clear()

                direction_history.clear()

                stable_start = None

                draw_interface(
                    frame,
                    mode,
                    "FACE NOT RECOGNIZED",
                    RED,
                    progress=(
                        challenge_index /
                        len(challenge)
                    )
                )

        # ========================================================
        # TIMEOUT
        # ========================================================

        if (
            verification_start is not None
            and
            time.time()
            - verification_start
            >
            CHALLENGE_TIME_LIMIT
        ):

            camera.release()

            cv2.destroyWindow(
                window_name
            )

            cv2.destroyAllWindows()

            return {
                "success": False,
                "reason":
                    "LIVE VERIFICATION FAILED",
                "person": None
            }

        # ========================================================
        # SHOW FRAME
        # ========================================================

        cv2.imshow(
            window_name,
            frame
        )

        key = (
            cv2.waitKey(1)
            & 0xFF
        )

        # ========================================================
        # CANCEL
        # ========================================================

        if key == ord("q"):

            camera.release()

            cv2.destroyWindow(
                window_name
            )

            cv2.destroyAllWindows()

            return {
                "success": False,
                "reason":
                    "Verification cancelled.",
                "person": None
            }