from importlib import machinery

from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets

from lib.data_fetch import DataManager
from lib.subwindows.train_config import TrainParamServer
from lib.cw_progress_bar import CWProgressBar


class TrainRunner(object):

    def __init__(self):
        train_server = TrainParamServer()
        module_file = machinery.SourceFileLoader("net_run",
                                                 train_server.get_net_name())
        self.module = module_file.load_module()

        # Progress bar should be initialized after loading module file.
        self.pbar = CWProgressBar(train_server['Epoch'])

    def run(self):
        train_data, test_data = DataManager().get_data_train()
        self.module.training_main(train_data, test_data, self.pbar)

    def kill(self):
        self.pbar.finalize()


class PredictionRunner(object):

    def __init__(self):
        train_server = TrainParamServer()
        module_file = machinery.SourceFileLoader("net_run",
                                                 train_server.get_net_name())
        self.module = module_file.load_module()

    def run(self, classification=False):
        input_data = DataManager().get_data_pred()
        #pbar = PredProgressBar()
        #pbar.onStart()
        result = self.module.prediction_main(input_data, classification)
        #pbar.onFinished()
        return result


class PredProgressBar(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(PredProgressBar, self).__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)

        # Create a progress bar and a button and add them to the main layout
        self.progressBar = QtWidgets.QProgressBar(self)
        self.progressBar.setRange(0,1)
        layout.addWidget(self.progressBar)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

    def onStart(self):
        self.progressBar.setValue(0)
        self.show()
        self.raise_()

    def onFinished(self):
        # Stop the pulsation
        self.progressBar.setValue(1)
