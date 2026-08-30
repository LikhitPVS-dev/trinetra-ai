import cv2
import os
from face_verification import TRINETRAFaceVerifier

def main():
    verifier = TRINETRAFaceVerifier()
    
    test_image_path = "test_face.jpg"
    
    if not os.path.exists(test_image_path):
        print(f"ERROR: Please place a real image named '{test_image_path}' in this folder.")
        print("Don't worry, it is ignored by Git.")
        return

    img = cv2.imread(test_image_path)
    
    print("Testing verification pipeline...")
    # Passing the same image twice should result in a 100% match
    result = verifier.verify(img, img)
    
    print("\n--- PIPELINE RESULT ---")
    print(result)

if __name__ == "__main__":
    main()