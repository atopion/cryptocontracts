import sys
from requests import get
import socket
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from core import core


class GUI(QMainWindow):

    def __init__(self, width, height):
        super().__init__()
        self.PROGRESS_MAX = 100
        self.DEFAULT_STRING = "No Data"
        self.progress = QProgressBar(self)
        self.file_label = QLineEdit(self)
        self.sign1_label = QLineEdit(self)
        self.sign2_label = QLineEdit(self)
        self.conn_label = QLineEdit(self)
        self.check_file = QCheckBox()
        self.check_pubkey = QCheckBox()
        self.check_privkey = QCheckBox()
        self.check_conn = QCheckBox()
        self.statusBar()
        self.width = width
        self.height = height
        self.init_ui()

    def init_ui(self):

        self.setGeometry(0, 0, self.width/2, self.height/2)
        self.setMinimumSize(self.width/3, self.height/3)
        self.setWindowTitle('CryptoContracts')
        self.setWindowIcon(QIcon('GUI/blockchain.png'))

        exit_action = QAction(QIcon('exit.png'), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(qApp.quit)

        select_button = QPushButton('Select PDF...', self)
        select_button.clicked.connect(self.clicked_select_file)

        pubkey_button = QPushButton('Public Key...', self)
        pubkey_button.clicked.connect(self.clicked_pubkey)

        privkey_button = QPushButton('Private Key...', self)
        privkey_button.clicked.connect(self.clicked_privkey)

        connect_button = QPushButton('Connect peer...', self)
        connect_button.clicked.connect(self.clicked_connect)

        add_to_layer_button = QPushButton('Add to chain...', self)
        add_to_layer_button.clicked.connect(self.clicked_add_to_layer)

        ip_label = QLineEdit()
        ip_label.setText(GUI.get_ip())
        ip_label.setReadOnly(True)

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
        vbox1.addWidget(pubkey_button)
        vbox1.addWidget(privkey_button)
        vbox1.addWidget(connect_button)

        vbox2 = QVBoxLayout()
        vbox2.setSpacing(6)
        vbox2.addWidget(self.file_label)
        vbox2.addWidget(self.sign1_label)
        vbox2.addWidget(self.sign2_label)
        vbox2.addWidget(self.conn_label)

        vbox_checks = QVBoxLayout()
        vbox_checks.addWidget(self.check_file)
        vbox_checks.addWidget(self.check_pubkey)
        vbox_checks.addWidget(self.check_privkey)
        vbox_checks.addWidget(self.check_conn)

        hbox = QHBoxLayout()
        hbox.addLayout(vbox1)
        hbox.addLayout(vbox2)
        hbox.addLayout(vbox_checks)

        vbox3 = QVBoxLayout()
        vbox3.addWidget(ip_label)
        vbox3.addWidget(add_to_layer_button)
        vbox3.addWidget(self.progress)

        vbox4 = QVBoxLayout()
        vbox4.addStretch(1)
        vbox4.addLayout(hbox)
        vbox4.addSpacing(5)
        vbox4.addLayout(vbox3)
        vbox4.addStretch(10)

        spacer = QSpacerItem(self.width / 5, self.height / 5, QSizePolicy.Expanding)
        hbox2 = QHBoxLayout()
        hbox2.addSpacerItem(spacer)
        hbox2.addLayout(vbox4)
        hbox2.addSpacerItem(spacer)

        widget.setLayout(hbox2)
        self.setCentralWidget(widget)

        self.show()

    def update_progress_bar(self, line_edit, s):
        if not s:
            if not line_edit.text() == self.DEFAULT_STRING:
                line_edit.setText(self.DEFAULT_STRING)
                self.progress.setValue(self.progress.value() - self.PROGRESS_MAX / 5)
            print("Canceled")
            return False
        elif line_edit.text() == self.DEFAULT_STRING:
            if not line_edit.text() == s:
                self.progress.setValue(self.progress.value() + self.PROGRESS_MAX / 5)
            line_edit.setText(s)
            return True
        else:
            line_edit.setText(s)
            return True

    def clicked_select_file(self):
        file = QFileDialog.getOpenFileName(filter='*.pdf')[0]

        # checksum calling crashes program (due to error in blake code)
        if file != "":
            self.doc_hash = core.checksum(path=file)
            print(self.doc_hash)
        self.check_file.setChecked(self.update_progress_bar(self.file_label, file))

    def clicked_pubkey(self):
        file = QFileDialog.getOpenFileName(filter='*.txt')[0]

        # checksum calling crashes program
        if file != "":
            try:
                self.pubkey = GUI.get_pubkey(file)
            except ValueError as err:
                print("unexpected public key", err)
                return
            print(self.pubkey)
        self.check_pubkey.setChecked(self.update_progress_bar(self.sign1_label, file))

    def clicked_privkey(self):
        file = QFileDialog.getOpenFileName(filter='*.ppk')[0]

        # checksum calling crashes program
        if file != "":
            try:
                self.privkey = GUI.get_privkey(file)
            except ValueError as err:
                print("unexpected private key", err)
                return
            print(self.privkey)
        self.check_privkey.setChecked(self.update_progress_bar(self.sign2_label, file))

    def clicked_connect(self):
        # establish connection with other client
        ip, ok = QInputDialog.getText(self, 'Input Dialog', 'Enter ip address of other client:')
        if ok and GUI.validate_ip(ip):
            # connect to partner client
            if not ip == GUI.get_ip():
                #GUI.connect_to_partner(ip)
                #GUI.receive_message(GUI.get_ip())
                self.check_conn.setChecked(self.update_progress_bar(self.conn_label, ip))
                print(ip)
            else:
                print("That's your own IP dude...")
                return
        else:
            ip = ""
            self.check_conn.setChecked(self.update_progress_bar(self.conn_label, ip))

    def clicked_add_to_layer(self):
        # broadcast transmission to all peers if block verified
        if core.compare(self.doc_hash, self.sig_hash):
            print("same")
        print(GUI.get_ip())

    @staticmethod
    def get_privkey(path=None):
        file = open(path, "r")
        write_flag = False
        privkey = ""
        for line in file:
            if "Private" in line and not write_flag:
                write_flag = True
                continue
            elif "Private" in line and write_flag:
                write_flag = False
            if write_flag:
                privkey += line
        if not privkey:
            raise ValueError
        return privkey

    @staticmethod
    def get_pubkey(path=None):
        file = open(path, "r")
        write_flag = False
        pubkey = ""
        for line in file:
            if "Comment" in line and not write_flag:
                write_flag = True
                continue
            elif "----" in line and write_flag:
                write_flag = False
            if write_flag:
                pubkey += line
        if not pubkey:
            raise ValueError
        return pubkey

    """relocate functions to network module"""
    @staticmethod
    def get_ip():
        ip = "My IP: " + get('https://api.ipify.org').text
        return ip

    @staticmethod
    def validate_ip(s):
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

    @staticmethod
    def connect_to_partner(ip):
        PORT = 5005
        MESSAGE = "Hello!"
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("connecting to partner with ip:", ip)
        try:
            s.connect((ip, PORT))
        except:
            print("something went wrong")
        print("sending message", MESSAGE)
        s.send(MESSAGE)
        s.close()


    @staticmethod
    def receive_message(ip):
        PORT = 5005
        BUFFER_SIZE = 1024
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((ip, PORT))
        s.listen(1)

        conn, addr = s.accept()
        print('Connection address:', addr)
        while 1:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
            print("received data:", data)
            conn.send(data)  # echo
        conn.close()


stylesheet = """GUI {
    border-image: url("blockchain.png"); 
    background-repeat: no-repeat; 
    background-position: center;}"""


def start():
#if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(stylesheet)
    screen = app.primaryScreen()
    ex = GUI(screen.size().width(), screen.size().height())
    sys.exit(app.exec_())
