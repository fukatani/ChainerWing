from PyQt5 import QtWidgets
from chainer_wing import inspector
from chainer_wing import util

import os


class TrainParamServer(object):
    """Singleton parameter server
    """
    __instance = None

    def __new__(cls, *args, **keys):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def __getitem__(cls, key):
        if key in cls.__dict__:
            return cls.__dict__[key]
        else:
            if key == 'IncludingLabel':
                return False
            elif key == 'PredClass':
                return False
            elif key == 'WorkDir':
                return os.path.dirname(__file__) + '../../examples/'
            elif key == 'PreProcessor':
                return 'Do Nothing'
            else:
                raise KeyError(key)

    def __setitem__(cls, key, value):
        cls.__dict__[key] = value

    def __iter__(cls):
        return cls.__dict__.keys()

    def iter_for_opt_params(cls):
        for param in cls.__dict__:
            if param.startswith('opt_'):
                yield param

    def clear_opt_params(cls):
        opt_keys = [key for key in cls.iter_for_opt_params()]
        for key in opt_keys:
            del cls.__dict__[key]

    def to_dict(cls):
        return cls.__dict__

    def load_from_dict(cls, dict):
        cls.__dict__ = dict

    def get_work_dir(cls):
        if not os.path.isdir(cls['WorkDir']):
            cls['WorkDir'] = os.path.dirname(__file__) + '../../examples/'
        return cls['WorkDir']

    def get_net_name(cls):
        return cls.get_work_dir() + '/' + cls['NetName'] + '.py'

    def get_result_dir(cls):
        return cls.get_work_dir() + '/result'

    def get_model_name(cls):
        return cls.get_result_dir() + '/' + cls['ModelName']

    def get_train_data_name(cls):
        final_slash_pos = cls['TrainData'].rfind('/')
        final_dot_pos = cls['TrainData'].rfind('.')
        if final_slash_pos > 0 and final_dot_pos > 0:
            assert final_slash_pos < final_dot_pos
            return cls['TrainData'][final_slash_pos+1:]
        else:
            return ''

    def use_minmax(cls):
        cls['PreProcessor'] == 'MinMax Scale'


