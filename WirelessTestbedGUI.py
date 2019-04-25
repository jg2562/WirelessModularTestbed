import sys
from PyQt4 import QtGui, QtCore

class Window(QtGui.QMainWindow):

    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(50, 50, 500, 300)
        self.setWindowTitle("Wireless Modular Testbed GUI")
        self.home()

    def home(self):
        btn = QtGui.QPushButton("Submit", self)
        btn.clicked.connect(self.send_application)
        btn.resize(btn.minimumSizeHint())
        btn.move(400,250)
        self.show()
        btn = QtGui.QPushButton("Quit", self)
        btn.clicked.connect(self.close_application)
        btn.resize(btn.minimumSizeHint())
        btn.move(450,250)
        self.show()

        openFile = QtGui.QAction("&Open File", self)
        openFile.setShortcut("Ctrl+O")
        openFile.setStatusTip('Open File')
        openFile.triggered.connect(self.file_open)

        comboBox = QtGui.QComboBox(self)
        comboBox.addItem("FM")
        comboBox.addItem("Wi-Fi AP")
        comboBox.addItem("Wi-Fi Mesh")
        comboBox.addItem("Bluetooth")
        comboBox.addItem("Zigbee")
        comboBox.addItem("LoRa")
        comboBox.move(50, 150)


    def close_application(self):
        print("Closing")
        sys.exit()

    def send_application(self):
        print("Sending")
        # QProcess::execute(file); #file needs to change to raspberry pi and antenna application
     #send code to antenna option

    def file_open(self):
        name = QtGui.QFileDialog.getOpenFileName(self, 'Open File')
        qp = QtGui.QPixmap(name)


def run():
    app = QtGui.QApplication(sys.argv)
    GUI = Window()
    sys.exit(app.exec_())


run()
