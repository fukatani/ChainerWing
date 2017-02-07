from floppy.graph import Graph
from floppy.painter import Painter2D, MainWindow
import sys
from PyQt5.QtWidgets import QApplication
import argparse
import logging

logger = logging.getLogger('Floppy')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('floppy.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)



def run():
    logger.info('Starting Floppy Application with '+' '.join(sys.argv))
    app = QApplication(sys.argv)
    painter = initializePainter()
    startUI(app, painter)


def initializePainter():
    painter = Painter2D()
    Graph(painter=painter)

    return painter


def startUI(app, painter):
    win = MainWindow(painter=painter)
    win.setArgs(parseArgv())
    win.show()
    logger.debug('Startup successful. Handing main thread control to Qt main loop.')
    sys.exit(app.exec_())
    # try:
    #     sys.exit(app.exec_())
    # except KeyboardInterrupt:
    #     print('Keyboard Interrupt. Shutting down gracefully.')
    #     win.killRunner()

def parseArgv():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', action='store_true', required=False)
    parser.add_argument('--test', nargs=1, required=False, default=False)
    args = parser.parse_args()
    return args