class TrainDialog(QtWidgets.QDialog):
    def __init__(self, *args, settings=None):
        self.settings = settings
        work_edit = WorkDirEdit(settings, self)
        opt_edit = OptimizerEdit(settings, self)
        opt_edit.currentTextChanged.connect(self.update_optimizer)
        self.dialogs = [('File Settings', None),
                        ('Working Directory', work_edit),
                        ('', work_edit.label),
                        ('Train Settings', None),
                        ('Task', TaskEdit(settings, self)),
                        ('Net Name', NetNameEdit(settings, self)),
                        ('Model Name', ModelNameEdit(settings, self)),
                        ('Batch Size', BatchSizeEdit(settings, self)),
                        ('Epoch', EpochEdit(settings, self)),
                        ('GPU', GPUEdit(settings, self)),
                        ('Optimizer Settings', None),
                        ('Optimizer', opt_edit),
                        ]
        optimizer_name = TrainParamServer()['Optimizer']
        oi = inspector.OptimizerInspector()
        for name, default in oi.get_signature(optimizer_name).items():
            if name not in TrainParamServer().__dict__:
                TrainParamServer()[name] = default
        for param in TrainParamServer().iter_for_opt_params():
            dialog = (param, OptimizeParamEdit(settings, self, param,
                                               TrainParamServer()[param]))
            self.dialogs.append(dialog)

        super(TrainDialog, self).__init__(*args)
        self.draw(*args, settings=settings)
        self.setStyleSheet('''TrainDialog {
                                background: rgb(75,75,75);
                            }
                            QLineEdit {
                                background-color: rgb(95,95,95);
                                border: 1px solid gray;
                                color: white;
                            }
                            QSpinBox {
                                background-color: rgb(95,95,95);
                                color: white;
                                border: 1px solid gray;
                            }
                            QPushButton {
                                background-color: rgb(155,95,95);
                                color: white;
                            }
                            QLabel {
                                color: white;
                            }
        ''')

    def draw(self, *args, settings=None):
        main_layout = QtWidgets.QVBoxLayout()
        for name, widget in self.dialogs:
            if not widget:
                l_widget = QtWidgets.QGroupBox(name)
                l_widget.setStyleSheet('''
                QGroupBox {
                    color: white;
                    border: 1px solid gray;
                    border-radius: 9px;
                    margin-top: 0.5em;
                }
                QGroupBox::title {
                    color: white;
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 3px 0 3px;
                }
                ''')
                l_widget.setFlat(False)
                section_layout = QtWidgets.QFormLayout()
                l_widget.setLayout(section_layout)
                main_layout.addWidget(l_widget)
            else:
                section_layout.addRow(name, widget)
        close_button = QtWidgets.QPushButton('Apply')
        close_button.clicked.connect(self.close)
        main_layout.addWidget(close_button)
        self.setLayout(main_layout)

    def close(self):
        for name, widget in self.dialogs:
            try:
                widget.commit()
            except AttributeError:
                pass
        self.update_opt_params(TrainParamServer()['Optimizer'])
        self.settings.sync()
        super(TrainDialog, self).close()

    def redraw(self):
        self.parent().drawer.repaint()

    def update_optimizer(self, optimizer_name):
        print(optimizer_name)
        self.update_opt_params(optimizer_name)
        self.parent().open_train_config()
        self.close()

    def update_opt_params(self, optimizer_name):
        TrainParamServer()['Optimizer'] = optimizer_name
        oi = inspector.OptimizerInspector()
        not_exist_names = []
        exist_names = []
        for name in TrainParamServer().iter_for_opt_params():
            if name in oi.get_signature(optimizer_name):
                exist_names.append(name)
            else:
                not_exist_names.append(name)
        for name in not_exist_names:
            del TrainParamServer().__dict__[name]
        for name, default in oi.get_signature(optimizer_name).items():
            if name not in exist_names:
                TrainParamServer()[name] = default


class AbstractTrainEdit(QtWidgets.QSpinBox):
    def __init__(self, settings, parent, default, val_type=int):
        self.parent = parent
        self.settings = settings
        super(AbstractTrainEdit, self).__init__()
        self.globals_key = self.__class__.__name__[:-4]
        v = settings.value(self.globals_key, type=val_type)
        v = v if v else default
        if self.globals_key in TrainParamServer().__dict__:
            v = TrainParamServer()[self.globals_key]
        else:
            TrainParamServer()[self.globals_key] = v
        self.setValue(v)
        self.valueChanged.connect(self.redraw)

    def commit(self):
        self.settings.setValue(self.globals_key, self.value())
        TrainParamServer()[self.globals_key] = self.value()

    def redraw(self):
        TrainParamServer()[self.globals_key] = self.value()
        self.parent.redraw()


class BatchSizeEdit(AbstractTrainEdit):
    def __init__(self, settings, parent):
        super(BatchSizeEdit, self).__init__(settings, parent, 20)


class EpochEdit(AbstractTrainEdit):
    def __init__(self, settings, parent):
        super(EpochEdit, self).__init__(settings, parent, 20)


class GPUEdit(AbstractTrainEdit):
    def __init__(self, settings, parent):
        super(GPUEdit, self).__init__(settings, parent, 0)


class OptimizerEdit(QtWidgets.QComboBox):
    def __init__(self, settings, parent):
        menu = inspector.OptimizerInspector().get_members()
        self.parent = parent
        self.settings = settings
        super(OptimizerEdit, self).__init__()
        self.addItems(menu)
        self.length = len(menu)
        if 'Optimizer' in TrainParamServer().__dict__:
            selected_optimizer = TrainParamServer()['Optimizer']
        else:
            selected_optimizer = settings.value('Optimizer', type=str)
        self.setCurrentText(selected_optimizer)
        TrainParamServer()['Optimizer'] = self.currentText()

    def commit(self):
        self.settings.setValue('Optimizer', self.currentText())
        self.setCurrentText(TrainParamServer()['Optimizer'])


