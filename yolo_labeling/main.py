import sys
import os
import cv2
import json
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QComboBox
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QFileDialog, QLabel
from PyQt5.QtWidgets import QDesktopWidget, QMessageBox, QPushButton
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
    def __init__(self, app):
        super(MainWidget, self).__init__(app)
        self.app = app
        self.directory = None
        self.classes = []
        self.images = []
        self.cur_image = 0

        self.initUI()

        self.loadConfig()
        self.initImagesDirectory()
        self.fillClassesCombo()
        self.setCurrentImage()
        self.check_controls()


    def initUI(self):
        self.label_img = ImageWidget(self)

        self.firstButton = QPushButton('First', self)
        self.firstButton.clicked.connect(self.firstImage)

        self.prevButton = QPushButton('<', self)
        self.prevButton.clicked.connect(self.prevImage)

        self.nextButton = QPushButton('>', self)
        self.nextButton.clicked.connect(self.nextImage)

        self.rewindButton = QPushButton('>>>', self)
        self.rewindButton.clicked.connect(self.nextUnmarkedImage)

        self.lastButton = QPushButton('Last', self)
        self.lastButton.clicked.connect(self.lastImage)

        self.removeLastButton = QPushButton('Remove Last', self)
        self.removeLastButton.clicked.connect(self.label_img.removeLast)

        self.removeAllButton = QPushButton('Remove All', self)
        self.removeAllButton.clicked.connect(self.label_img.removeAll)

        self.undoButton = QPushButton('Undo', self)
        self.undoButton.clicked.connect(self.label_img.reload)

        self.classesCombo = QComboBox(self)
        self.classesCombo.setFixedWidth(200)
        self.classesCombo.activated[int].connect(self.onClassesComboChanged)

        hbox = QHBoxLayout()

        hbox.addWidget(self.classesCombo)
        hbox.addStretch(1)
        hbox.addWidget(self.removeLastButton)
        hbox.addWidget(self.removeAllButton)
        hbox.addWidget(self.undoButton)

        hbox.addStretch(3)
        hbox.addWidget(self.firstButton)
        hbox.addWidget(self.prevButton)
        hbox.addWidget(self.nextButton)
        hbox.addWidget(self.rewindButton)
        hbox.addWidget(self.lastButton)

        vbox = QVBoxLayout()
        vbox.addWidget(self.label_img)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

    def fillClassesCombo(self):

        self.classesCombo.clear()
        for v in enumerate(self.classes):
            if v[0]<10:
                self.classesCombo.addItem(f'({v[0]}) {v[1]}')
            else:
                self.classesCombo.addItem(v[1])


        if len(self.classes):
            self.classesCombo.setCurrentIndex(0)


    def check_controls(self):
        valid_img = 0 < self.cur_image < len(self.images)
        not_first_img = self.cur_image > 0
        not_last_img = self.cur_image+1 < len(self.images)

        self.firstButton.setEnabled(not_first_img)
        self.prevButton.setEnabled(not_first_img)
        self.nextButton.setEnabled(not_last_img)
        self.rewindButton.setEnabled(not_last_img)
        self.lastButton.setEnabled(not_last_img)

        self.removeLastButton.setEnabled(valid_img)
        self.removeAllButton.setEnabled(valid_img)
        self.undoButton.setEnabled(valid_img)
        pass

    def firstImage(self):
        self.label_img.saveModifiedBoxes()
        self.cur_image = 0
        self.setCurrentImage()
        self.check_controls()

    def lastImage(self):
        self.label_img.saveModifiedBoxes()
        self.cur_image = 0
        if len(self.images) > 0:
            self.cur_image = len(self.images) - 1
        self.setCurrentImage()
        self.check_controls()

    def nextUnmarkedImage(self):
        self.label_img.saveModifiedBoxes()
        self.rewind_to_unmarked()
        self.setCurrentImage()
        self.check_controls()

    def prevImage(self):
        if self.cur_image <= 0:
            return

        self.label_img.saveModifiedBoxes()
        self.cur_image -= 1
        self.setCurrentImage()
        self.check_controls()

    def nextImage(self):
        if self.cur_image >= len(self.images):
            return

        self.label_img.saveModifiedBoxes()
        self.cur_image += 1
        self.setCurrentImage()
        self.check_controls()

    def setCurrentImage(self):
        if self.cur_image < 0 or self.cur_image >= len(self.images):
            self.app.fileName.setText("")
            self.app.progress.setText("")
            self.label_img.removeAll()
            return

        img_file = self.images[self.cur_image]
        filename, ext = os.path.splitext(img_file)

        img_file = os.path.join(self.directory, "images/"+img_file)
        txt_file = os.path.join(self.directory, "labels/"+filename+".txt")

        self.app.fileName.setText(filename)
        self.app.progress.setText(str(self.cur_image)+'/'+str(len(self.images)))

        self.label_img.init(img_file, txt_file)
        self.app.fitSize()

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

        self.cur_image = 0
        self.rewind_to_unmarked()

    def rewind_to_unmarked(self):
        labels_dir = os.path.join(self.directory, "labels")
        if self.cur_image < len(self.images) - 1:
            filename, ext = os.path.splitext(self.images[self.cur_image])
            file_path = os.path.join(labels_dir, filename + ".txt")
            if not os.path.exists(file_path):
                return

        txt_files = {}
        if os.path.exists(labels_dir):
            for entry in os.scandir(labels_dir):
                if not entry.is_file():
                    continue

                basename = os.path.basename(entry)
                filename, ext = os.path.splitext(basename)
                if ext.lower() == '.txt':
                    txt_files[filename.lower()] = 1

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
        k = e.key()
        if 0x30 <= e.key() <= 0x39:
            idx = e.key()-0x30
            if idx < self.classesCombo.count():
                self.classesCombo.setCurrentIndex(idx)
            self.label_img.markBox(idx)
        if e.key() == Qt.Key_Escape:
            self.label_img.removeLast()
        elif e.key() == Qt.Key_Right:
            self.nextImage()
        elif e.key() == Qt.Key_Left:
            self.prevImage()
        elif e.key() == Qt.Key_Up:
            sel_idx = self.classesCombo.currentIndex()
            sel_idx -= 1
            if sel_idx >= 0:
                self.classesCombo.setCurrentIndex(sel_idx)
                self.label_img.markBox(sel_idx)
        elif e.key() == Qt.Key_Down:
            sel_idx = self.classesCombo.currentIndex()
            sel_idx += 1
            if sel_idx < len(self.classes):
                self.classesCombo.setCurrentIndex(sel_idx)
                self.label_img.markBox(sel_idx)

    def onClassesComboChanged(self, idx):
        self.label_img.markBox(idx)
        self.setFocus()

