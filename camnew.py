import cv2
from picamera2 import Picamera2
from ultralytics import YOLO
import cvzone
import os
import time
import RPi.GPIO as gp
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QFont
from PyQt5.QtCore import QThread, pyqtSignal

# Ensure Qt plugin path is set
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = '/usr/local/lib/python3.11/dist-packages/cv2/qt/plugins/platforms'

# Configuration
width = 640
height = 480

adapter_info = {
    "A": {
        "i2c_cmd": "i2cset -y 10 0x70 0x00 0x04",
        "gpio_sta": [0, 0, 1],
    },
    "B": {
        "i2c_cmd": "i2cset -y 10 0x70 0x00 0x05",
        "gpio_sta": [1, 0, 1],
    },
    "C": {
        "i2c_cmd": "i2cset -y 10 0x70 0x00 0x06",
        "gpio_sta": [0, 1, 0],
    },
    "D": {
        "i2c_cmd": "i2cset -y 10 0x70 0x00 0x07",
        "gpio_sta": [1, 1, 0],
    }
}

class WorkThread(QThread):
    update_image_signal = pyqtSignal(QPixmap, str)

    def __init__(self):
        super(WorkThread, self).__init__()
        gp.setwarnings(False)
        gp.setmode(gp.BOARD)
        gp.setup(7, gp.OUT)
        gp.setup(11, gp.OUT)
        gp.setup(12, gp.OUT)
        self.models = {item: YOLO('yolov8n.pt') for item in ["A", "B", "C", "D"]}
        self.class_list = self.load_class_list("coco.txt")

    def load_class_list(self, filepath):
        with open(filepath, "r", encoding="utf-8") as file:
            return file.read().split("\n")

    def select_channel(self, index):
        channel_info = adapter_info.get(index)
        if channel_info:
            gpio_sta = channel_info["gpio_sta"]
            gp.output(7, gpio_sta[0])
            gp.output(11, gpio_sta[1])
            gp.output(12, gpio_sta[2])

    def init_i2c(self, index):
        channel_info = adapter_info.get(index)
        if channel_info:
            os.system(str(channel_info["i2c_cmd"]))

    def draw_text_on_image(self, image, text):
        painter = QPainter(image)
        painter.setPen(QColor(255, 0, 0))  # Text color red
        painter.setFont(QFont('Arial', 20))  # Font Arial size 20
        painter.drawText(10, 30, text)  # Text at position (10, 30)
        painter.end()

    def draw_boxes(self, image, boxes, class_list):
        for box in boxes:
            x1, y1, x2, y2, conf, cls_id = map(int, box)
            class_name = class_list[cls_id]
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cvzone.putTextRect(image, f'{class_name}', (x1, y1), 1, 1)

    def run(self):
        picam2 = None

        for item in {"A", "B", "C", "D"}:
            try:
                self.select_channel(item)
                self.init_i2c(item)
                time.sleep(0.5)
                if picam2:
                    picam2.close()
                print("init1 " + item)
                picam2 = Picamera2()
                picam2.configure(picam2.create_still_configuration(main={"size": (width, height), "format": "BGR888"}, buffer_count=2))
                picam2.start()
                time.sleep(2)
                picam2.capture_array(wait=False)
                time.sleep(0.1)
            except Exception as e:
                print("except: " + str(e))

        while True:
            for item in {"A", "B", "C", "D"}:
                self.select_channel(item)
                time.sleep(0.02)
                try:
                    buf = picam2.capture_array()
                    frame = cv2.cvtColor(buf, cv2.COLOR_BGR2RGB)
                    results = self.models[item].predict(frame)
                    boxes = results[0].boxes.data.tolist()

                    self.draw_boxes(frame, boxes, self.class_list)

                    qimage = QImage(frame, width, height, QImage.Format_RGB888)
                    pixmap = QPixmap(qimage)

                    self.update_image_signal.emit(pixmap, item)
                except Exception as e:
                    print("capture_buffer: " + str(e))

app = QApplication([])
window = QWidget()
layout_h = QHBoxLayout()
layout_h2 = QHBoxLayout()
layout_v = QVBoxLayout()
image_label = QLabel()
image_label2 = QLabel()
image_label3 = QLabel()
image_label4 = QLabel()

def update_image(pixmap, camera_id):
    if camera_id == 'A':
        image_label.setPixmap(pixmap)
    elif camera_id == 'B':
        image_label2.setPixmap(pixmap)
    elif camera_id == 'C':
        image_label3.setPixmap(pixmap)
    elif camera_id == 'D':
        image_label4.setPixmap(pixmap)

work = WorkThread()
work.update_image_signal.connect(update_image)

if __name__ == "__main__":
    image_label.setFixedSize(640, 480)
    image_label2.setFixedSize(640, 480)
    image_label3.setFixedSize(640, 480)
    image_label4.setFixedSize(640, 480)
    window.setWindowTitle("Qt Picamera2 Arducam Multi Camera Demo")

    window.resize(1300, 1000)

    layout_h.addWidget(image_label)
    layout_h.addWidget(image_label2)
    layout_h2.addWidget(image_label3)
    layout_h2.addWidget(image_label4)
    layout_v.addLayout(layout_h)
    layout_v.addLayout(layout_h2)
    window.setLayout(layout_v)

    work.start()

    window.show()
    app.exec()
    work.quit()
    if picam2:
        picam2.close()
