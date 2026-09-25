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


def extract_selected(result, side):
    """Reject ambiguous same-side detections; never fall back to the other hand."""
    from types import SimpleNamespace
    matches = []
    for i, categories in enumerate(result.handedness):
        if categories:
            top = max(categories, key=lambda c: c.score)
            if top.category_name == side and top.score >= .8 and i < len(result.hand_landmarks):
                matches.append(i)
    if len(matches) != 1:
        return extract(SimpleNamespace(hand_landmarks=[], gestures=[], handedness=[]))
    i = matches[0]
    return extract(SimpleNamespace(hand_landmarks=[result.hand_landmarks[i]],
        gestures=[result.gestures[i]] if i < len(result.gestures) else [],
        handedness=[result.handedness[i]]))
