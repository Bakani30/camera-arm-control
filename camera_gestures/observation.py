"""Expose model results without temporal filtering or invented confidence."""

def extract(result):
    present = bool(result.hand_landmarks)
    gesture, score = 'No_hand' if not present else 'Unknown', 0.0
    if present and result.gestures and result.gestures[0]:
        top = max(result.gestures[0], key=lambda category: category.score)
        gesture, score = top.category_name, float(top.score)
    handedness = 'Unknown'
    if present and result.handedness and result.handedness[0]:
        handedness = result.handedness[0][0].category_name
    points = [[float(p.x), float(p.y), float(p.z)] for p in result.hand_landmarks[0]] if present else []
    return dict(hand_present=present, gesture=gesture, score=score,
                handedness=handedness, landmarks=points)
