import filecmp
import sys

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication

from chainer_wing.gui_main.graph import Graph
from chainer_wing.gui_main.painter import MainWindow, Painter2D
from chainer_wing.subwindows import train_config
from chainer_wing.subwindows.train_config import TrainParamServer

if __name__ == '__main__':
    # To initialize train_parameter.
    test_app = QApplication(sys.argv)
    settings = QSettings('test_compiler', 'test_compiler')

    painter = Painter2D()
    test_window = MainWindow(painter=painter)
    train_config.TrainDialog(test_window, settings=settings)

    graph = Graph(painter=painter)
    with open('../../examples/mnist.json', 'r') as fp:
        graph.load_from_dict(fp.readline())
        graph.compile()
        TrainParamServer().load_from_dict(fp.readline())

    assert filecmp.cmp('MyNet1.py', 'expect.txt')
    assert TrainParamServer().__dict__ == {'Epoch': 10,
                                           'NetName': 'MyNet1',
                                           'BatchSize': 20,
                                           'GPU': 0,
                                           'Optimizer': 'AdaDelta'}
