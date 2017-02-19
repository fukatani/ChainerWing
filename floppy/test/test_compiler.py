from floppy.graph import Graph
from floppy import node_lib
from floppy import train_configuration
from floppy.painter import MainWindow, Painter2D
from floppy.train_configuration import TrainParamServer
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSettings
import sys
import filecmp


if __name__ == '__main__':
    # To initialize train_parameter.
    test_app = QApplication(sys.argv)
    settings = QSettings('test_compiler', 'test_compiler')

    painter = Painter2D()
    test_window = MainWindow(painter=painter)
    train_configuration.TrainDialog(test_window, settings=settings)

    graph = Graph(painter=painter)
    with open('../../examples/mnist.json', 'r') as fp:
        graph.load_from_json(fp.readline())
        graph.execute()
        TrainParamServer().from_json(fp.readline())

    assert filecmp.cmp('MyNet1.py', 'expect.txt')
    assert TrainParamServer().__dict__ == {'Epoch': 20,
                                           'NetName': 'MyNet1',
                                           'BatchSize': 20,
                                           'GPU': 11,
                                           'Optimizer': 'AdaDelta'}

