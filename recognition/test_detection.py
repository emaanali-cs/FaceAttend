import cv2

from recognition.face_recognition import FaceDetector, draw_faces


def main():

    detector = FaceDetector()

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("ERROR: Could not open camera.")
        return

    print("Face detection started.")
    print("Press Q to close.")

    while True:

        success, frame = camera.read()

        if not success:
            print("ERROR: Could not read camera frame.")
            break

        # Detect faces
        faces = detector.detect(frame)

        # Draw face boxes
        frame = draw_faces(frame, faces)

        # Display number of faces
        cv2.putText(
            frame,
            f"Faces detected: {len(faces)}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        cv2.imshow("Face Detection Test", frame)

        # Press Q to quit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()