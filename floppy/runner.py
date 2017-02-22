import importlib

from floppy.train_configuration import TrainParamServer
from PyQt5.QtWidgets import QErrorMessage


class Runner(object):

    def run(self, do_train):
        module_file = TrainParamServer()['NetName']
        try:
            module = importlib.import_module(module_file)
        except SyntaxError:
            error = QErrorMessage()
            error.showMessage('Generated chainer script ({}.py) is not valid.'
                              .format(TrainParamServer()['NetName']))
            error.exec_()
            return
        if do_train:
            module.training_main(True)
        else:
            module.prediction_main()
        del module

    def kill(self):
        pass
