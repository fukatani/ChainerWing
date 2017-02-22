from floppy.train_configuration import TrainParamServer

from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QPoint


class ReportWidget(QTabWidget):

    def __init__(self, *args, **kwargs):
        super(ReportWidget, self).__init__(height=210, *args, **kwargs)
        self.setStyleSheet('''ReportWidget{background: rgb(55,55,55)}
        ''')
        try:
            loss_image = TrainParamServer()['WorkDir'] + "result/loss.png"
        except KeyError:
            loss_image = "result/loss.png"
        self.addTab(GraphWidget(loss_image, parent=self), 'Loss')
        try:
            acc_image = TrainParamServer()['WorkDir'] + "result/accuracy.png"
        except KeyError:
            acc_image = "result/accuracy.png"
        self.addTab(GraphWidget(acc_image, parent=self), 'Accuracy')
        self.resize(200, 200)


class GraphWidget(QWidget):

    def __init__(self, image_file, *args, **kwargs):
        super(GraphWidget, self).__init__(height=200)
        self.setStyleSheet('''ReportWidget{background: rgb(55,55,55)}
        ''')
        self.pixmap = None
        self.image_file = image_file

    def paintEvent(self, event):
        if 'Class' not in TrainParamServer()['TrainMode']:
            if 'accuracy' in self.image_file:
                return
        self.pixmap = QPixmap(self.image_file)
        #self.adjustSize()
        size = self.size()
        painter = QPainter(self)
        point = QPoint(0, 0)
        scaled_pix = self.pixmap.scaled(size, Qt.KeepAspectRatio,
                                        transformMode=Qt.SmoothTransformation)
        # start painting the label from left upper corner
        point.setX((size.width() - scaled_pix.width()) / 2)
        point.setY((size.height() - scaled_pix.height()) / 2)
        painter.drawPixmap(point, scaled_pix)
