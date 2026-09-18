"""Download the official pretrained gesture model; run once with internet."""
from pathlib import Path
from urllib.request import urlopen

MODEL = Path(__file__).resolve().parent.parent / 'models' / 'gesture_recognizer.task'
URL = 'https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task'


def main():
    MODEL.parent.mkdir(exist_ok=True)
    temporary = MODEL.with_suffix('.download')
    try:
        with urlopen(URL, timeout=60) as response, temporary.open('wb') as out:
            while chunk := response.read(1024 * 1024):
                out.write(chunk)
        temporary.replace(MODEL)
    finally:
        temporary.unlink(missing_ok=True)
    print(MODEL)


if __name__ == '__main__':
    main()
