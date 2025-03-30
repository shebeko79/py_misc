import sys
import os
import cv2
import json
import numpy as np
from PIL import Image, ExifTags
from glob import glob
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QFileDialog, QLabel
from PyQt5.QtWidgets import QDesktopWidget, QMessageBox, QCheckBox
from PyQt5.QtGui import QPixmap, QPainter, QBrush, QColor, QPen, QFont
from PyQt5.QtCore import QRect, QPoint

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.fileName = QLabel('Ready')
        self.cursorPos = QLabel('      ')
        self.imageSize = QLabel('      ')
        self.progress = QLabel('                 ')

        mainWidget = MainWidget(self)

        self.setCentralWidget(mainWidget)
        statusbar = self.statusBar()
        self.setStatusBar(statusbar)

        widget = QWidget(self)
        widget.setLayout(QHBoxLayout())
        widget.layout().addWidget(self.fileName)
        widget.layout().addStretch(1)
        widget.layout().addWidget(self.imageSize)
        widget.layout().addWidget(self.cursorPos)
        widget.layout().addStretch(1)
        widget.layout().addWidget(self.progress)
        statusbar.addWidget(widget, 1)

        self.setGeometry(50, 50, 1200, 800)
        self.setWindowTitle('Labeling tool')
        self.show()
        
    def fitSize(self):
        self.setFixedSize(self.layout().sizeHint())


class MainWidget(QWidget):
    def __init__(self, parent):
        super(MainWidget, self).__init__(parent)
        self.parent = parent
        self.directory = None
        self.classes = []
        self.images = []
        self.cur_image = 0

        self.initUI()

        self.loadConfig()
        self.initImagesDirectory()
        self.setCurrentImage()
        self.check_controls()


    def initUI(self):
        self.label_img = ImageWidget(self.parent)

        self.prevButton = QPushButton('Prev', self)
        self.prevButton.clicked.connect(self.prevImage)

        self.nextButton = QPushButton('Next', self)
        self.nextButton.clicked.connect(self.nextImage)

        self.clearButton = QPushButton('Clear', self)
        self.clearButton.clicked.connect(self.label_img.cancelLast)

        hbox = QHBoxLayout()

        vbox = QVBoxLayout()
        vbox.addWidget(self.clearButton)
        hbox.addLayout(vbox)

        hbox.addStretch(3)
        hbox.addWidget(self.prevButton)
        hbox.addWidget(self.nextButton)

        vbox = QVBoxLayout()
        vbox.addWidget(self.label_img)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

    def check_controls(self):
        valid_img = 0 < self.cur_image < len(self.images)

        self.prevButton.setEnabled(self.cur_image > 0)
        self.nextButton.setEnabled(self.cur_image+1 < len(self.images))
        self.clearButton.setEnabled(valid_img)
        pass

    def prevImage(self):
        if self.cur_image <= 0:
            return

        self.cur_image -= 1
        self.setCurrentImage()
        self.check_controls()

    def nextImage(self):
        if self.cur_image >= len(self.images):
            return

        self.cur_image += 1
        self.setCurrentImage()
        self.check_controls()

    def setCurrentImage(self):
        if self.cur_image < 0 or self.cur_image >= len(self.images):
            self.parent.fileName.setText("")
            self.parent.progress.setText("")
            self.label_img.resetResult()
            return

        img_file = self.images[self.cur_image]
        filename, ext = os.path.splitext(img_file)

        img_file = os.path.join(self.directory, "images/"+img_file)
        txt_file = os.path.join(self.directory, "labels/"+filename+".txt")

        self.parent.fileName.setText(filename)
        self.parent.progress.setText(str(self.cur_image)+'/'+str(len(self.images)))

        self.label_img.setPixmap(img_file)
        self.label_img.update()
        self.parent.fitSize()

    def writeResults(self, res:list):
        if self.parent.fileName.text() != 'Ready':
            W, H = self.label_img.getRatio()
            if not res:
                open(self.currentImg[:-4]+'.txt', 'a', encoding='utf8').close()
            for i, elements in enumerate(res):  # box : (lx, ly, rx, ry, idx)
                lx, ly, rx, ry, idx = elements
                # yolo : (idx center_x_ratio, center_y_ratio, width_ratio, height_ratio)
                yolo_format = [idx, (lx+rx)/2/W, (ly+ry)/2/H, (rx-lx)/W, (ry-ly)/H]
                with open(self.currentImg[:-4]+'.txt', 'a', encoding='utf8') as resultFile:
                    resultFile.write(' '.join([str(x) for x in yolo_format])+'\n')

    def initImagesDirectory(self):
        if self.directory is None or not os.path.isdir(self.directory):
            self.directory = str(QFileDialog.getExistingDirectory(self, "Select Input Directory"))
            if self.directory == "":
                exit(1)
            self.saveConfig()

        self.classes = []

        file_name = os.path.join(self.directory, "classes.txt")
        if os.path.exists(file_name):
            with open(file_name, "r") as file:
                self.classes = file.read().splitlines()

        self.images = []

        file_name = os.path.join(self.directory, "images")
        if os.path.exists(file_name):
            for entry in os.scandir(file_name):
                if not entry.is_file():
                    continue

                basename = os.path.basename(entry)
                filename, ext = os.path.splitext(basename)
                if ext.lower() == '.jpg' or ext.lower() == '.png':
                 self.images.append(basename)

        self.images.sort()

        txt_files = {}
        file_name = os.path.join(self.directory, "labels")
        if os.path.exists(file_name):
            for entry in os.scandir(file_name):
                if not entry.is_file():
                    continue

                basename = os.path.basename(entry)
                filename, ext = os.path.splitext(basename)
                if ext.lower() == '.txt':
                    txt_files[filename.lower()] = 1

        self.cur_image = 0
        while self.cur_image < len(self.images) - 1:
            filename, ext = os.path.splitext(self.images[self.cur_image])
            if not (filename.lower() in txt_files):
                break

            self.cur_image += 1

    def loadConfig(self):
        if not os.path.exists('config.json'):
            self.directory = None
            return

        with open('config.json', 'r') as config_file:
            try:
                config_dict = json.load(config_file)
            except ValueError:
                config_dict = {}

        self.directory = config_dict["directory"]

    def saveConfig(self):
        config_dict = {}
        config_dict["directory"] = self.directory

        with open('config.json', 'w') as config_file:
            json.dump(config_dict, config_file)

    def keyPressEvent(self, e):
        config_len = len(self.key_config)
        for i, key_n in enumerate(range(49,58), 1):
            if e.key() == key_n and config_len >= i:
                self.label_img.markBox(i-1) 
                break
        if e.key() == Qt.Key_Escape:
            self.label_img.cancelLast()
        elif e.key() == Qt.Key_E:
            self.setNextImage()
        elif e.key() == Qt.Key_Q:
            self.label_img.resetResult()
            self.label_img.pixmap = self.label_img.drawResultBox()
            self.label_img.update()


