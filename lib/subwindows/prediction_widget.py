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
        self.model_sel_button.clicked.connect(self.set_model)

    def set_input(self):
        init_path = TrainParamServer().get_data_dir()
        data_file = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Select Input Data File', init_path,
            filter='(*.csv, *.npz, *.py);; Any (*.*)')[0]
        if data_file:
            self.input_data_name.setText(self.value)

    def set_model(self):
        init_path = TrainParamServer().get_data_dir()
        data_file = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Select Model Data File', init_path,
            filter='(*.npz);; Any (*.*)')[0]
        if data_file:
            self.model_name.setText(self.value)

    def set_output(self):
        init_path = TrainParamServer().get_data_dir()
        data_file = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Select Input Data File', init_path,
            filter='(*.csv, *.npz);; Any (*.*)')[0]
        if data_file:
            self.output_name.setText(self.value)

    def exe_prediction(self):
        runner = PredictionRunner()
        runner.run()
