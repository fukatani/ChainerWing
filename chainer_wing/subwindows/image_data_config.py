import glob

import chainercv.utils
import PIL.Image
from PyQt5 import QtWidgets
from PyQt5 import QtGui

from chainer_wing.subwindows.train_config import TrainParamServer
from chainer_wing.subwindows.data_config import AbstractDataDialog
from chainer_wing.subwindows.data_config import DataCheckBox
from chainer_wing.subwindows.data_config import DataFileLabel
from chainer_wing.subwindows.data_config import DataLineEdit
from chainer_wing.extension.image_dataset import augment_data
from chainer_wing import util


class ImageDataDialog(AbstractDataDialog):

    def __init__(self, *args, settings=None):
        super(ImageDataDialog, self).__init__(*args, settings=settings)
        self.image_idx = 0
        self.setStyleSheet('''ImageDataDialog {
                                        background: rgb(75,75,75);
                                    }
                                    QSpinBox {
                                        background-color: rgb(95,95,95);
                                        color: white;
                                        border: 1px solid gray;
                                    }
                                    QPushButton {
                                        background-color: rgb(155,95,95);
                                    }
                                    QLabel {
                                        color: white;
                                    }
                ''')

    def configure_window(self):
        settings = self.settings
        self.train_edit = DataDirEdit(settings, self, 'TrainData')
        self.test_edit = DataDirEdit(settings, self, 'TestData')
        self.preview_button = QtWidgets.QPushButton('Update')
        self.preview_button.clicked.connect(self.update_preview)

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

        self.preview = QtWidgets.QLabel()

        self.dialogs = [('Train data Settings', None),
                        ('Set Train Data', self.train_edit),
                        ('', self.train_edit.label),
                        ('Test data Settings', None),
                        ('Same data with training', self.same_data_check),
                        ('Shuffle', self.shuffle_check),
                        ('Test data ratio', self.ratio_edit),
                        ('Set Test Data', self.test_edit),
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
                        ('Open Preview', self.preview_button),
                        ('', self.preview)
                        ]

    def update_preview(self):
        self.commit_all()
        image_files = glob.glob(TrainParamServer()['TrainData'] + '/*/*.jpg')
        if not image_files:
            self.image_file = None
            util.disp_error('No image was found in {}.'.format(TrainParamServer()['TrainData']))
            return
        self.image_idx = self.image_idx % len(image_files)
        self.image_file = image_files[self.image_idx]
        image_array = chainercv.utils.read_image_as_array(self.image_file)

        resize_width = TrainParamServer()['ResizeWidth']
        resize_height = TrainParamServer()['ResizeHeight']

        crop_edit = TrainParamServer()['Crop']
        crop_width = TrainParamServer()['CropWidth']
        crop_height = TrainParamServer()['CropHeight']

        use_random_x_flip = TrainParamServer()['UseRandomXFlip']
        use_random_y_flip = TrainParamServer()['UseRandomYFlip']
        use_random_rotate = TrainParamServer()['UseRandomRotation']
        pca_lighting = TrainParamServer()['PCAlighting']

        image_array = augment_data(image_array, resize_width,
                                   resize_height, use_random_x_flip,
                                   use_random_y_flip, use_random_rotate,
                                   pca_lighting, crop_edit, crop_width,
                                   crop_height)

        im = PIL.Image.fromarray(image_array)
        im = im.resize((300, int(300 * image_array.shape[1] / image_array.shape[0])))
        im.save('preview_temp.jpg')

        pixmap = QtGui.QPixmap('preview_temp.jpg')
        self.preview.setPixmap(pixmap)

        self.image_idx += 1


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


class DataDirEdit(QtWidgets.QPushButton):
    def __init__(self, settings, parent, key):
        self.parent = parent
        self.settings = settings
        super(DataDirEdit, self).__init__('Browse')
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

    def python_selected(self):
        return False
