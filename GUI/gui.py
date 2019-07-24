import sys
from requests import get
import socket
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from core import core, transmission
import threading
import json
from storage import config


class ModeDialog(QDialog):

	def __init__(self, parent=None):
		super(ModeDialog, self).__init__(parent)
		self.master = True
		self.setup_buttons()
		self.relocate()

	def setup_buttons(self):
		self.setWindowTitle('Select Mode')

		input_label = QLabel('Connect to IP:', )
		input_label.setStyleSheet("font: 10pt")

		self.input_line = QLineEdit()

		button_send = QPushButton('Send to..', self)
		button_receive = QPushButton('Receive from..', self)

		button_send.clicked.connect(self.clicked_send)
		button_receive.clicked.connect(self.clicked_receive)

		button_layout = QHBoxLayout()
		button_layout.addWidget(button_send)
		button_layout.addWidget(button_receive)

		main_layout = QVBoxLayout()
		main_layout.addWidget(input_label)
		main_layout.addWidget(self.input_line)
		main_layout.addLayout(button_layout)
		self.setLayout(main_layout)

	def relocate(self):
		screen = QDesktopWidget()
		self.resize(screen.width() * 0.1, screen.height() * 0.1)

	def get_text(self):
		return self.input_line.text()

	def is_master(self):
		return self.master

	def clicked_send(self):
		ip = self.get_text()
		if not ip:
			return
		else:
			self.close()

	def clicked_receive(self):
		ip = self.get_text()
		if not ip:
			return
		else:
			self.master = False
			self.close()


