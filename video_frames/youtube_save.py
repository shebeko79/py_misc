from vidgear.gears import CamGear
from vidgear.gears import WriteGear
import cv2
import sys
import os
import params

def getYoutubeId(video_url):
    file_name = video_url
    file_name = file_name.replace("https://","")
    file_name = file_name.replace("www.youtu.be/","")
    file_name = file_name.replace("www.youtube.com/watch?v=","")
    file_name = file_name.replace("youtu.be/","")
    file_name = file_name.replace("youtube.com/watch?v=","")

    pos = file_name.find('?')
    if pos != -1:
        file_name = file_name[:pos]

    pos = file_name.find('&')
    if pos != -1:
        file_name = file_name[:pos]
        
    return file_name


if len(sys.argv) < 2:
    print(f'Use {sys.argv[0]} <URL>')
    sys.exit()

video_url = sys.argv[1]


file_name = os.path.join(params.video_directory, getYoutubeId(video_url)+".mp4")
print( file_name)



stream = CamGear(source=video_url, stream_mode=True, logging=True).start()
writer = WriteGear(output = file_name) 

count = 0 

while True:
    frame = stream.read()
    if frame is None:
        break
        
    writer.write(frame)
    
    count += 1;
    if (count %300) == 0:
        print("#", end="")
        
print("")
stream.stop()
writer.close()
cv2.destroyAllWindows()
