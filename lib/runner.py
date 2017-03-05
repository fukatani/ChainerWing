from importlib import machinery

from lib import util
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
        self.pbar = CWProgressBar(train_server['Epoch'])
        module_file = machinery.SourceFileLoader("net_run",
                                                 train_server.get_net_name())
        self.module = module_file.load_module()

    def run(self):
        input_data = DataManager().get_data_pred()
        return self.module.prediction_main(input_data)

    def kill(self):
        self.pbar.finalize()