class ImageWidget(QWidget):
    def __init__(self, parent):
        super(ImageWidget, self).__init__(parent)
        self.parent = parent
        self.results = []
        self.setMouseTracking(True)
        self.screen_height = QDesktopWidget().screenGeometry().height()
        self.last_idx = 0

        self.initUI()

    def initUI(self):
        self.pixmap = QPixmap('start.png')
        self.label_img = QLabel()
        self.label_img.setObjectName("image")
        self.pixmapOriginal = QPixmap.copy(self.pixmap)

        self.drawing = False
        self.lastPoint = QPoint()
        hbox = QHBoxLayout(self.label_img)
        self.setLayout(hbox)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.prev_pixmap = self.pixmap
            self.drawing = True
            self.lastPoint = event.pos()
        elif event.button() == Qt.RightButton:
            x, y = event.pos().x(), event.pos().y()
            for i, box in enumerate(self.results):
                lx, ly, rx, ry = box[:4]
                if lx <= x <= rx and ly <= y <= ry:
                    self.results.pop(i)
                    self.pixmap = self.drawResultBox()
                    self.update()
                    break

    def mouseMoveEvent(self, event):
        self.parent.cursorPos.setText('({}, {})'
                                      .format(event.pos().x(), event.pos().y()))
        if event.buttons() and Qt.LeftButton and self.drawing:
            self.pixmap = QPixmap.copy(self.prev_pixmap)
            painter = QPainter(self.pixmap)
            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            p1_x, p1_y = self.lastPoint.x(), self.lastPoint.y()
            p2_x, p2_y = event.pos().x(), event.pos().y()
            painter.drawRect(min(p1_x, p2_x), min(p1_y, p2_y),
                             abs(p1_x - p2_x), abs(p1_y - p2_y))
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            p1_x, p1_y = self.lastPoint.x(), self.lastPoint.y()
            p2_x, p2_y = event.pos().x(), event.pos().y()
            lx, ly = min(p1_x, p2_x), min(p1_y, p2_y)
            w, h = abs(p1_x - p2_x), abs(p1_y - p2_y)
            if (p1_x, p1_y) != (p2_x, p2_y):
                if self.results and (len(self.results[-1]) == 4):
                    self.showPopupOk('warning messege',
                                     'Please mark the box you drew.')
                    self.pixmap = self.drawResultBox()
                    self.update()
                else:
                    self.results.append([lx, ly, lx + w, ly + h])
                self.drawing = False

    def showPopupOk(self, title: str, content: str):
        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(content)
        msg.setStandardButtons(QMessageBox.Ok)
        result = msg.exec_()
        if result == QMessageBox.Ok:
            msg.close()

    def drawResultBox(self):
        res = QPixmap.copy(self.pixmapOriginal)
        painter = QPainter(res)
        font = QFont('mono', 15, 1)
        painter.setFont(font)
        painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
        for box in self.results:
            lx, ly, rx, ry = box[:4]
            painter.drawRect(lx, ly, rx - lx, ry - ly)
            if len(box) == 5:
                painter.setPen(QPen(Qt.blue, 2, Qt.SolidLine))
                painter.drawText(lx, ly + 15, self.key_config[box[-1]])
                painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
        return res

    def setPixmap(self, image_fn):
        self.pixmap = QPixmap(image_fn)
        self.W, self.H = self.pixmap.width(), self.pixmap.height()

        if self.H > self.screen_height * 0.8:
            resize_ratio = (self.screen_height * 0.8) / self.H
            self.W = round(self.W * resize_ratio)
            self.H = round(self.H * resize_ratio)
            self.pixmap = QPixmap.scaled(self.pixmap, self.W, self.H,
                                         transformMode=Qt.SmoothTransformation)

        self.parent.imageSize.setText('{}x{}'.format(self.W, self.H))
        self.setFixedSize(self.W, self.H)
        self.pixmapOriginal = QPixmap.copy(self.pixmap)

    def cancelLast(self):
        if self.results:
            self.results.pop()  # pop last
            self.pixmap = self.drawResultBox()
            self.update()

    def getRatio(self):
        return self.W, self.H

    def getResult(self):
        return self.results

    def resetResult(self):
        self.results = []

    def markBox(self, idx):
        self.last_idx = idx
        if self.results:
            if len(self.results[-1]) == 4:
                self.results[-1].append(idx)
            elif len(self.results[-1]) == 5:
                self.results[-1][-1] = idx
            else:
                raise ValueError('invalid results')
            self.pixmap = self.drawResultBox()
            self.update()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())