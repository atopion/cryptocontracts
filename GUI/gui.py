import sys
from requests import get
import socket
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from core import core, transmission
import threading
import json
from storage import config
from core import signing


class ModeDialog(QDialog):
	"""
	Class creating the mode dialog when clicking on the connect button in the main window
	"""
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
	"""
	Class for creation of main window for user interface

	Attributes
	----------
	PROGRESS_MAX:
		maximum value of progressbar
	DEFAULT_STRING:
		default string for line edits
	progress:
		progress bar representing progress
	file_label:
		line edit showing path to contract document
	pubkey_label:
		line edit showing path to public key file
	privkey_label:
		line edit showing path to private key file
	conn_label:
		line edit showing IP address set by user
	ipc_socket:
		socket for ipc interface used for communicating with database storing the chain
	mutex:
		ensures ipc thread safety
	transmission:
		final transmission object
	previous_hash:
		transmission hash of the previous block in the chain
	doc_hash:
		calculated checksum of contract document
	pubkey:
		public key from user specified key file
	privkey:
		private key from user specified key file

	Methods
	-------
	init_ui():
		Initiates main window layout
	set_frame():
		Sets main window size and location, window title and icon
	set_menu():
		Sets menu for main window with exit function
	set_default_contents():
		Sets line edit and progress bar defaults
	set_layouts():
		Sets layout for main window
	close_window():
		Closes main window and terminates ipc interface
	start_ipc():
		Sets up thread and socket for ipc interface
	ipc_send(mode):
		Sends requests to database for receiving head of chain and adding new block to chain
	ipc_receive():
		Receives answers to sent requests over ipc interface
	update_progress_bar(line_edit, s):
		Updates progress bar and given line edit contents
	clicked_select_file():
		Opens a dialog window to select contract document and read it's path
	clicked_pubkey():
		Opens a dialog window to select public key file, read it's path and call get_pubkey(path)
	clicked_privkey():
		Opens a dialog window to select private key file, read it's path and call get_privkey(path)
	connect():
		Opens dialog box for user to enter ip address to connect to or receive from partner in network or set up
		single party contract block
	single_party_contract(ip):
		Creates full block from locally saved document and keys without sending it to a partner
	master_send(ip):
		Initiates communication to partner as master node
	slave_receive(ip):
		Initiates communication to partner as receiver node
	clicked_add_to_layer():
		Adds created block via ipc to chain
	inputs_valid():
		Checks if document hash is not empty and keys are matching
	get_privkey(path):
		Reads private key from file
	get_pubkey(path):
		Reads public key from file
	get_ip(mode):
		Determines public or local IP address depending on mode
	validate_ip(s):
		Checks if s is a valid IP address
	send_to_partner(ip, data):
		Sends data to partner with IP ip via TCP
	receive_from_partner(ip):
		Receives data from partner sent via TCP
	start():
		Starts GUI
	"""

	def __init__(self):
		super(GUI, self).__init__(parent=None)
		self.PROGRESS_MAX = 100
		self.DEFAULT_STRING = "No Data"
		self.progress = QProgressBar(self)
		self.file_label = QLineEdit(self)
		self.pubkey_label = QLineEdit(self)
		self.privkey_label = QLineEdit(self)
		self.conn_label = QLineEdit(self)
		self.ipc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.mutex = threading.Lock()
		self.mutex.acquire()
		self.transmission = transmission.Transmission()
		self.previous_hash = None
		self.doc_hash = None
		self.pubkey = None
		self.privkey = None

		self.init_ui()

	def init_ui(self):
		"""
		Initiates main window layout with all buttons, line edits and progress bar
		"""
		self.set_frame()
		self.set_menu()
		self.set_default_contents()
		self.set_layouts()
		self.start_ipc()
		self.show()

	def set_frame(self):
		"""
		Sets main window size and location, window title and icon
		"""
		screen = QDesktopWidget()
		self.setGeometry(0, 0, screen.width() / 2, screen.height() / 2)
		self.setMinimumSize(screen.width() / 3, screen.height() / 3)
		self.setWindowTitle('CryptoContracts')
		self.setWindowIcon(QIcon('GUI/blockchain.png'))

	def set_menu(self):
		"""
		Sets main window menu with exit function
		"""
		exit_action = QAction(QIcon('exit.png'), '&Exit', self)
		exit_action.setShortcut('Ctrl+Q')
		exit_action.triggered.connect(self.close_window)

		menubar = self.menuBar()
		file_menu = menubar.addMenu('&File')
		file_menu.addAction(exit_action)

	def set_default_contents(self):
		"""
		Sets line edit and progress bar defaults
		"""
		self.file_label.setText(self.DEFAULT_STRING)
		self.file_label.setReadOnly(True)

		self.pubkey_label.setText(self.DEFAULT_STRING)
		self.pubkey_label.setReadOnly(True)

		self.privkey_label.setText(self.DEFAULT_STRING)
		self.privkey_label.setReadOnly(True)

		self.conn_label.setText(self.DEFAULT_STRING)
		self.conn_label.setReadOnly(True)

		self.progress.setMaximum(self.PROGRESS_MAX)
		self.progress.setValue(0)
		self.progress.setTextVisible(False)

	def set_layouts(self):
		"""
		Creates buttons, sets line edit default contents, creates layouts and adds elements to them, adds layouts to
		main window
		"""
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

		widget = QWidget()

		button_layout = QVBoxLayout()
		button_layout.addWidget(select_button)
		button_layout.addWidget(pubkey_button)
		button_layout.addWidget(privkey_button)
		button_layout.addWidget(connect_button)

		label_layout = QVBoxLayout()
		label_layout.setSpacing(6)

		label_layout.addWidget(self.file_label)
		label_layout.addWidget(self.pubkey_label)
		label_layout.addWidget(self.privkey_label)
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

		screen = QDesktopWidget()
		spacer = QSpacerItem(screen.width() / 5, screen.height() / 5, QSizePolicy.Expanding)
		main_hbox_layout = QHBoxLayout()
		main_hbox_layout.addSpacerItem(spacer)
		main_hbox_layout.addLayout(main_vbox_layout)
		main_hbox_layout.addSpacerItem(spacer)

		widget.setLayout(main_hbox_layout)
		self.setCentralWidget(widget)

	def close_window(self):
		"""
		Closes main window and terminates ipc interface
		"""
		self.ipc_socket.shutdown(socket.SHUT_RDWR)
		self.ipc_socket.close()
		qApp.quit()

	def start_ipc(self):
		"""
		Method to set up ipc interface
		:return: If no connection can be established
		"""
		self.ipc_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.ipc_socket.bind((config.get("gui", "addr"), int(config.get("gui", "recv"))))
		try:
			self.ipc_socket.connect((config.get("gui", "addr"), int(config.get("gui", "port"))))
		except OSError as err:
			print("Connection error:", err)
			return
		thread = threading.Thread(target=self.ipc_receive)
		thread.daemon = True
		thread.start()

	def ipc_send(self, mode):
		"""
		Method to send requests for receiving the head of the chain or adding a block to the chain
		:param mode: 1 to request head of chain, 0 to add block to chain
		"""
		if mode == 1:
			self.ipc_socket.send(b'\x11')
			self.mutex.acquire()
		elif mode == 0:
			self.ipc_socket.send(b'\x12' + bytes(self.transmission.to_json(), "utf-8"))

	def ipc_receive(self):
		"""
		Method to receive answers to sent requests via ipc (mode 21 for receiving head, mode 22 for adding block)
		"""
		while True:
			data = self.ipc_socket.recv(4096)
			data = str(data, "utf-8")
			if len(data) > 1:
				content = data[1:]

			if data != "":
				mode = int(bytes(data, "utf-8").hex()[0:2])
				if mode == 21:
					self.previous_hash = json.loads(content)
					self.mutex.release()

				if mode == 22:
					print("Document successfully placed in Chain")

	def update_progress_bar(self, line_edit, s):
		"""
		Updates value of progress bar and sets content of given line edit to s
		:param line_edit: Given line edit of the main window
		:param s: Value to be set as new content of given line edit
		:return: True if s set as new content of line_edit, False if s is empty
		"""
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
		"""
		Opens a dialog window to select contract document and read it's path
		"""
		file = QFileDialog.getOpenFileName(filter='*.pdf')[0]

		if file != "":
			self.doc_hash = core.checksum(path=file)
		self.update_progress_bar(self.file_label, file)

	def clicked_pubkey(self):
		"""
		Opens a dialog window to select a file from where to read in the public key and update progressbar and
		corresponding line edit accordingly
		:return: If public key is empty
		"""
		file = QFileDialog.getOpenFileName(filter='*.pub')[0]

		if file != "":
			try:
				self.pubkey = GUI.get_pubkey(file)
			except ValueError as err:
				print("unexpected public key", err)
				return
		self.update_progress_bar(self.pubkey_label, file)

	def clicked_privkey(self):
		"""
		Opens a dialog window to select a file from where to read in the private key and update progressbar and
		corresponding line edit accordingly
		:return: If private key is empty
		"""
		file = QFileDialog.getOpenFileName(filter='*')[0]

		if file != "":
			try:
				self.privkey = GUI.get_privkey(file)
			except ValueError as err:
				print("unexpected private key", err)
				return
		self.update_progress_bar(self.privkey_label, file)

	def connect(self):
		"""
		Opens dialog box for the user to type in ip address used to connect to or receive from partner in network,
		calling corresponding master_send or slave_receive functions, or setting up a single party contract block in
		case of own ip address
		"""
		mode = ModeDialog()
		mode.exec_()
		master = mode.is_master()
		ip = mode.get_text()
		own_ip = GUI.get_ip("public")

		if self.inputs_valid() and own_ip == ip:
			self.single_party_contract(ip)

		elif self.inputs_valid() and GUI.validate_ip(ip):
			if master:
				self.master_send(ip)
			else:
				self.slave_receive(ip)

		mode.close()

	def single_party_contract(self, ip):
		"""
		Creates a block from local document hash, private and public key and transmission hash of the previous block
		received through ipc interface. On success updates progress bar.
		:param ip: Own IP address to update corresponding line edit upon successful creation of block
		:return: If block transmission hash differs from unsigned transmission hash
		"""
		self.ipc_send(1)
		privkey_list = [self.privkey]
		pubkey_list = [self.pubkey]
		self.doc_hash = str(self.doc_hash)
		self.transmission = core.produce_transmission_fully(previous_hash=self.previous_hash, private_keys=privkey_list, pub_keys=pubkey_list, document_hash=self.doc_hash)
		trans_hash = signing.unsign(self.transmission.transmission_hash, privkey_list)

		if not self.transmission.get_transmission_hash() == trans_hash:
			self.transmission = None
			return
		else:
			print("Block valid")
			self.update_progress_bar(self.conn_label, ip)

	def master_send(self, ip):
		"""
		Initiates communication as master, sending temporary transmission object to and receiving it from partner in two
		stages. In the first stage the document is signed by both partners, in the second stage the transmission hash is
		signed by both partners and the progress bar is updated afterwards.
		:param ip: IP address of partner to send temporary blocks to
		:return: If connection fails
		"""
		own_ip = GUI.get_ip("public")

		if GUI.validate_ip(ip):
			if not ip == own_ip:

				# stage 1 start
				temp_trans = core.produce_transmission_stage_one(self.privkey, self.pubkey, self.doc_hash)
				trans_json = temp_trans.to_json()

				if GUI.send_to_partner(ip, trans_json):
					try:
						received_trans = GUI.receive_from_partner(own_ip)
					except ValueError as err:
						print("Connection failed:", err)
						return

					# stage 2 start
					self.ipc_send(1)
					temp = core.Transmission.from_json(received_trans)
					temp.hash = str(temp.hash)
					temp.signed_hash = str(temp.signed_hash)
					temp_trans2 = core.produce_transmission_stage_two(previous_hash=self.previous_hash, private_key=self.privkey, transmission=temp, master=True)
					trans_json2 = temp_trans2.to_json()
					GUI.send_to_partner(ip, trans_json2)
					try:
						received_trans = GUI.receive_from_partner(GUI.get_ip(own_ip))
					except ValueError as err:
						print("Connection failed:", err)
						return
					self.transmission = core.Transmission.from_json(received_trans)
					self.update_progress_bar(self.conn_label, ip)

				else:
					return
		else:
			ip = ""
			self.update_progress_bar(self.conn_label, ip)

	def slave_receive(self, ip):
		"""
		Initiates communication as slave, receiving temporary transmission object from and sending it to partner in two
		stages. In the first stage the document is signed by both partners, in the second stage the transmission hash is
		signed by both partners and the progress bar is updated afterwards.
		:param ip: IP address of partner to send temporary blocks to
		:return: If connection fails
		"""
		own_ip = GUI.get_ip("public")
		# stage 1 start
		received_json = GUI.receive_from_partner(own_ip)
		received_trans = core.Transmission.from_json(received_json)
		temp_trans = core.produce_transmission_stage_one(self.privkey, self.pubkey, transmission=received_trans)
		trans_json = temp_trans.to_json()
		GUI.send_to_partner(ip, trans_json)

		# stage 2 start
		received_json = GUI.receive_from_partner(own_ip)
		received_trans = core.Transmission.from_json(received_json)
		temp_trans = core.produce_transmission_stage_two(previous_hash=None, private_key=self.privkey, transmission=received_trans, master=False)
		trans_json = temp_trans.to_json()
		GUI.send_to_partner(ip, trans_json)
		self.update_progress_bar(self.conn_label, ip)

	def clicked_add_to_layer(self):
		"""
		Adds the created block via ipc interface to the chain if inputs are valid
		"""
		if self.inputs_valid() and self.conn_label != self.DEFAULT_STRING:
			self.ipc_send(0)
			self.progress.setValue(self.PROGRESS_MAX)

	def inputs_valid(self):
		"""
		Checks if relevant inputs are not empty and keys are correct
		:return: True if document, public key and private key are set and matching, False otherwise
		"""
		if self.file_label != self.DEFAULT_STRING and self.pubkey_label != self.DEFAULT_STRING and self.privkey_label != self.DEFAULT_STRING:
			if signing.unsign(signing.sign(self.doc_hash, [self.pubkey]), [self.privkey]) == str(self.doc_hash):
				return True
			else:
				print("Keys are not matching")
			return False
		else:
			return False

	@staticmethod
	def get_privkey(path):
		"""
		Method to read private key from file and save it in a string
		:param path: Path to private key file
		:return: Private key as string
		"""
		file = open(path, "r")
		write_flag = False
		privkey = ""
		for line in file:
			if "PRIVATE" in line and not write_flag:
				write_flag = True
			elif "PRIVATE" in line and write_flag:
				privkey += line
				write_flag = False
			if write_flag:
				privkey += line
		if not privkey:
			raise ValueError
		return privkey

	@staticmethod
	def get_pubkey(path):
		"""
		Method to read private key from file and save it in a string
		:param path: Path to public key file
		:return: Public key as string
		"""
		file = open(path, "r")
		pubkey = ""
		for line in file:
			pubkey += line
		if not pubkey:
			raise ValueError
		return pubkey

	@staticmethod
	def get_ip(mode):
		"""
		Method to get own public or local IP address
		:param mode: public for public IP, local for local IP
		:return: Public or local IP depending on mode, or None otherwise
		"""
		if mode == "public":
			return get('https://api.ipify.org').text
		elif mode == "local":
			return socket.gethostbyname(socket.gethostname())
		else:
			return None

	@staticmethod
	def validate_ip(s):
		"""
		Checks if string has a valid IP address structure
		:param s: Input string
		:return: True for valid IP address, False for invalid IP address
		"""
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
		"""
		Method to send data string to given IP address via TCP
		:param ip: IP address to connect to
		:param data: String of data to be sent
		:return: True if data sent, False otherwise
		"""
		byte = bytes(data, "utf-8")
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			s.connect((ip, int(config.get("comm", "port"))))
		except OSError as err:
			print("Could not connect:", err)
			s.close()
			return False
		s.send(byte)
		s.close()
		return True

	@staticmethod
	def receive_from_partner(ip):
		"""
		Method to receive data from given IP address
		:param ip: IP address to receive data from
		:return: Received data as String
		"""
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.bind(("0.0.0.0", int(config.get("comm", "port"))))
		s.listen(1)
		data_str = ""

		conn, addr = s.accept()
		while 1:
			data = conn.recv(4096)
			if not data:
				break
			data_str += data.decode("utf-8")
		conn.close()
		if not data_str:
			raise ValueError
		return data_str


# Stylesheet for background of main window
stylesheet = """GUI {
	border-image: url("GUI/blockchain.png");
	background-repeat: no-repeat;
	background-position: center;}"""


def start():
	"""
	Starts GUI
	"""
	app = QApplication(sys.argv)
	app.setStyleSheet(stylesheet)
	ex = GUI()
	sys.exit(app.exec_())

