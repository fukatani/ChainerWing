import importlib

from lib import util
from lib.data_fetch import DataManager
from lib.subwindows.train_config import TrainParamServer

from lib.cw_progress_bar import CWProgressBar


class Runner(object):

    def __init__(self):
        # Stop Training if True.
        self.pbar = CWProgressBar(TrainParamServer()['Epoch'])

    def run(self, do_train):
        module_file = TrainParamServer()['NetName']
        try:
            module = importlib.import_module(module_file)
        except SyntaxError:
            util.disp_error('Generated chainer script ({}.py) is not valid.'
                            .format(TrainParamServer().get_net_name()))
            return
        if do_train:
            train_data, test_data = DataManager().get_data_train()
            module.training_main(train_data, test_data, self.pbar)
        else:
            input_data = DataManager().get_data_pred()
            module.prediction_main(input_data)
        del module

    def kill(self):
        self.pbar.finalize()
