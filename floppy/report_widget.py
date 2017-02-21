from floppy.train_configuration import TrainParamServer

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QPoint


class ReportWidget(QWidget):

    def __init__(self, *args, **kwargs):
        super(ReportWidget, self).__init__(height=200, *args, **kwargs)
        self.setStyleSheet('''ReportWidget{background: rgb(55,55,55)}
        ''')
        try:
            loss_image = TrainParamServer()['WorkDir'] + "result/loss.png"
        except KeyError:
            loss_image = "result/loss.png"
        self.pixmap = QPixmap(loss_image)
        self.resize(200, 200)

    def paintEvent(self, event):
        self.adjustSize()
        size = self.size()
        painter = QPainter(self)
        point = QPoint(0, 0)
        scaled_pix = self.pixmap.scaled(size, Qt.KeepAspectRatio,
                                        transformMode=Qt.SmoothTransformation)
        # start painting the label from left upper corner
        point.setX((size.width() - scaled_pix.width()) / 2)
        point.setY((size.height() - scaled_pix.height()) / 2)
        painter.drawPixmap(point, scaled_pix)
