import sys

from PyQt5 import QtCore
from PyQt5 import QtWidgets, uic, QtGui
from ionic.plc import MachinePLC


class UI(QtWidgets.QMainWindow):
    def __init__(self, machine_plc):
        super(UI, self).__init__()
        uic.loadUi('user_interface/user_interface.ui', self)
        self.setWindowIcon(QtGui.QIcon('user_interface/robot.ico'))

        # Define threadpool object
        self.threadpool = QtCore.QThreadPool()

        self.plc = machine_plc

        self.complete_timer = QtCore.QTimer()
        self.complete_timer.timeout.connect(self.complete_timer_callback)

        # extract UI elements
        self.spinbox_current_pos = self.findChild(QtWidgets.QDoubleSpinBox, 'doubleSpinBox')
        self.spinbox_requested_pos = self.findChild(QtWidgets.QDoubleSpinBox, 'doubleSpinBox_3')
        self.spinbox_rob_req_pos = self.findChild(QtWidgets.QDoubleSpinBox, 'doubleSpinBox_4')

        self.btn_go_to = self.findChild(QtWidgets.QPushButton, 'pushButton')
        self.btn_home = self.findChild(QtWidgets.QPushButton, 'pushButton_2')
        self.btn_stop = self.findChild(QtWidgets.QPushButton, 'pushButton_3')
        self.btn_stop.setStyleSheet('background-color: rgb(150, 0, 0); color: white')
        self.btn_force_req = self.findChild(QtWidgets.QPushButton, 'pushButton_4')
        self.btn_force_complete = self.findChild(QtWidgets.QPushButton, 'pushButton_5')

        self.ind_motion_req = self.findChild(QtWidgets.QLabel, 'label')
        self.ind_motion_complete = self.findChild(QtWidgets.QLabel, 'label_2')
        self.ind_motion_progress = self.findChild(QtWidgets.QLabel, 'label_3')

        # Connect callbacks
        self.btn_go_to.clicked.connect(self.go_to_callback)
        self.btn_home.clicked.connect(self.home_callback)
        self.btn_stop.clicked.connect(self.stop_callback)
        self.btn_force_complete.clicked.connect(self.force_motion_complete_callback)

        self.spinbox_requested_pos.valueChanged.connect(self.spinbox_callback)

        self.show()

    def spinbox_callback(self):
        self.plc.manual_run = False

    def go_to_callback(self):
        if not self.plc.manual_run:
            self.plc.command_pos = self.spinbox_requested_pos.value()
            self.plc.manual_run = True
            self.statusBar().showMessage(f'Requesting motion to {self.plc.command_pos:.1f} degrees')
        else:
            self.plc.manual_run = False

    def home_callback(self):
        self.plc.home_bit = True
        self.statusBar().showMessage('Re-zeroed encoder')

    def stop_callback(self):
        self.plc.manual_run = False

    def force_motion_request_callback(self):
        pass

    def force_motion_complete_callback(self):
        if self.btn_force_complete.isChecked():
            self.plc.motion_complete = True
        else:
            self.plc.motion_complete = False
        pass

    def complete_timer_callback(self):
        self.plc.manual_run = False
        self.statusBar().showMessage('Motion complete')

    def ui_loop(self):
        self.spinbox_current_pos.setValue(self.plc.current_position)
        # self.spinbox_requested_pos.setValue(self.plc.requested_position)
        self.spinbox_rob_req_pos.setValue(self.plc.robot_requested_position)

        # Robot request indicator
        if self.plc.robot_request_bit:
            self.ind_motion_req.setStyleSheet('background-color: green')
        else:
            self.ind_motion_req.setStyleSheet('')

        # Button indicator
        if self.plc.manual_run and not self.complete_timer.isActive():
            self.btn_go_to.setStyleSheet('background-color: green')
        elif self.plc.manual_run and self.complete_timer.isActive():
            self.btn_go_to.setStyleSheet('background-color: yellow')
        else:
            self.btn_go_to.setStyleSheet('')

        # Motion complete indicator
        if self.plc.motion_complete:
            # If the complete timer is not started, start it
            if not self.complete_timer.isActive() and self.plc.manual_run:
                self.complete_timer.start(1000)

            self.ind_motion_complete.setStyleSheet('background-color: green')
        else:
            self.complete_timer.stop()
            self.ind_motion_complete.setStyleSheet('')

        # Motion in progress indicator
        if (self.plc.robot_request_bit or self.plc.manual_run) and not self.plc.motion_complete:
            self.ind_motion_progress.setStyleSheet('background-color: green')
        else:
            self.ind_motion_progress.setStyleSheet('')


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    plc = MachinePLC('192.168.1.12')
    window = UI(plc)

    timer_ui = QtCore.QTimer()
    timer_plc = QtCore.QTimer()
    timer_ui.timeout.connect(window.ui_loop)
    timer_plc.timeout.connect(plc.run)
    timer_ui.start(10)
    timer_plc.start(100)
    app.exec_()
