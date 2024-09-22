from vidgear.gears import CamGear
from vidgear.gears import WriteGear
from enum import Enum
import cv2
import sys
import os
import params

class PlayState(Enum):
    BEGIN = 1
    PLAY = 2
    PAUSE = 3
    FRAME_FORWARD = 4
    FRAME_BACKWARD = 5
    
def cropFrame(frame):
    return cv2.resize(frame, params.model_size)

images_count = 0    

def saveImage(baseName, frame):
    global images_count
    
    while True:
        images_count += 1
        fileName = os.path.join(params.images_directory, baseName+"_"+str(images_count)+".jpg")
        if not os.path.exists(fileName):
            break
    
    print (fileName)
    cv2.imwrite(fileName, frame)


def processFile(filePath):
    stream = CamGear(source=filePath).start()
    
    state = PlayState.BEGIN
    
    windowName = 'Process video'
    
    baseName = os.path.splitext(os.path.basename(filePath))[0]
    
    leftArrow = 0x250000
    rightArrow = 0x270000
    
    frames_buf = [] 
    MAX_FRAMES = 300
    frames_buf_pos = 0
    
    while True:

        if state != PlayState.BEGIN and cv2.getWindowProperty(windowName, cv2.WND_PROP_VISIBLE) < 1:
            break
        
        if state == PlayState.FRAME_BACKWARD:
            if frames_buf_pos > 0:
                if frames_buf_pos>1 and frames_buf_pos == len(frames_buf):
                    frames_buf_pos -=2
                else:
                    frames_buf_pos -= 1
            
                frame = frames_buf[frames_buf_pos]
                cv2.imshow(windowName, frame)

        elif state != PlayState.PAUSE:
            if frames_buf_pos < len(frames_buf):
                frame = frames_buf[frames_buf_pos]
                frames_buf_pos += 1
                cv2.imshow(windowName, frame)

            else:
                frame = stream.read()
                if frame is None:
                    break
                    
                if len(frames_buf) >= MAX_FRAMES:
                    frames_buf.pop(0)
                    
                frame = cropFrame(frame)

                frames_buf.append(frame)
                frames_buf_pos = len(frames_buf)
                
                cv2.imshow(windowName, frame)
        
        if state == PlayState.BEGIN or state == PlayState.FRAME_FORWARD or state == PlayState.FRAME_BACKWARD:
           state = PlayState.PAUSE

        key = cv2.waitKeyEx(1)
        
        if (key&0xFF) == ord(" "):
            if state == PlayState.PAUSE:
                state = PlayState.PLAY
            elif state == PlayState.PLAY:
                state = PlayState.PAUSE

            continue
        elif key == rightArrow:
            state = PlayState.FRAME_FORWARD
            continue
        elif key == leftArrow:
            state = PlayState.FRAME_BACKWARD
            continue
        elif (key&0xFF) == 0xd:
            if frames_buf_pos >=len(frames_buf):
                frame = frames_buf[-1]
            else:
                frame = frames_buf[frames_buf_pos]
            
            saveImage(baseName, frame)
        
        
            

    cv2.destroyAllWindows()
    stream.stop()





if len(sys.argv) < 2:
    print(f'Use {sys.argv[0]} <video_file_name>')
    sys.exit()

processFile(sys.argv[1])