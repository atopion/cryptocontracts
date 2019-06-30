import sys
import time
import os
from PyQt5.QtWidgets import (QMainWindow, QAction, qApp, QApplication, QPushButton, QProgressBar, QInputDialog,
                             QLineEdit, QFileDialog as Dialog)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QUrl
#from core import core


class GUI(QMainWindow):

    def __init__(self):
        super().__init__()
        self.progress = QProgressBar(self)
        self.file_label = QLineEdit(self)
        self.sign1_label = QLineEdit(self)
        self.sign2_label = QLineEdit(self)
        self.conn_label = QLineEdit(self)
        self.PROGRESS_MAX = 100
        self.DEFAULT_STRING = "No Data"
        self.statusBar()

        self.init_ui()

    def init_ui(self):

        self.setGeometry(300, 300, 900, 640)
        self.setMinimumSize(900, 640)
        self.setWindowTitle('CryptoContracts')

        exit_action = QAction(QIcon('exit.png'), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        # exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(qApp.quit)

        select_button = QPushButton('Select PDF...', self)
        select_button.move(310, 30)
        select_button.clicked.connect(self.clicked_select_file)

        sign1_button = QPushButton('Signature1...', self)
        sign1_button.move(310, 70)
        sign1_button.clicked.connect(self.clicked_signature1)

        sign2_button = QPushButton('Signature2...', self)
        sign2_button.move(310, 110)
        sign2_button.clicked.connect(self.clicked_signature2)

        connect_button = QPushButton('Connect...', self)
        connect_button.move(310, 150)
        connect_button.clicked.connect(self.clicked_connect)

        add_to_layer_button = QPushButton('Add to chain...', self)
        add_to_layer_button.move(405, 240)
        add_to_layer_button.clicked.connect(self.clicked_add_to_layer)

        self.file_label.move(420, 33)
        self.file_label.resize(180, 25)
        self.file_label.setText(self.DEFAULT_STRING)

        self.sign1_label.move(420, 73)
        self.sign1_label.resize(180, 25)
        self.sign1_label.setText(self.DEFAULT_STRING)

        self.sign2_label.move(420, 113)
        self.sign2_label.resize(180, 25)
        self.sign2_label.setText(self.DEFAULT_STRING)

        self.conn_label.move(420, 153)
        self.conn_label.resize(180, 25)
        self.conn_label.setText(self.DEFAULT_STRING)

        self.progress.setGeometry(310, 200, 325, 25)
        self.progress.setMaximum(self.PROGRESS_MAX)

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(exit_action)

        self.show()

    def clicked_select_file(self):
        file = Dialog.getOpenFileName(filter='*.pdf')[0]
        if self.file_label.text() == self.DEFAULT_STRING and file != "":
            if not self.file_label.text() == file:
                self.progress.setValue(self.progress.value() + self.PROGRESS_MAX / 5)
        self.file_label.setText(file)
        # checksum calling crashes program
        # return file_hash = core.checksum()
        print(file)

    def clicked_signature1(self):
        sig = Dialog.getOpenFileName(filter='*.pdf')[0]
        if self.sign1_label.text() == self.DEFAULT_STRING and sig != "":
            if not self.sign1_label.text() == sig:
                self.progress.setValue(self.progress.value() + self.PROGRESS_MAX / 5)
        self.sign1_label.setText(sig)

        # url = QUrl.fromLocalFile(sig)
        # print(os.path.splitext(url.fileName())[0])
        # checksum calling crashes program
        # sig_hash = core.checksum(url.fileName())
        print(sig)

    def clicked_signature2(self):
        sig = Dialog.getOpenFileName(filter='*.pdf')[0]
        if self.sign2_label.text() == self.DEFAULT_STRING and sig != "":
            if not self.sign2_label.text() == sig:
                self.progress.setValue(self.progress.value() + self.PROGRESS_MAX / 5)
        self.sign2_label.setText(sig)
        # checksum calling crashes program
        # sig_hash = core.checksum(sig)
        print(sig)

    def clicked_connect(self):
        # establish connection with other client
        ip, ok = QInputDialog.getText(self, 'Input Dialog', 'Enter ip address of other client:')
        if ok and self.validate_ip(ip):
            if self.conn_label.text() == self.DEFAULT_STRING:
                if not self.conn_label.text() == ip:
                    self.progress.setValue(self.progress.value() + self.PROGRESS_MAX / 5)
            self.conn_label.setText(ip)
        else:
            print("IP wrong")
        print(ip)

    def validate_ip(self, s):
        a = s.split('.')
        if len(a) != 4:
            return False
        for x in a:
            if not x.isdigit():
                return False
            i = int(x)
            if i < 0 or i > 255:
                return False
        return True

    def clicked_add_to_layer(self):
        # broadcast transmission to all peers
        print("Nothing yet")

    # def update_progress(self, s):
    #    if s == self.DEFAULT_STRING:
    #        if not s == sig:
    #            self.progress.setValue(self.progress.value() + self.PROGRESS_MAX / 5)


stylesheet = """
    GUI {
    border-image: url("blockchain.png"); 
    background-repeat: no-repeat; 
    background-position: center;}"""


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(stylesheet)
    ex = GUI()
    sys.exit(app.exec_())
