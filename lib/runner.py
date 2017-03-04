import importlib

from lib import util
from lib.data_fetch import DataManager
from lib.subwindows.train_config import TrainParamServer

from lib.cw_progress_bar import CWProgressBar


class TrainRunner(object):

    def __init__(self):
        self.pbar = CWProgressBar(TrainParamServer()['Epoch'])
        module_file = TrainParamServer()['NetName']
        self.module = importlib.import_module(module_file)

    def run(self):
        train_data, test_data = DataManager().get_data_train()
        self.module.training_main(train_data, test_data, self.pbar)

    def kill(self):
        self.pbar.finalize()


class PredictionRunner(object):

    def __init__(self):
        self.pbar = CWProgressBar(TrainParamServer()['Epoch'])
        module_file = TrainParamServer()['NetName']
        self.module = importlib.import_module(module_file)

    def run(self):
        input_data = DataManager().get_data_pred()
        self.module.prediction_main(input_data)

    def kill(self):
        self.pbar.finalize()
