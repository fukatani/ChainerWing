from importlib import machinery

from lib.data_fetch import DataManager
from lib.extension.cw_progress_bar import CWProgressBar
from lib.extension.plot_extension import cw_postprocess
from lib.subwindows.train_config import TrainParamServer


class TrainRunner(object):

    def __init__(self):
        train_server = TrainParamServer()
        module_file = machinery.SourceFileLoader('net_run',
                                                 train_server.get_net_name())
        self.module = module_file.load_module()

        # Progress bar should be initialized after loading module file.
        self.pbar = CWProgressBar(train_server['Epoch'])

    def run(self):
        train_data, test_data = DataManager().get_data_train()
        self.module.training_main(train_data, test_data, self.pbar,
                                  cw_postprocess)

    def kill(self):
        self.pbar.finalize()


class PredictionRunner(object):

    def __init__(self):
        train_server = TrainParamServer()
        module_file = machinery.SourceFileLoader('net_run',
                                                 train_server.get_net_name())
        self.module = module_file.load_module()

    def run(self, classification=False):
        input_data = DataManager().get_data_pred()
        result = self.module.prediction_main(input_data, classification)
        return result
