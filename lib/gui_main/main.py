import argparse
import logging
import os
import sys

from PyQt5 import QtWidgets

from lib.gui_main.graph import Graph
from lib.gui_main.painter import Painter2D, MainWindow

logger = logging.getLogger('Chainer-Wing')
logger.setLevel(logging.DEBUG)
if os.path.isfile('cw_debug.log'):
    os.remove('cw_debug.log')
fh = logging.FileHandler('cw_debug.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)


def run():
    logger.info('Starting Floppy Application with '+' '.join(sys.argv))
    app = QtWidgets.QApplication(sys.argv)
    painter = initialize_painter()
    startUI(app, painter)


def initialize_painter():
    painter = Painter2D()
    Graph(painter=painter)
    return painter


def startUI(app, painter):
    win = MainWindow(painter=painter)
    win.setArgs(parse_argv())
    win.show()
    logger.debug('Startup successful. Handing main thread control to Qt main loop.')
    sys.exit(app.exec_())


def parse_argv():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', action='store_true', required=False)
    parser.add_argument('--test', nargs=1, required=False, default=False)
    args = parser.parse_args()
    return args
