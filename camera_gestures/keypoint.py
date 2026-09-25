"""Adapted from Kazuhito Takahashi's Apache-2.0 sample; see third_party/kazuhito.

Normalization reduces translation/scale differences, not detection errors or
perspective/occlusion. The pretrained model has only Open/Close/Pointer classes.
"""
import hashlib
import math
from pathlib import Path

MODEL = Path(__file__).resolve().parent.parent / 'models/kazuhito_keypoint.tflite'
SHA256 = 'de646612f72941523d01ddb8cff8685ded1781f1a3b254eb5674c5f616782580'
LABELS = ('Open_Palm', 'Closed_Fist', 'Pointing_Up')


def normalize(points, width, height):
    if len(points) != 21 or width <= 0 or height <= 0:
        return None
    if any(len(p) < 2 or not all(math.isfinite(v) for v in p[:2]) for p in points):
        return None
    # Match upstream pixel conversion and axis scaling before wrist centering.
    pixels = [(min(int(p[0]*width), width-1), min(int(p[1]*height), height-1)) for p in points]
    x, y = pixels[0]
    values = [v for px, py in pixels for v in (px-x, py-y)]
    scale = max(map(abs, values))
    return [v/scale for v in values] if scale else None


class KeypointClassifier:
    def __init__(self, path=MODEL):
        if not path.is_file():
            raise ValueError('Run python -m camera_gestures.download_keypoint first')
        if hashlib.sha256(path.read_bytes()).hexdigest() != SHA256:
            raise ValueError('Keypoint model checksum mismatch; download again')
        import tensorflow as tf
        self.interpreter = tf.lite.Interpreter(model_path=str(path), num_threads=1)
        self.interpreter.allocate_tensors()
        self.input = self.interpreter.get_input_details()[0]['index']
        self.output = self.interpreter.get_output_details()[0]['index']

    def predict(self, points, width, height):
        values = normalize(points, width, height)
        if values is None:
            return 'Unknown', 0.0
        import numpy as np
        self.interpreter.set_tensor(self.input, np.asarray([values], dtype=np.float32))
        self.interpreter.invoke()
        scores = self.interpreter.get_tensor(self.output).reshape(-1)
        if len(scores) != len(LABELS) or not np.isfinite(scores).all():
            return 'Unknown', 0.0
        index = int(np.argmax(scores))
        return LABELS[index], float(scores[index])
