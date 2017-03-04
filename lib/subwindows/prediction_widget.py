from PyQt5 import QtWidgets
from lib.subwindows.prediction import Ui_PredictionWindow


class PredictionWindow(QtWidgets.QMainWindow, Ui_PredictionWindow):
    def __init__(self, *args, settings=None):
        self.settings = settings
        super(PredictionWindow, self).__init__(*args)
        self.setupUi(self)
