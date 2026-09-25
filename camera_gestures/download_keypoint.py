"""Fetch pinned upstream model and verify bytes before use."""
import hashlib
from urllib.request import urlopen
from .keypoint import MODEL, SHA256
URL = 'https://raw.githubusercontent.com/Kazuhito00/hand-gesture-recognition-using-mediapipe/19311a68b16b42d3ee89e505e3f185693dbd7147/model/keypoint_classifier/keypoint_classifier.tflite'

def main():
    with urlopen(URL, timeout=60) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError('Downloaded model checksum mismatch')
    MODEL.parent.mkdir(exist_ok=True)
    MODEL.write_bytes(data)
    print(MODEL)

if __name__ == '__main__':
    main()
