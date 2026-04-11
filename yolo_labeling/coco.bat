rem seg_to_bbox.py -l C:\src\py\detection\coco\labels\train2017
rem seg_to_bbox.py -l C:\src\py\detection\coco\labels\val2017

rem replace_class.py -l C:\src\py\detection\coco\labels\train2017 --input_yaml=C:\src\py\detection\coco\coco.yaml --output_yaml=C:\src\py\detection\room\yolo\room.yaml
rem replace_class.py -l C:\src\py\detection\coco\labels\val2017 --input_yaml=C:\src\py\detection\coco\coco.yaml --output_yaml=C:\src\py\detection\room\yolo\room.yaml

remove_empty.py -l C:\src\py\detection\coco\labels\train2017