class ImageWidget(QWidget):
    def __init__(self, main_widget: MainWidget):
        super(ImageWidget, self).__init__(main_widget.app)
        self.main_widget = main_widget
        self.app = main_widget.app
        self.results = []
        self.setMouseTracking(True)
        self.screen_height = QDesktopWidget().screenGeometry().height()
        self.txt_file = ""
        self.modified = False

        self.initUI()

    def initUI(self):
        self.pixmap = QPixmap()
        self.label_img = QLabel()
        self.label_img.setObjectName("image")
        self.pixmapOriginal = QPixmap.copy(self.pixmap)

        self.drawing = False
        self.lastPoint = QPoint()
        hbox = QHBoxLayout(self.label_img)
        self.setLayout(hbox)

    def init(self, img_file, txt_file):
        self.setPixmap(img_file)
        self.txt_file = txt_file
        self.loadBoxes()
        self.pixmap = self.drawResultBox()
        self.update()

    def setPixmap(self, image_fn):
        self.pixmap = QPixmap(image_fn)
        self.W, self.H = self.pixmap.width(), self.pixmap.height()

        if self.H > self.screen_height * 0.8:
            resize_ratio = (self.screen_height * 0.8) / self.H
            self.W = round(self.W * resize_ratio)
            self.H = round(self.H * resize_ratio)
            self.pixmap = QPixmap.scaled(self.pixmap, self.W, self.H,
                                         transformMode=Qt.SmoothTransformation)

        self.app.imageSize.setText('{}x{}'.format(self.W, self.H))
        self.setFixedSize(self.W, self.H)
        self.pixmapOriginal = QPixmap.copy(self.pixmap)

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
        self.app.cursorPos.setText(f'({event.pos().x()}, {event.pos().y()})')
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
        if event.button() != Qt.LeftButton:
            return

        p1_x, p1_y = self.lastPoint.x(), self.lastPoint.y()
        p2_x, p2_y = event.pos().x(), event.pos().y()
        lx, ly = min(p1_x, p2_x), min(p1_y, p2_y)
        w, h = abs(p1_x - p2_x), abs(p1_y - p2_y)
        if (p1_x, p1_y) == (p2_x, p2_y):
            return

        self.drawing = False
        self.results.append([lx, ly, lx + w, ly + h, 0])

        sel_idx = self.main_widget.classesCombo.currentIndex()
        if sel_idx < 0:
            sel_idx = 0
        self.markBox(sel_idx)

    def drawResultBox(self):
        res = QPixmap.copy(self.pixmapOriginal)
        painter = QPainter(res)
        font = QFont('mono', 15, 1)
        painter.setFont(font)
        painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
        for box in self.results:
            lx, ly, rx, ry = box[:4]
            painter.drawRect(lx, ly, rx - lx, ry - ly)
            idx = box[4]
            if 0 <= idx < len(self.main_widget.classes):
                painter.setPen(QPen(Qt.blue, 2, Qt.SolidLine))
                painter.drawText(lx, ly + 15, self.main_widget.classes[idx])
                painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
        return res

    def removeLast(self):
        if len(self.results)>0:
            self.results.pop()  # pop last
            self.modified = True
            self.pixmap = self.drawResultBox()
            self.update()
            self.main_widget.check_controls()

    def removeAll(self):
        self.results = []
        self.modified = True
        self.pixmap = self.drawResultBox()
        self.update()
        self.main_widget.check_controls()

    def reload(self):
        self.loadBoxes()
        self.pixmap = self.drawResultBox()
        self.update()
        self.main_widget.check_controls()

    def markBox(self, idx):
        if len(self.results)>0:
            self.results[-1][-1] = idx

        self.modified = True
        self.pixmap = self.drawResultBox()
        self.update()
        self.main_widget.check_controls()

    def loadBoxes(self):
        self.results = []
        self.modified = False

        if self.txt_file == '' or not os.path.exists(self.txt_file):
            return

        lines = []

        with open(self.txt_file, "r") as file:
            lines = file.read().splitlines()
            for l in lines:
                vls = l.split()
                if len(vls) == 5:
                    idx = int(vls[0])
                    cx = float(vls[1])
                    cy = float(vls[2])
                    w = float(vls[3])
                    h = float(vls[4])

                    vls = [int((cx-w/2)*self.W), int((cy-h/2)*self.H), int((cx+w/2)*self.W), int((cy+h/2)*self.H), idx]
                    self.results.append(vls)

    def saveModifiedBoxes(self):
        if self.txt_file == '' or not self.modified:
            return

        with open(self.txt_file, 'w') as file:
            for elements in self.results:
                lx, ly, rx, ry, idx = elements
                cx = (lx + rx) / 2 / self.W
                cy = (ly + ry) / 2 / self.H
                s = f"{idx} {cx} {cy} {(rx - lx) / self.W} {(ry - ly) / self.H}\n"
                file.write(s)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())