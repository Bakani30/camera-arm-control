# Camera Gesture Implementation Plan
Goal: webcam preview with stable 01/10/00 outputs and timestamped CSV events.
Architecture: pure state mapping in camera_gestures/state.py; camera/model/display/logging in camera_gestures/app.py; explicit model download helper. Python 3.11, MediaPipe Tasks, OpenCV.
Spec: docs/superpowers/specs/2026-09-18-camera-gestures-design.md

1. Implement and test mapping/state transitions: palm/fist dwell, immediate reset for missing/low-score/unknown, changed gesture and long observation gaps.
2. Add explicit pretrained-model download and camera preview. Release camera/model/window on errors, emit 00 at shutdown, report camera read failure. CSV logs transitions with session config. No commands sent to hardware.
3. Document PowerShell install/run and manual trials. Run unit tests, compile check and real model smoke test if dependencies available. Mark Windows/webcam tests NOT RUN unless physically tested.
No git repository exists; no commit can be created here. User authorized implementation; proceed locally without another approval round.
