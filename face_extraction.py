import cv2

image = cv2.imread("sample-indian-passport-1.jpg")

if image is None:
    print("Image not found")
    exit()

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

if len(faces) == 0:
    print("No face extraction")

else:
    x, y, w, h = faces[0]

    # Add extra area around the face
    padding = 20

    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(image.shape[1], x + w + padding)
    y2 = min(image.shape[0], y + h + padding)

    # Extract face
    face = image[y1:y2, x1:x2]

    # Resize for further processing
    face = cv2.resize(face, (224, 224))

    # Display extracted face
    cv2.imshow("Extracted Face", face)

    print("Face extracted successfully!")

    cv2.waitKey(0)
    cv2.destroyAllWindows()