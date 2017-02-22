import importlib

from floppy.train_configuration import TrainParamServer
from PyQt5.QtWidgets import QErrorMessage


class Runner(object):
    def __init__(self):
        self.is_running = False
        self.run_process = None

    def run(self):
        self.is_running = True
        module_file = TrainParamServer()['NetName']
        try:
            module = importlib.import_module(module_file)
        except SyntaxError:
            error = QErrorMessage()
            error.showMessage('Generated chainer script ({}.py) is not valid.'
                              .format(TrainParamServer()['NetName']))
            error.exec_()
            return
        module.main(True)
        del module

    def kill(self):
        pass
