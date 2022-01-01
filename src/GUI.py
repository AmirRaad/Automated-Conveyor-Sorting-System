import sys
from time import sleep

import cv2
import utils
import numpy as np
import requests
import serial
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QSizePolicy, QFormLayout, \
    QHBoxLayout, QRadioButton, QDial, QMessageBox
from QLed import QLed


class Gui(QWidget):
    def __init__(self, parent=None):
        super(Gui, self).__init__(parent)
        self.setWindowTitle("Pepsi conveyor")
        main_layout = QHBoxLayout()
        self.connect = False
        self.result = None
        try:
            self.ser = serial.Serial("COM3", 9600)
            self.connect = True
        except serial.SerialException:
            print("There is no Arduino connected!")
        sleep(2)

        # Control Frame =====================================================================================
        layout1 = QFormLayout()
        counters = QHBoxLayout()
        self.cnt1 = 0
        self.cnt2 = 0
        self.counter1 = QLabel("Accepted: 0")
        self.counter2 = QLabel("Rejected: 0")

        self.lbl = QLabel("Manual Mode:")
        self.angle = QLabel("Angle: 90")
        self.speed = QLabel("Speed: 90")

        for label in self.counter1, self.counter2, self.lbl, self.angle, self.speed:
            label.setStyleSheet(
                # setting variable margins
                "*{margin-left: " + str(5) + "px;" +
                "margin-right: " + str(5) + "px;" +
                '''
                color: white;
                font-family: 'abeatbyKai';
                font-size: 25px;
                font-weight: bold;
                padding: 5px 0;
                margin-top: 10px;
                margin-bottom: 20px;
                }
                '''
            )
        counters.addWidget(self.counter1)
        counters.addWidget(self.counter2)

        leds = QHBoxLayout()
        self.led1 = QLed(self, onColour=QLed.Green, shape=QLed.Circle)
        self.led1.value = False
        self.led2 = QLed(self, onColour=QLed.Red, shape=QLed.Circle)
        self.led2.value = False
        leds.addWidget(self.led1)
        leds.addWidget(self.led2)

        rbs = QHBoxLayout()
        self.rb1 = QRadioButton("Auto")
        self.rb2 = QRadioButton("Manual")
        self.rb1.setChecked(True)
        for rb in self.rb1, self.rb2:
            rb.setStyleSheet(
                # setting variable margins
                "*{margin-left: " + str(5) + "px;" +
                "margin-right: " + str(5) + "px;" +
                '''
                color: white;
                font-family: 'abeatbyKai';
                font-size: 20px;
                font-weight: bold;
                padding: 5px 0;
                margin-top: 50px;
                margin-left: 50px;
                }
                '''
            )
        rbs.addWidget(self.rb1)
        rbs.addWidget(self.rb2)

        begin_button = QPushButton("Begin")
        begin_button.clicked.connect(self.begin)
        begin_button = self.style_button(begin_button, 50, 50, 5, 5)

        self.dial = QDial(self)
        self.dial.setRange(65, 120)
        self.dial.setStyleSheet("background-color: white;")
        self.dial.setValue(90)

        self.dial1 = QDial(self)
        self.dial1.setRange(80, 120)
        self.dial1.setStyleSheet("background-color: white;")
        self.dial1.setValue(90)

        info_label = QLabel("About us:")
        info_label.setStyleSheet(
            # setting variable margins
            "*{margin-left: 100px;" +
            "margin-right: 5px;" +
            '''
            color: white;
            font-family: 'abeatbyKai';
            font-size: 20px;
            font-weight: bold;
            padding: 5px 0;
            margin-top: 10px;
            margin-bottom: 10px;
            }
            ''')
        info_button = QPushButton("i")
        info_button.clicked.connect(self.info)
        info_button.setFixedSize(50, 50)
        info_button.setStyleSheet("*{border: 2px solid '#FFFFFF';"
                                  "border-radius: 25px;"
                                  "color: white;"
                                  "font-family: 'cocon';"
                                  "font-size: 30px;"
                                  "}"
                                  "*:hover{"
                                  "background: '#FFFFFF';"
                                  "color: #005794;"
                                  "}")

        layout1.addRow(counters)
        layout1.addRow(leds)
        layout1.addRow(rbs)
        layout1.addRow(begin_button)
        layout1.addRow(self.lbl)
        layout1.addRow(self.dial, self.angle)
        layout1.addRow(self.dial1, self.speed)
        layout1.addRow(info_label, info_button)
        # ===================================================================================================

        # Video Frame =======================================================================================
        self.timer = QTimer()
        self.cap = cv2.VideoCapture(0)
        self.camMode = False
        self.url = "http://192.168.43.72:9000/shot.jpg"
        layout = QFormLayout()

        self.lblVid = QLabel()
        self.lblVid.setGeometry(QRect(4, 5, 790, 560))
        self.lblVid.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.lblVid.setAlignment(Qt.AlignCenter)
        self.lblVid.setStyleSheet("""
        background-color: black;
        border-radius: 20%;
        """)

        start_button = QPushButton("Start Feed")
        start_button.clicked.connect(self.start)
        stop_button = QPushButton("Stop Feed")
        stop_button.clicked.connect(self.stop)

        start_button = self.style_button(start_button, 20, 5, 5, 5)
        stop_button = self.style_button(stop_button, 5, 20, 5, 5)

        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(start_button)
        buttonLayout.addWidget(stop_button)

        layout.addRow(self.lblVid)
        layout.addRow(buttonLayout)
        # ===================================================================================================

        main_layout.addLayout(layout)
        main_layout.addLayout(layout1)
        self.setLayout(main_layout)
        self.startVideo()

    def startVideo(self):
        fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        millisecs = int(1000.0 / fps)
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.nextFrameSlot)
        self.timer.start(millisecs)

    def nextFrameSlot(self):
        self.angle.setText("Angle: " + str(self.dial.value()))
        self.speed.setText("Speed: " + str(self.dial1.value()))
        self.check()

        if self.camMode:
            RawData = requests.get(self.url, verify=False)
            # Converting it to serialized one dimension array
            One_D_Arry = np.array(bytearray(RawData.content), dtype=np.uint8)
            # converting One dimension Array into opencv image matrix, format using "imdecode" function
            frame = cv2.imdecode(One_D_Arry, -1)

            # ret, frame = self.cap.read()
            # frame = cv2.flip(frame, 1)
            output = frame.copy()

            if self.connect and self.ser.in_waiting:
                data = self.ser.read()  # read a byte string
                string_n = data.decode()  # decode byte string into Unicode

                if string_n == '1':
                    self.led2.value = True
                    self.led1.value = False
                    self.cnt2 += 1
                    self.counter2.setText("Rejected: " + str(self.cnt2))
                    self.result = None

                if string_n == '2':
                    print('Checking can quality...')

                    status = None
                    circle = utils.detect_circles(frame, output)
                    if circle is not None:
                        # mask, contour, status = utils.detect_hole(img, lower, upper, circle, output)
                        hole, status = utils.detect_hole_v2(frame, circle, output)

                        self.result = output
                        self.result = cv2.resize(self.result, (108, 150))
                        self.result = cv2.copyMakeBorder(self.result, 5, 5, 5, 5, cv2.BORDER_CONSTANT,
                                                         value=(255, 255, 255))
                        # print(status)

                        if status == "Accepted":
                            self.led1.value = True
                            self.led2.value = False
                            self.cnt1 += 1
                            self.counter1.setText("Accepted: " + str(self.cnt1))
                            self.ser.write(b'A')
                        else:
                            self.led2.value = True
                            self.led1.value = False
                            self.cnt2 += 1
                            self.counter2.setText("Rejected: " + str(self.cnt2))
                            self.ser.write(b'R')

                    if status is None:
                        self.led1.value = False
                        self.led2.value = False

            if self.result is not None:
                height, width, channels = self.result.shape
                offset = np.array((0, 0))
                output[offset[0]:offset[0] + height, offset[1]:offset[1] + width] = self.result

            # ret, frame = self.cap.read()
            # frame = cv2.flip(frame, 1)
            frame = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
            img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            pix = QPixmap.fromImage(img)
            pix = pix.scaled(self.lblVid.width(), self.lblVid.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.lblVid.setPixmap(pix)

        else:
            sleep(0.05)

    def begin(self):
        print("begin")
        self.led1.value = False
        self.led2.value = False
        if self.connect:
            self.ser.write(b'S')

    def start(self):
        self.camMode = True
        self.cap = cv2.VideoCapture(0)

    def stop(self):
        self.cap.release()
        self.camMode = False
        self.lblVid.clear()

        self.dial1.setValue(90)
        self.dial.setValue(90)

        self.led1.value = False
        self.led2.value = False

    def check(self):
        if self.rb2.isChecked():
            print("manual")
            mes1 = 'a' + str(self.dial.value()) + '*'
            mes2 = 's' + str(self.dial1.value()) + '$'
            mes1 += mes2
            print(mes1)
            if self.connect:
                self.ser.write(bytearray(mes1, 'ascii'))

    def info(self):
        msg = QMessageBox()
        msg.setText("A project prepared for the Peripheral Units Lab, Damascus University.\n"
                    "Project Team:\n\nAmir Raad\nMhd Qusai Al-Hakeam\nRiham Allababidi\nSouad Roumani\n\n"
                    "Copyright all rights reserved December 2021 ©")
        msg.setWindowTitle("Project Team")
        msg.setWindowIcon(QIcon("Pepsi-Logo.png"))
        msg.setIcon(QMessageBox.Information)
        msg.setStyleSheet("background: #FFFFFF;")
        msg.exec_()

    def style_button(self, btn, l_margin, r_margin, t_margin, b_margin):
        btn.setStyleSheet(
            # setting variable margins
            "*{margin-left: " + str(l_margin) + "px;" +
            "margin-right: " + str(r_margin) + "px;" +
            '''
            border: 2px solid '#FFFFFF';
            color: white;
            font-family: 'abeatbyKai';
            font-size: 20px;
            font-weight: bold;
            border-radius: 25px;
            padding: 15px 0;
            '''
            "margin-top:" + str(t_margin) + "px;"
                                            "margin-bottom:" + str(b_margin) + "px;"
                                                                               '''
              }
              *:hover{
              background: '#FFFFFF';
              color: #005794;
              }
            '''
        )
        return btn


def main():
    app = QApplication(sys.argv)
    ex = Gui()
    ex.setWindowIcon(QIcon('Pepsi-Logo.png'))
    ex.setStyleSheet("background: #005794;")
    ex.setGeometry(100, 50, 1000, 640)
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
