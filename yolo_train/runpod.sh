#!/bin/bash
apt-get update
apt-get --assume-yes install zip

pip install ultralytics
unzip -q /content/yolo.zip

wget https://ultralytics.com/assets/coco2017labels-segments.zip
unzip -q coco2017labels-segments.zip

python /content/seg_to_bbox.py -l /content/coco/labels/train2017
python /content/seg_to_bbox.py -l /content/coco/labels/val2017

python /content/replace_class.py -l /content/coco/labels/train2017 --input_yaml=/content/coco.yaml --output_yaml=/content/yolo/room.yaml
python /content/replace_class.py -l /content/coco/labels/val2017 --input_yaml=/content/coco.yaml --output_yaml=/content/yolo/room.yaml

find /content/coco/labels/train2017 -name '*.txt' -exec mv {} /content/yolo/data/train/labels/ \;
find /content/coco/labels/val2017 -name '*.txt' -exec mv {} /content/yolo/data/validation/labels/ \;

wget http://images.cocodataset.org/zips/train2017.zip
wget http://images.cocodataset.org/zips/val2017.zip

unzip -q /content/train2017.zip
unzip -q /content/val2017.zip

find /content/train2017 -name '*.jpg' -exec mv {} /content/yolo/data/train/images/ \;
find /content/val2017 -name '*.jpg' -exec mv {} /content/yolo/data/validation/images/ \;

rm -fR train2017.zip val2017.zip coco

#yolo detect train data=/content/yolo/room.yaml model=yolo11n.pt epochs=100 imgsz=320
yolo detect train data=/content/yolo/room.yaml model=yolo11n.pt epochs=100 imgsz=320 device=0,1
