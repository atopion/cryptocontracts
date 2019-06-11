import sys
import time
from PyQt5.QtWidgets import QApplication, QFileDialog as dialog
import PyQt5.uic as uic
import Core
import storage


class GUI:

    def __init__(self):
        super().__init__()
        self.init_gui()

    def init_gui(self):
        def clicked_select_file():
            file = dialog.getOpenFileName(filter='*.pdf')[0]
            # checksum calling crashes program
            # file_hash = Core.checksum()

        def clicked_signature():
            sig = dialog.getOpenFileName(filter='*.pdf')[0]
            # checksum calling crashes program
            # sig_hash = Core.checksum()
            # print(sig_hash)

        def clicked_add_layer():
            self.approveDialog.exec_()
            for i in range(1, 101):
                time.sleep(0.2)
                mainWindow.progressBar.setValue(i)

        self.mainWindow = uic.loadUi("cryptocontracts.ui")
        self.approveDialog = uic.loadUi("approveDialog.ui")

        mainWindow = self.mainWindow
        mainWindow.pButtonSelect.clicked.connect(clicked_select_file)
        mainWindow.pButtonSign1.clicked.connect(clicked_signature)
        mainWindow.pButtonSign2.clicked.connect(clicked_signature)
        mainWindow.pButtonAddToLayer.clicked.connect(clicked_add_layer)

        mainWindow.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = GUI()
    sys.exit(app.exec_())
