from pathlib import Path
from time import strftime, gmtime, time_ns
import traceback
import sys
import shutil
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QRunnable, QObject, pyqtSignal
import ionic_vision.constants as c


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)


class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
            print('failed running threaded task')
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


class InspectionParameters(QtWidgets.QDialog):
    def __init__(self):
        super(InspectionParameters, self).__init__()

        uic.loadUi('user_interface/inspection_parameters.ui', self)

        self.max_slit = self.findChild(QtWidgets.QDoubleSpinBox, 'doubleSpinBox_9')
        self.min_slit = self.findChild(QtWidgets.QDoubleSpinBox, 'doubleSpinBox_8')
        self.max_center_x = self.findChild(QtWidgets.QDoubleSpinBox, 'doubleSpinBox_7')
        self.min_center_x = self.findChild(QtWidgets.QDoubleSpinBox, 'doubleSpinBox_6')
        self.max_center_y = self.findChild(QtWidgets.QDoubleSpinBox, 'doubleSpinBox_5')
        self.min_center_y = self.findChild(QtWidgets.QDoubleSpinBox, 'doubleSpinBox_4')
        self.max_parallel = self.findChild(QtWidgets.QDoubleSpinBox, 'doubleSpinBox_3')
        self.min_parallel = self.findChild(QtWidgets.QDoubleSpinBox, 'doubleSpinBox_2')
        self.mm_per_px = self.findChild(QtWidgets.QDoubleSpinBox, 'doubleSpinBox')
        self.pixel = self.findChild(QtWidgets.QSpinBox, 'spinBox')

        self.max_slit.setValue(c.MAX_SLIT_MM.get_value())
        self.min_slit.setValue(c.MIN_SLIT_MM.get_value())
        self.max_center_x.setValue(c.MAX_SKEW_MM.get_value())
        self.min_center_x.setValue(0)
        self.max_center_y.setValue(c.MAX_THICKNESS_MM.get_value())
        self.min_center_y.setValue(c.MIN_THICKNESS_MM.get_value())
        self.max_parallel.setValue(c.MIN_PARA_DEG.get_value())
        self.min_parallel.setValue(0)
        self.mm_per_px.setValue(c.MM_PER_PIXEL_NUM)
        self.pixel.setValue(c.MM_PER_PIXEL_DEN)

    def accept(self):
        c.MIN_SLIT_MM.set_value(self.min_slit.value())
        c.MAX_SLIT_MM.set_value(self.max_slit.value())
        c.MAX_SKEW_MM.set_value(self.max_center_x.value())
        c.MAX_THICKNESS_MM.set_value(self.max_center_y.value())
        c.MIN_THICKNESS_MM.set_value(self.min_center_y.value())
        c.MIN_PARA_DEG.set_value(self.max_parallel.value())
        c.MM_PER_PIXEL_NUM = self.mm_per_px.value()
        c.MM_PER_PIXEL_DEN = self.pixel.value()
        c.update()
        c.save_settings()
        self.close()


class Login(QtWidgets.QDialog):
    def __init__(self):
        super(Login, self).__init__()

        uic.loadUi('user_interface/login.ui', self)

        self.username = self.findChild(QtWidgets.QLineEdit, 'lineEdit')
        self.password = self.findChild(QtWidgets.QLineEdit, 'lineEdit_2')

        self.accepted = 1
        self.username.setFocus()

    def accept(self):
        """
        Perform the accept option. Overrides the accept method of the QDialog class to handle the username/password
        checking.
        :return: Null
        """
        # Extract username/password
        u = str(self.username.text())
        p = str(self.password.text())

        # Verify the username and password against the values in the settings file
        if u == c.USERNAME and p == c.PASSWORD:
            c.USER_ELEVATION = c.USER_ENGINEERING
            c.LOGIN_TIME = time_ns()
        else:
            self.accepted = 0
            self.reject()

        self.close()


def manage_save_files():
    file_dir_base = Path(f'./logs/images/')
    file_dirs = []
    try:
        for x in file_dir_base.iterdir():
            if x.is_dir():
                file_dirs.append(x)
    except:
        print('file directory not found')

    time_str = strftime('%Y%m%d%H%M%S', gmtime())
    new_path = Path(f'./logs/images/{time_str}')

    if len(file_dirs) > 0:
        if file_dirs[-1] != time_str:
            new_path.mkdir(mode=0o777, parents=True)
            Path(f'{new_path}/proc/fail/A').mkdir(mode=0o777, parents=True)
            Path(f'{new_path}/proc/pass/A').mkdir(mode=0o777, parents=True)
            Path(f'{new_path}/raw/fail/A').mkdir(mode=0o777, parents=True)
            Path(f'{new_path}/raw/pass/A').mkdir(mode=0o777, parents=True)
    else:
        new_path.mkdir(mode=0o777, parents=True)
        Path(f'{new_path}/proc/fail/A').mkdir(mode=0o777, parents=True)
        Path(f'{new_path}/proc/pass/A').mkdir(mode=0o777, parents=True)
        Path(f'{new_path}/raw/fail/A').mkdir(mode=0o777, parents=True)
        Path(f'{new_path}/raw/pass/A').mkdir(mode=0o777, parents=True)

    while len(file_dirs) >= 4:
        remove_path = Path(f'{file_dirs[0]}')
        shutil.rmtree(remove_path)
        file_dirs.pop(0)

    return file_dirs[0]