class GUI(QMainWindow):

	def __init__(self):
		super(GUI, self).__init__(parent=None)
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
		self.transmission = transmission.Transmission()
		self.ipc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.previous_block = None
		self.mutex = threading.Lock()
		self.mutex.acquire()
		self.init_ui()

	def init_ui(self):


		screen = QDesktopWidget()
		self.setGeometry(0, 0, screen.width()/2, screen.height()/2)
		self.setMinimumSize(screen.width()/3, screen.height()/3)
		self.setWindowTitle('CryptoContracts')
		self.setWindowIcon(QIcon('GUI/blockchain.png'))

		self.start_ipc()

		exit_action = QAction(QIcon('exit.png'), '&Exit', self)
		exit_action.setShortcut('Ctrl+Q')
		exit_action.triggered.connect(self.close_window)

		select_button = QPushButton('Select PDF...', self)
		select_button.clicked.connect(self.clicked_select_file)

		pubkey_button = QPushButton('Public Key...', self)
		pubkey_button.clicked.connect(self.clicked_pubkey)

		privkey_button = QPushButton('Private Key...', self)
		privkey_button.clicked.connect(self.clicked_privkey)

		connect_button = QPushButton('Connect peer...', self)
		connect_button.clicked.connect(self.connect)

		add_to_layer_button = QPushButton('Add to chain...', self)
		add_to_layer_button.clicked.connect(self.clicked_add_to_layer)

		ip_label = QLineEdit()
		ip_label.setText("My IP:" + GUI.get_ip("public"))
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

		button_layout = QVBoxLayout()
		button_layout.addWidget(select_button)
		button_layout.addWidget(pubkey_button)
		button_layout.addWidget(privkey_button)
		button_layout.addWidget(connect_button)

		label_layout = QVBoxLayout()
		label_layout.setSpacing(6)

		label_layout.addWidget(self.file_label)
		label_layout.addWidget(self.sign1_label)
		label_layout.addWidget(self.sign2_label)
		label_layout.addWidget(self.conn_label)

		upper_menu_layout = QHBoxLayout()
		upper_menu_layout.addLayout(button_layout)
		upper_menu_layout.addLayout(label_layout)

		lower_menu_layout = QVBoxLayout()
		lower_menu_layout.addWidget(ip_label)
		lower_menu_layout.addWidget(add_to_layer_button)
		lower_menu_layout.addWidget(self.progress)

		main_vbox_layout = QVBoxLayout()
		main_vbox_layout.addStretch(1)
		main_vbox_layout.addLayout(upper_menu_layout)
		main_vbox_layout.addSpacing(5)
		main_vbox_layout.addLayout(lower_menu_layout)
		main_vbox_layout.addStretch(10)

		spacer = QSpacerItem(screen.width() / 5, screen.height() / 5, QSizePolicy.Expanding)
		main_hbox_layout = QHBoxLayout()
		main_hbox_layout.addSpacerItem(spacer)
		main_hbox_layout.addLayout(main_vbox_layout)
		main_hbox_layout.addSpacerItem(spacer)

		widget.setLayout(main_hbox_layout)
		self.setCentralWidget(widget)

		self.show()

	def close_window(self):
		self.ipc_socket.shutdown(socket.SHUT_RDWR)
		self.ipc_socket.close()
		qApp.quit()

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

		if file != "":
			self.doc_hash = core.checksum(path=file)
			print(self.doc_hash)
		self.update_progress_bar(self.file_label, file)

	def clicked_pubkey(self):
		file = QFileDialog.getOpenFileName(filter='*.pub')[0]

		if file != "":
			try:
				self.pubkey = GUI.get_pubkey(file)
			except ValueError as err:
				print("unexpected public key", err)
				return
			print(self.pubkey)
		self.update_progress_bar(self.sign1_label, file)

	def clicked_privkey(self):
		file = QFileDialog.getOpenFileName(filter='*')[0]

		# checksum calling crashes program
		if file != "":
			try:
				self.privkey = GUI.get_privkey(file)
			except ValueError as err:
				print("unexpected private key", err)
				return
			print(self.privkey)
		self.update_progress_bar(self.sign2_label, file)

	def connect(self):
		# establish connection with other client
		mode = ModeDialog()
		mode.exec_()
		master = mode.is_master()
		ip = mode.get_text()
		if self.inputs_valid() and GUI.validate_ip(ip):
			if master:
				print("master send", ip)
				self.master_send(master, ip)
			else:
				print("slave receive", ip)
				self.slave_receive(ip)

		mode.close()

	def master_send(self, master, ip):
		#ip, ok = QInputDialog.getText(self, 'Select mode', 'Enter ip address of other client:')
		own_ip = GUI.get_ip("public")

		if GUI.validate_ip(ip):
			# connect to partner client
			if not ip == own_ip:
				print("stage 1:")
				transmission = core.produce_transmission_stage_one(self.privkey, self.pubkey, self.doc_hash)
				trans_json = transmission.to_json()
				print(type(trans_json))
				if GUI.send_to_partner(ip, trans_json):
					try:
						received_trans = GUI.receive_from_partner(own_ip)
					except ValueError as err:
						print("Connection failed:", err)
						return
					print("stage 2:")
					#############
					self.ipc_send(1)
					if not self.mutex.locked():
						print("locked after get head signaling, continuing..")
						previous_hash = self.previous_block.transmission_hash
						transmission = core.produce_transmission_stage_two(self.privkey, previous_hash,
																		   transmission.from_json(received_trans), True)
						trans_json = transmission.to_json()
						GUI.send_to_partner(trans_json)
						try:
							received_trans = GUI.receive_from_partner(GUI.get_ip("public"))
						except ValueError as err:
							print("Connection failed:", err)
							return
						self.transmission = transmission.from_json(received_trans)
						####################################################################################################
						self.update_progress_bar(self.conn_label, ip)
				else:
					return
			else:
				print("That's your own IP dude...")
				return
		else:
			ip = ""
			self.update_progress_bar(self.conn_label, ip)

	def slave_receive(self, ip):
		print("stage 1:")
		own_ip = GUI.get_ip("public")
		received_json = GUI.receive_from_partner(own_ip)
		print(received_json)
		received_trans = core.Transmission.from_json(received_json)
		transmission = core.produce_transmission_stage_one(self.privkey, self.pubkey, transmission=received_trans)
		trans_json = transmission.to_json()
		GUI.send_to_partner(ip, trans_json)

		print("stage 2:")
		received_json = GUI.receive_from_partner(own_ip)
		print(received_json)
		received_trans = core.Transmission.from_json(received_json)
		transmission = core.produce_transmission_stage_two(self.privkey, transmission=received_trans, master=False)
		trans_json = transmission.to_json(transmission)
		GUI.send_to_partner(ip, trans_json)
		self.update_progress_bar(self.conn_label, ip)

	def clicked_add_to_layer(self):
	# put block into db if valid
		if self.transmission.check_self() and self.transmission.is_valid():
			self.ipc_send(0)

	def inputs_valid(self):
		if self.file_label != self.DEFAULT_STRING and self.sign1_label != self.DEFAULT_STRING and self.sign2_label != self.DEFAULT_STRING:
			####test if keys are matching and for valid doc_hash####
			return True
		else:
			return False

	@staticmethod
	def get_privkey(path):
		file = open(path, "r")
		write_flag = False
		privkey = ""
		for line in file:
			if "PRIVATE" in line and not write_flag:
				write_flag = True
				continue
			elif "PRIVATE" in line and write_flag:
				write_flag = False
			if write_flag:
				privkey += line
		if not privkey:
			raise ValueError
		return privkey

	@staticmethod
	def get_pubkey(path):
		file = open(path, "r")
		write_flag = False
		pubkey = ""
		for line in file:
			if not write_flag:
				if "Comment" in line:
					write_flag = True
					continue
				elif "ssh-rsa" in line:
					write_flag = True
			elif "END" in line:
				write_flag = False
			if write_flag:
				pubkey += line
		if write_flag:
			pubkey = pubkey.split(" ")[1]
		if not pubkey:
			raise ValueError
		return pubkey

	"""relocate functions to network module"""
	@staticmethod
	def get_ip(mode):
		if mode == "public":
			return get('https://api.ipify.org').text
		elif mode == "local":
			return socket.gethostbyname(socket.gethostname())
		else:
			return None

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
	def send_to_partner(ip, data):
		PORT = 10150
		byte = bytes(data, "utf-8")
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		print("connecting to partner with ip:", ip)
		try:
			s.connect((ip, PORT))
		except OSError as err:
			print("Could not connect:", err)
			return s.close()
		print("sending message", data)
		s.send(byte)
		s.close()
		return True

	@staticmethod
	def receive_from_partner(ip):
		PORT = 10150
		BUFFER_SIZE = 2048
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.bind(("0.0.0.0", PORT))
		s.listen(1)
		data_str = ""

		conn, addr = s.accept()
		print('Connection address:', addr)
		while 1:
			data = conn.recv(BUFFER_SIZE)
			if not data:
				break
			print("received data:", data.decode("utf-8"))
			data_str = data.decode("utf-8")
		conn.close()
		if not data_str:
			raise ValueError
		return data_str

	def start_ipc(self):
		self.ipc_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.ipc_socket.bind((config.get("gui", "addr"), 9005))
		try:
			self.ipc_socket.connect((config.get("gui", "addr"), int(config.get("gui", "port"))))
		except OSError as err:
			print("error:", err)
			return
		thread = threading.Thread(target=self.ipc_receive)
		thread.daemon = True
		thread.start()

	def ipc_send(self, mode):
		# 1 for get head 0 for attach block
		if mode:
			self.ipc_socket.send(b'\x11')
			self.mutex.acquire()
		else:
			self.ipc_socket.send(b'\x12' + bytes(self.transmission.to_json(), "utf-8"))

	def ipc_receive(self):

		while True:
			data = self.ipc_socket.recv(4096)

			data = str(data, "utf-8")
			print("data: ", data)
			mode = int(bytes(data, "utf-8").hex()[0:2])
			print("mode: ", mode)

			if len(data) > 1:
				content = data[1:]
				print("content: ", content)

			if mode == 21:
				self.previous_block = json.loads(content)
				print("Head of Chain: ", self.previous_block)
				self.mutex.release()

			if mode == 22:  # Ack from Peer
				print("Document successfully placed in Chain")



stylesheet = """GUI {
    border-image: url("GUI/blockchain.png"); 
    background-repeat: no-repeat; 
    background-position: center;}"""

def start():
	#if __name__ == '__main__':
		app = QApplication(sys.argv)
		app.setStyleSheet(stylesheet)
		ex = GUI()
		sys.exit(app.exec_())

