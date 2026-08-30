import cv2

from recognition.face_recognition import (
    FaceSystem,
    load_registered_faces,
    recognize_face
)


# ============================================================
# SETTINGS
# ============================================================

CAMERA_ID = 0

MATCH_THRESHOLD = 0.40


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 55)
    print("       DATABASE FACE RECOGNITION TEST")
    print("=" * 55)
    print()

    # --------------------------------------------------------
    # Load face system
    # --------------------------------------------------------

    face_system = FaceSystem()

    # --------------------------------------------------------
    # Load registered employees
    # --------------------------------------------------------

    registered_faces = load_registered_faces()

    print(
        f"Registered face samples: "
        f"{len(registered_faces)}"
    )

    if not registered_faces:

        print("No registered faces found.")
        return

    # --------------------------------------------------------
    # Camera
    # --------------------------------------------------------

    camera = cv2.VideoCapture(CAMERA_ID)

    if not camera.isOpened():

        print("Could not open camera.")
        return

    while True:

        success, frame = camera.read()

        if not success:
            break

        frame = cv2.flip(frame, 1)

        faces = face_system.detect(frame)

        cv2.putText(
            frame,
            f"Faces detected: {len(faces)}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        # ----------------------------------------------------
        # Only recognize one face
        # ----------------------------------------------------

        if len(faces) == 1:

            face = faces[0]

            x, y, w, h = face[:4]

            x = int(x)
            y = int(y)
            w = int(w)
            h = int(h)

            # Generate live SFace feature
            feature = face_system.get_feature(
                frame,
                face
            )

            match, score = recognize_face(
                face_system,
                feature,
                registered_faces
            )

            # ------------------------------------------------
            # Recognition decision
            # ------------------------------------------------

            if match and score >= MATCH_THRESHOLD:

                label = (
                    f"{match['name']} "
                    f"({match['employee_code']})"
                )

                status = f"MATCH {score:.3f}"

            else:

                label = "UNKNOWN"
                status = f"NO MATCH {score:.3f}"

            # ------------------------------------------------
            # Draw
            # ------------------------------------------------

            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                label,
                (x, max(y - 30, 25)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                status,
                (x, y + h + 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 0),
                2
            )

        elif len(faces) > 1:

            cv2.putText(
                frame,
                "ONLY ONE PERSON ALLOWED",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )

        else:

            cv2.putText(
                frame,
                "NO FACE DETECTED",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 200, 255),
                2
            )

        cv2.imshow(
            "Database Face Recognition",
            frame
        )

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()