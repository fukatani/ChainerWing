from PyQt5 import QtWidgets

import json
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
        return cls.__dict__[key]

    def __setitem__(cls, key, value):
        cls.__dict__[key] = value

    def __iter__(cls):
        return cls.__dict__.keys()

    def iter_for_opt_params(cls):
        for param in cls.__dict__:
            if param[:4] == 'opt_':
                yield param

    def clear_opt_params(cls):
        opt_keys = [key for key in cls.iter_for_opt_params()]
        for key in opt_keys:
            del cls.__dict__[key]

    def to_dict(cls):
        return cls.__dict__

    def load_from_dict(cls, dict):
        cls.__dict__ = dict

    def get_net_name(cls):
        return cls['WorkDir'] + '/' + cls['NetName'] + '.py'

    def get_result_dir(cls):
        return cls['WorkDir'] + '/result'

    def get_model_name(cls):
        return cls.get_result_dir() + '/' + cls['ModelName']

    def get_train_data_name(cls):
        final_slash_pos = cls['TrainData'].rfind('/')
        final_dot_pos = cls['TrainData'].rfind('.')
        if final_slash_pos > 0 and final_dot_pos > 0:
            assert final_slash_pos < final_dot_pos
            return cls['TrainData'][final_slash_pos+1: final_dot_pos]
        else:
            return ''

    def get_work_dir(cls):
        if 'WorkDir' not in cls.__dict__:
            cls.__dict__['WorkDir'] = os.path.abspath(__file__) + '/../../examples/'
        return cls.__dict__['WorkDir']


class TrainDialog(QtWidgets.QDialog):
    def __init__(self, *args, settings=None):
        self.settings = settings
        work_edit = WorkDirEdit(settings, self)
        self.dialogs = [('File Settings', None),
                        ('Working Directory', work_edit),
                        ('', work_edit.label),
                        ('Train Settings', None),
                        ('TrainModeEdit', TrainModeEdit(settings, self)),
                        ('Net Name', NetNameEdit(settings, self)),
                        ('Model Name', ModelNameEdit(settings, self)),
                        ('Batch Size', BatchSizeEdit(settings, self)),
                        ('Epoch', EpochEdit(settings, self)),
                        ('GPU', GPUEdit(settings, self)),
                        ('Optimizer Settings', None),
                        ('Optimizer', OptimizerEdit(settings, self)),
                        ]
        for param in TrainParamServer().iter_for_opt_params():
            dialog = (param, OptimizeParamEdit(settings, self, param))
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
                # layout.addRow(name)
            else:
                section_layout.addRow(name, widget)
        edit_opt_detail_btn = QtWidgets.QPushButton("Update Optimizer")
        edit_opt_detail_btn.clicked.connect(self.update_optimizer)
        main_layout.addWidget(edit_opt_detail_btn)
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
        self.settings.sync()
        super(TrainDialog, self).close()

    def redraw(self):
        self.parent().drawer.repaint()

    def update_optimizer(self, e):
        # TODO(fukatani): temporal.
        TrainParamServer()['opt_learning_rate'] = 1e-1
        TrainParamServer()['opt_vvaaabbb'] = 1e-2
        self.parent().open_train_config()
        self.close()


class AbstractTrainEdit(QtWidgets.QSpinBox):
    def __init__(self, settings, parent, default, val_type=int):
        self.parent = parent
        self.settings = settings
        super(AbstractTrainEdit, self).__init__()
        self.globals_key = self.__class__.__name__[:-4]
        v = settings.value(self.globals_key, type=val_type)
        v = v if v else default
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


class OptimizerEdit(QtWidgets.QLineEdit):
    def __init__(self, settings, parent):
        self.parent = parent
        self.settings = settings
        super(OptimizerEdit, self).__init__()
        v = settings.value('Optimizer', type=str)
        v = v if v else 'AdaDelta'
        self.setText(v)

    def commit(self):
        self.settings.setValue('Optimizer', self.text())
        TrainParamServer()['Optimizer'] = self.text()


class NetNameEdit(QtWidgets.QLineEdit):
    def __init__(self, settings, parent):
        self.parent = parent
        self.settings = settings
        super(NetNameEdit, self).__init__()
        v = settings.value('NetName', type=str)
        v = v if v else 'MyNet'
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
        self.setText(v)
        TrainParamServer()['ModelName'] = self.text()

    def commit(self):
        self.settings.setValue('ModelName', self.text())
        TrainParamServer()['ModelName'] = self.text()


class OptimizeParamEdit(AbstractTrainEdit):
    def __init__(self, settings, parent, key, default_value=1):
        super(OptimizeParamEdit, self).__init__(settings, parent, default_value)
        TrainParamServer()[key] = self.value()


class WorkDirEdit(QtWidgets.QPushButton):
    def __init__(self, settings, parent):
        self.parent = parent
        self.settings = settings
        super(WorkDirEdit, self).__init__('Browse')
        v = settings.value('WorkDir', type=str)
        v = v if v else './'
        self.value = v
        self.clicked.connect(self.open_dialog)
        TrainParamServer()['WorkDir'] = self.value
        self.label = WorkDirLabel(settings, parent)

    def commit(self):
        self.settings.setValue('WorkDir', self.value)
        TrainParamServer()['WorkDir'] = self.value

    def open_dialog(self):
        self.value = QtWidgets.QFileDialog.\
            getExistingDirectory(self,
                                 'Result file storage',
                                 self.value)
        self.label.setText(self.value)


class WorkDirLabel(QtWidgets.QLabel):
    def __init__(self, settings, parent):
        self.parent = parent
        self.settings = settings
        super(WorkDirLabel, self).__init__(TrainParamServer()['WorkDir'])


class TrainModeEdit(QtWidgets.QComboBox):
    def __init__(self, settings, parent):
        menu = ('Simple Classification', 'Simple Regression')
        self.parent = parent
        self.settings = settings
        super(TrainModeEdit, self).__init__()
        self.addItems(menu)
        v = settings.value('TrainMode', type=str)
        v = v if v else 'Simple Classification'
        self.value = v
        TrainParamServer()['TrainMode'] = self.value

    def commit(self):
        self.settings.setValue('TrainMode', self.value)
        TrainParamServer()['TrainMode'] = self.value
