import importlib

from lib.train_config import TrainParamServer
from PyQt5.QtWidgets import QErrorMessage


class Runner(object):

    def run(self, do_train):
        module_file = TrainParamServer().get_net_name()
        try:
            module = importlib.import_module(module_file)
        except SyntaxError:
            error = QErrorMessage()
            error.showMessage('Generated chainer script ({}.py) is not valid.'
                              .format(TrainParamServer().get_net_name()))
            error.exec_()
            return
        if do_train:
            module.training_main(True)
        else:
            module.prediction_main()
        del module

    def kill(self):
        pass
