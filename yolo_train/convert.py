from ultralytics import YOLO

model = YOLO("yolo11n_320_room.pt")
model.export(format="onnx")