import cv2

from recognition.face_recognition import FaceSystem


def main():

    face_system = FaceSystem()

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("ERROR: Could not open camera.")
        return

    print()
    print("Face recognition test started.")
    print("Press Q to exit.")
    print()

    while True:

        success, frame = camera.read()

        if not success:
            print("ERROR: Could not read camera.")
            break

        # Detect faces
        faces = face_system.detect(frame)

        for face in faces:

            # Generate face feature
            feature = face_system.get_feature(
                frame,
                face
            )

            print(
                "Face feature generated:",
                feature.shape
            )

        # Draw detected faces
        for face in faces:

            x, y, w, h = face[:4]

            x = int(x)
            y = int(y)
            w = int(w)
            h = int(h)

            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                (0, 255, 0),
                2
            )

        cv2.putText(
            frame,
            f"Faces detected: {len(faces)}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        cv2.imshow(
            "Face Recognition Test",
            frame
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()