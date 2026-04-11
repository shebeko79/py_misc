from ultralytics import YOLO

# Load the YOLOv8n-seg model (make sure it's the segmentation variant)
model = YOLO('yolo11n_320_room.pt')
#model = YOLO('yolov8n.pt')
#model = YOLO('FastSAM-s.pt')

# Run real-time inference on webcam (device 0 by default)
#results = model.track(source=0, show=True, stream=True,imgsz=640, conf=0.7, iou=0.9)
results = model.track(source=0, show=True, stream=True, imgsz=640, conf=0.3, iou=0.5)

# Process results
for result in results:
#    # Access detection boxes
    boxes = result.boxes
#    # Access segmentation masks
    masks = result.masks
#    # ... (additional processing)