# Save this temporarily as download_models.py and run it: `python download_models.py`
import os
import urllib.request

os.makedirs("models", exist_ok=True)

files = {
    "models/face_detection_yunet_2023mar.onnx": "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
    "models/face_recognition_sface_2021dec.onnx": "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"
}

for path, url in files.items():
    if not os.path.exists(path):
        print(f"Downloading {path}...")
        urllib.request.urlretrieve(url, path)
        print("Done!")
    else:
        print(f"{path} already exists.")