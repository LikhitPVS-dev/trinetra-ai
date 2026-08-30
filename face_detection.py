import cv2


def detect_face(image_path):

    image = cv2.imread(image_path)

    if image is None:
        return False

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades +
        "haarcascade_frontalface_default.xml"
    )

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5
    )


    if len(faces) > 0:
        return True

    return False


result = detect_face("passport.jpg")

print("Face detected:", result)
