import cv2
from face_verification import TRINETRAFaceVerifier

# Optional: You can test on your webcam real quick!
verifier = TRINETRAFaceVerifier()

# Make fake blank images just to see the output structure
fake_img = cv2.imread("any_pic_on_your_pc.jpg") 

result = verifier.verify(fake_img, fake_img)
print("Contract Output:")
print(result)