import filecmp
import sys

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication

from floppy import node_lib
from floppy import train_config
from floppy.graph import Graph
from floppy.painter import MainWindow, Painter2D
from floppy.train_config import TrainParamServer

if __name__ == '__main__':
    # To initialize train_parameter.
    test_app = QApplication(sys.argv)
    settings = QSettings('test_compiler', 'test_compiler')

    painter = Painter2D()
    test_window = MainWindow(painter=painter)
    train_config.TrainDialog(test_window, settings=settings)

    graph = Graph(painter=painter)
    with open('../../examples/mnist.json', 'r') as fp:
        graph.load_from_json(fp.readline())
        graph.compile()
        TrainParamServer().from_json(fp.readline())

    assert filecmp.cmp('MyNet1.py', 'expect.txt')
    assert TrainParamServer().__dict__ == {'Epoch': 10,
                                           'NetName': 'MyNet1',
                                           'BatchSize': 20,
                                           'GPU': 0,
                                           'Optimizer': 'AdaDelta'}
