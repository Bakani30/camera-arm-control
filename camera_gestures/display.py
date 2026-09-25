"""Camera overlay and independent two-dimensional target canvas."""
import math


def hand_box(points, width, height):
    if not points or not all(math.isfinite(v) for p in points for v in p[:2]):
        return None
    xs, ys = [p[0]*width for p in points], [p[1]*height for p in points]
    clamp = lambda value, limit: max(0, min(limit-1, int(value)))
    return (clamp(min(xs)-12,width), clamp(min(ys)-12,height),
            clamp(max(xs)+12,width), clamp(max(ys)+12,height))


def draw(frame, observation, stale, threshold, target, depth=None):
    import cv2
    import numpy as np
    h,w = frame.shape[:2]
    box = None if stale else hand_box(observation['landmarks'],w,h)
    names = {'Open_Palm':'OPEN','Closed_Fist':'FIST','Pointing_Up':'POINT'}
    name = names.get(observation['gesture'],'UNKNOWN') if observation['score'] >= threshold else 'UNKNOWN'
    if box:
        x1,y1,x2,y2 = box
        color = (0,210,80) if name != 'UNKNOWN' else (0,180,255)
        cv2.rectangle(frame,(x1,y1),(x2,y2),color,2)
        cv2.putText(frame,f'{name} {observation["score"]:.2f}',(x1,max(22,y1-8)),cv2.FONT_HERSHEY_SIMPLEX,.7,color,2)
    else:
        cv2.putText(frame,'NO HAND / STALE',(12,h-20),cv2.FONT_HERSHEY_SIMPLEX,.7,(0,180,255),2)
    canvas = np.full((h,420,3),28,dtype=np.uint8)
    left,top,right,bottom = 30,100,390,max(160,h-80)
    cv2.rectangle(canvas,(left,top),(right,bottom),(100,100,100),1)
    def xy(point): return (int(left+point[0]*(right-left)),int(top+point[1]*(bottom-top)))
    for goal in [(.2,.2),(.8,.2),(.5,.5),(.2,.8),(.8,.8)]:
        cv2.circle(canvas,xy(goal),14,(90,90,90),1)
    cv2.circle(canvas,xy(target.raw),9,(0,180,255),1)
    cv2.circle(canvas,xy(target.position),7,(255,220,40),-1)
    for i,line in enumerate(['WRIST TARGET: '+('ACTIVE' if target.active else 'PAUSED'),
                             'C: resume  R: zero  SPACE: pause',
                             'L: left hand  H: right hand']):
        cv2.putText(canvas,line,(12,25+i*25),cv2.FONT_HERSHEY_SIMPLEX,.48,(230,230,230),1)
    if depth is not None:
        y = h-35
        cv2.line(canvas,(30,y),(390,y),(120,120,120),3)
        cv2.line(canvas,(210,y-6),(210,y+6),(190,190,190),1)
        cv2.circle(canvas,(int(210+depth.raw*180),y),8,(0,180,255),1)
        cv2.circle(canvas,(int(210+depth.value*180),y),6,(255,220,40),-1)
        status = 'ACTIVE' if depth.active else 'PAUSED: press C'
        cv2.putText(canvas,f'Depth {depth.value:+.2f} (relative) {status}',(12,h-53),cv2.FONT_HERSHEY_SIMPLEX,.43,(230,230,230),1)
        cv2.putText(canvas,'FAR (-)                 NEAR (+)',(30,h-10),cv2.FONT_HERSHEY_SIMPLEX,.45,(230,230,230),1)
    return np.hstack((frame,canvas))
