import os

from PyQt5 import QtWidgets
from lib.subwindows.prediction import Ui_PredictionWindow
from lib.subwindows.train_config import TrainParamServer
from lib.runner import PredictionRunner


class PredictionWindow(QtWidgets.QMainWindow, Ui_PredictionWindow):
    def __init__(self, *args, settings=None):
        self.settings = settings
        super(PredictionWindow, self).__init__(*args)
        self.setupUi(self)

        self.input_sel_button.clicked.connect(self.set_input)
        self.input_config = PredInputDataConfig(self.input_data_name, self)
        self.output_sel_button.clicked.connect(self.set_output)
        self.output_config = PredOutputDataConfig(self.output_name, self)
        self.model_sel_button.clicked.connect(self.set_model)
        self.model_config = PredModelConfig(self.model_name, self)

        self.exe_button.clicked.connect(self.exe_prediction)

    def set_input(self):
        self.input_config.set_data()

    def set_model(self):
        self.model_config.set_data()

    def set_output(self):
        self.output_config.set_data()

    def exe_prediction(self):
        runner = PredictionRunner()
        result = runner.run()
        self.result_table


class DataConfig(object):
    def __init__(self, label, window):
        self.param_name = self.__class__.__name__[:-6]  # remove 'Config'
        self.label = label
        train_server = TrainParamServer()
        if self.param_name in train_server.__dict__:
            self.label = label.setText(train_server[self.param_name])
        self.window = window
        self.direction = ''
        self.filter = ''

    def set_data(self):
        train_server = TrainParamServer()
        if self.param_name in train_server.__dict__:
            init_path = train_server[self.param_name]
            init_path = os.path.abspath(init_path)
        else:
            init_path = train_server.get_work_dir()
        data_file = QtWidgets.QFileDialog.getOpenFileName(
            self.window, self.direction, init_path,
            filter=self.filter)[0]
        if data_file:
            self.label.setText(data_file)
            train_server[self.param_name] = data_file
        else:
            self.label.setText(self.direction)
            del train_server[self.param_name]


class PredInputDataConfig(DataConfig):
    def __init__(self, label, window):
        super(PredInputDataConfig, self).__init__(label, window)
        self.direction = 'Select Input Data File'
        self.filter = '(*.csv, *.npz, *.py);; Any (*.*)'


class PredOutputDataConfig(DataConfig):
    def __init__(self, label, window):
        super(PredOutputDataConfig, self).__init__(label, window)
        self.direction = 'Select Output Data File'
        self.filter = '(*.csv, *.npz);; Any (*.*)'


class PredModelConfig(DataConfig):
    def __init__(self, label, window):
        super(PredModelConfig, self).__init__(label, window)
        self.direction = 'Select Model File'
        self.filter = '(*.npz);; Any (*.*)'