class NetNameEdit(QtWidgets.QLineEdit):
    def __init__(self, settings, parent):
        self.parent = parent
        self.settings = settings
        super(NetNameEdit, self).__init__()
        v = settings.value('NetName', type=str)
        v = v if v else 'MyNet'
        if 'NetName' in TrainParamServer().__dict__:
            v = TrainParamServer()['NetName']
        else:
            TrainParamServer()['NetName'] = v
        self.setText(v)

    def commit(self):
        self.settings.setValue('NetName', self.text())
        TrainParamServer()['NetName'] = self.text()


class ModelNameEdit(QtWidgets.QLineEdit):
    def __init__(self, settings, parent):
        self.parent = parent
        self.settings = settings
        super(ModelNameEdit, self).__init__()
        v = settings.value('ModelName', type=str)
        v = v if v else 'MyModel'
        if 'ModelName' in TrainParamServer().__dict__:
            v = TrainParamServer()['ModelName']
        else:
            TrainParamServer()['ModelName'] = v
        self.setText(v)

    def commit(self):
        self.settings.setValue('ModelName', self.text())
        TrainParamServer()['ModelName'] = self.text()


class OptimizeParamEdit(QtWidgets.QLineEdit):
    def __init__(self, settings, parent, key, value):
        self.parent = parent
        self.settings = settings
        self.key = key
        super(OptimizeParamEdit, self).__init__()
        if key in TrainParamServer().__dict__:
            value = TrainParamServer()[key]
        else:
            TrainParamServer()[key] = value
        self.setText(str(value))

    def commit(self):
        try:
            TrainParamServer()[self.key] = float(self.text())
        except ValueError:
            util.disp_error('Optimizer parameter should be float.')


class WorkDirEdit(QtWidgets.QPushButton):
    def __init__(self, settings, parent):
        self.parent = parent
        self.settings = settings
        super(WorkDirEdit, self).__init__('Browse')
        v = settings.value('WorkDir', type=str)
        v = v if v else './'
        if 'WorkDir' in TrainParamServer().__dict__:
            self.value = TrainParamServer().get_work_dir()
        else:
            self.value = v
            TrainParamServer()['WorkDir'] = self.value

        self.label = WorkDirLabel(settings, parent)
        self.clicked.connect(self.open_dialog)

    def commit(self):
        self.settings.setValue('WorkDir', self.value)
        TrainParamServer()['WorkDir'] = self.value

    def open_dialog(self):
        self.value = QtWidgets.QFileDialog.\
            getExistingDirectory(self,
                                 'Result file storage',
                                 self.value)
        self.label.setText(self.value)
        self.commit()


class WorkDirLabel(QtWidgets.QLabel):
    def __init__(self, settings, parent):
        self.parent = parent
        self.settings = settings
        super(WorkDirLabel, self).__init__(TrainParamServer().get_work_dir())


class TaskEdit(QtWidgets.QComboBox):
    def __init__(self, settings, parent):
        menu = ('Simple Classification', 'Simple Regression')
        # menu = ('Simple Classification', 'Simple Regression',
        #         'Image Classification')
        self.parent = parent
        self.settings = settings
        super(TaskEdit, self).__init__()
        self.addItems(menu)
        if 'Task_idx' in TrainParamServer().__dict__:
            self.setCurrentIndex(TrainParamServer()['Task_idx'])
        else:
            self.setCurrentIndex(settings.value('Task', type=int))
        TrainParamServer()['Task'] = self.currentText()

    def commit(self):
        self.settings.setValue('Task', self.currentIndex())
        TrainParamServer()['Task'] = self.currentText()
        TrainParamServer()['Task_idx'] = self.currentIndex()
