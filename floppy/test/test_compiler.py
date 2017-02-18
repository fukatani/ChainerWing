from floppy.graph import Graph
from floppy import node_lib
from floppy import train_configuration
from floppy.painter import MainWindow, Painter2D
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
    graph.load_from_json('../../examples/mnist.ppy')
    graph.execute()

    assert filecmp.cmp('ExampleNet.py', 'expect.txt')
