import sys
import time
import os
from PyQt5.QtWidgets import (QMainWindow, QAction, qApp, QApplication, QPushButton, QProgressBar, QInputDialog,
                             QLineEdit, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy, QWidget, QFileDialog as Dialog)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QUrl
from Core import core


class GUI(QMainWindow):

    def __init__(self, width, height):
        super().__init__()
        self.progress = QProgressBar(self)
        self.file_label = QLineEdit(self)
        self.sign1_label = QLineEdit(self)
        self.sign2_label = QLineEdit(self)
        self.conn_label = QLineEdit(self)
        self.PROGRESS_MAX = 100
        self.DEFAULT_STRING = "No Data"
        self.statusBar()
        self.width = width
        self.height = height
        self.init_ui()

    def init_ui(self):

        self.setGeometry(0, 0, self.width/2, self.height/2)
        self.setMinimumSize(self.width/3, self.height/3)
        self.setWindowTitle('CryptoContracts')

        exit_action = QAction(QIcon('exit.png'), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(qApp.quit)

        select_button = QPushButton('Select PDF...', self)
        select_button.clicked.connect(self.clicked_select_file)

        sign1_button = QPushButton('Signature1...', self)
        sign1_button.clicked.connect(self.clicked_signature1)

        sign2_button = QPushButton('Signature2...', self)
        sign2_button.clicked.connect(self.clicked_signature2)

        connect_button = QPushButton('Connect peer...', self)
        connect_button.clicked.connect(self.clicked_connect)

        add_to_layer_button = QPushButton('Add to chain...', self)
        add_to_layer_button.clicked.connect(self.clicked_add_to_layer)

        self.file_label.setText(self.DEFAULT_STRING)
        self.file_label.setReadOnly(True)

        self.sign1_label.setText(self.DEFAULT_STRING)
        self.sign1_label.setReadOnly(True)

        self.sign2_label.setText(self.DEFAULT_STRING)
        self.sign2_label.setReadOnly(True)

        self.conn_label.setText(self.DEFAULT_STRING)
        self.conn_label.setReadOnly(True)

        self.progress.setMaximum(self.PROGRESS_MAX)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(exit_action)

        widget = QWidget()

        vbox1 = QVBoxLayout()
        vbox1.addWidget(select_button)
        vbox1.addWidget(sign1_button)
        vbox1.addWidget(sign2_button)
        vbox1.addWidget(connect_button)

        vbox2 = QVBoxLayout()
        vbox2.addWidget(self.file_label)
        vbox2.addSpacing(3)
        vbox2.addWidget(self.sign1_label)
        vbox2.addSpacing(3)
        vbox2.addWidget(self.sign2_label)
        vbox2.addSpacing(3)
        vbox2.addWidget(self.conn_label)

        hbox = QHBoxLayout()
        hbox.addLayout(vbox1)
        hbox.addLayout(vbox2)

        vbox3 = QVBoxLayout()
        vbox3.addWidget(add_to_layer_button)
        vbox3.addWidget(self.progress)

        vbox4 = QVBoxLayout()
        vbox4.addStretch(1)
        vbox4.addLayout(hbox)
        vbox4.addSpacing(10)
        vbox4.addLayout(vbox3)
        vbox4.addStretch(10)

        spaceItem = QSpacerItem(self.width/5, self.height/5, QSizePolicy.Expanding)
        hbox2 = QHBoxLayout()
        hbox2.addSpacerItem(spaceItem)
        hbox2.addLayout(vbox4)
        hbox2.addSpacerItem(spaceItem)

        widget.setLayout(hbox2)
        self.setCentralWidget(widget)

        self.show()

    def update_progress(self, line_edit, s):
        if not s:
            if not line_edit.text() == self.DEFAULT_STRING:
                line_edit.setText(self.DEFAULT_STRING)
                self.progress.setValue(self.progress.value() - self.PROGRESS_MAX / 5)
            print("Canceled")
        elif line_edit.text() == self.DEFAULT_STRING:
            if not line_edit.text() == s:
                self.progress.setValue(self.progress.value() + self.PROGRESS_MAX / 5)
            line_edit.setText(s)
        else:
            line_edit.setText(s)

    def clicked_select_file(self):
        file = Dialog.getOpenFileName(filter='*.pdf')[0]
        self.update_progress(self.file_label, file)
        # checksum calling crashes program
        # return file_hash = core.checksum()
        print(file)

    def clicked_signature1(self):
        sig = Dialog.getOpenFileName(filter='*.pdf')[0]
        self.update_progress(self.sign1_label, sig)

        url = QUrl.fromLocalFile(sig)
        print(os.path.splitext(url.fileName())[0])
        # checksum calling crashes program
        sig_hash = core.checksum(path=sig)
        print(sig_hash)

    def clicked_signature2(self):
        sig = Dialog.getOpenFileName(filter='*.pdf')[0]
        self.update_progress(self.sign2_label, sig)
        # checksum calling crashes program
        # sig_hash = core.checksum(sig)
        print(sig)

    def clicked_connect(self):
        # establish connection with other client
        ip, ok = QInputDialog.getText(self, 'Input Dialog', 'Enter ip address of other client:')
        if ok and self.validate_ip(ip):
            self.update_progress(self.conn_label, ip)
        else:
            ip = ""
            self.update_progress(self.conn_label, ip)
        print(ip)

    def clicked_add_to_layer(self):
        # broadcast transmission to all peers if block verified
        print("Nothing yet")

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


stylesheet = """
    GUI {
    border-image: url("blockchain.png"); 
    background-repeat: no-repeat; 
    background-position: center;}"""


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(stylesheet)
    screen = app.primaryScreen()
    ex = GUI(screen.size().width(), screen.size().height())
    sys.exit(app.exec_())
