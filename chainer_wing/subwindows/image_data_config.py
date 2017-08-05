import glob

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtGui

from chainer_wing.subwindows.train_config import TrainParamServer
from chainer_wing.subwindows.data_config import AbstractDataDialog
from chainer_wing.subwindows.data_config import DataCheckBox
from chainer_wing.subwindows.data_config import DataFileEdit
from chainer_wing.subwindows.data_config import DataFileLabel
from chainer_wing.subwindows.data_config import DataLineEdit

import chainercv.utils


class ImageDataDialog(AbstractDataDialog):
    def configure_window(self):
        settings = self.settings
        self.train_edit = DataFileEdit(settings, self, 'TrainData')
        self.test_edit = DataFileEdit(settings, self, 'TestData')
        self.same_data_check = DataCheckBox(settings, self, 'UseSameData')
        self.same_data_check.stateChanged.connect(self.state_changed)
        self.shuffle_check = DataCheckBox(settings, self, 'Shuffle')
        self.ratio_edit = DataLineEdit(settings, self, 'TestDataRatio')

        self.use_resize = DataCheckBox(settings, self, 'UseResize')
        self.resize_width = DataLineEdit(settings, self, 'ResizeWidth', int)
        self.resize_height = DataLineEdit(settings, self, 'ResizeHeight', int)

        # Data augmentation
        self.crop_edit = CropEdit(settings, self)
        self.crop_width = DataLineEdit(settings, self, 'CropWidth', int)
        self.crop_height = DataLineEdit(settings, self, 'CropHeight', int)

        self.use_random_x_flip = DataCheckBox(settings, self, 'UseRandomXFlip')
        self.use_random_y_flip = DataCheckBox(settings, self, 'UseRandomYFlip')
        self.use_random_rotate = DataCheckBox(settings, self, 'UseRandomRotation')
        self.pca_lighting = DataLineEdit(settings, self, 'PCAlighting')

        self.dialogs = [('Train data Settings', None),
                        ('Set Train Data', self.train_edit),
                        ('', self.train_edit.label),
                        ('Test data Settings', None),
                        ('Same data with training', self.same_data_check),
                        ('Shuffle', self.shuffle_check),
                        ('Test data ratio', self.ratio_edit),
                        ('Set Test Data', self.test_edit),
                        ('Use Resize', self.use_resize),
                        ('Resize Width', self.resize_width),
                        ('Resize Height', self.resize_height),
                        ('', self.test_edit.label),
                        ('Data Augmentation Settings', None),
                        ('Crop mode', self.crop_edit),
                        ('Crop Width', self.crop_width),
                        ('Crop Height', self.crop_height),
                        ('Use Random X Flip', self.use_random_x_flip),
                        ('Use Random Y Flip', self.use_random_y_flip),
                        ('Use Random Rotation', self.use_random_rotate),
                        ('Use PCA Lighting', self.pca_lighting),
                        ]


class CropEdit(QtWidgets.QComboBox):
    def __init__(self, settings, parent):
        menu = ('Do Nothing', 'Center Crop', 'Random Crop')
        self.parent = parent
        self.settings = settings
        super(CropEdit, self).__init__()
        self.addItems(menu)
        if 'Crop_idx' in TrainParamServer().__dict__:
            self.setCurrentIndex(TrainParamServer()['Crop_idx'])
        else:
            self.setCurrentIndex(settings.value('Crop', type=int))
        TrainParamServer()['Crop'] = self.currentText()

    def commit(self):
        self.settings.setValue('Crop', self.currentIndex())
        TrainParamServer()['Crop'] = self.currentText()
        TrainParamServer()['Crop_idx'] = self.currentIndex()


class PreviewWidget(QtWidgets.QWidget):

    def __init__(self, image_file, *args, **kwargs):
        super(PreviewWidget, self).__init__()
        self.setStyleSheet('''ReportWidget{background: rgb(55,55,55)}
        ''')
        self.pixmap = None
        self.image_idx = 0
        self.update()

    def paintEvent(self, event):
        # TODO augmentation
        self.pixmap = QtGui.QPixmap(self.image_file)
        size = self.size()
        painter = QtGui.QPainter(self)
        point = QtCore.QPoint(0, 0)

        # start painting the label from left upper corner
        # point.setX((size.width() - scaled_pix.width()) / 2)
        # point.setY((size.height() - scaled_pix.height()) / 2)
        painter.drawPixmap(point, self.pixmap)

    def update(self):
        self.image_file = glob.glob(TrainParamServer()['TrainData'] + '.jpg')[self.image_idx]
        self.image_idx += 1


class DataDirEdit(QtWidgets.QPushButton):
    def __init__(self, settings, parent, key):
        self.parent = parent
        self.settings = settings
        super(DataFileEdit, self).__init__('Browse')
        v = settings.value(key, type=str)
        v = v if v else './'
        if key in TrainParamServer().__dict__:
            self.value = TrainParamServer()[key]
        else:
            self.value = v
            TrainParamServer()[key] = v
        self.key = key
        self.label = DataFileLabel(settings, parent, key)
        self.label.setText(self.value)
        self.clicked.connect(self.open_dialog)

    def commit(self):
        self.settings.setValue(self.key, self.value)
        TrainParamServer()[self.key] = self.value

    def open_dialog(self):
        init_path = TrainParamServer().get_work_dir()
        data_dir = QtWidgets.QFileDialog.getExistingDirectory(self,
        'Select Directory', init_path)
        if data_dir:
            self.value = data_dir
            self.label.setText(self.value)
            self.parent.state_changed(0)
