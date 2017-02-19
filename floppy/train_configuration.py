from PyQt5.QtWidgets import *
import json


class TrainParamServer(object):
    '''Singleton parameter server
    '''
    __instance = None

    def __new__(cls, *args, **keys):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def __getitem__(cls, key):
        return cls.__dict__[key]

    def __setitem__(cls, key, value):
        cls.__dict__[key] = value

    def iter_for_opt_params(cls):
        for param in cls.__dict__:
            if param[:4] == 'opt_':
                yield param

    def clear_opt_params(cls):
        opt_keys = [key for key in cls.iter_for_opt_params()]
        for key in opt_keys:
            del cls.__dict__[key]

    def save(cls, fp):
        train_state = json.dumps(cls.__dict__, sort_keys=True)
        fp.write(train_state)

    def from_json(cls, line):
        json.loads(line)


class TrainDialog(QDialog):
    def __init__(self, *args, settings=None):
        self.settings = settings
        self.dialogs = [('Train Settings', None),
                        ('Net Name', NetNameEdit(settings, self)),
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
        mainLayout = QVBoxLayout()
        for name, widget in self.dialogs:
            if not widget:
                lWidget = QGroupBox(name)
                lWidget.setStyleSheet('''
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
                lWidget.setFlat(False)
                sectionLayout = QFormLayout()
                lWidget.setLayout(sectionLayout)
                mainLayout.addWidget(lWidget)
                # layout.addRow(name)
            else:
                sectionLayout.addRow(name, widget)
        edit_opt_detail_btn = QPushButton("Update Optimizer")
        edit_opt_detail_btn.clicked.connect(self.update_optimizer)
        mainLayout.addWidget(edit_opt_detail_btn)
        closeButton = QPushButton('Apply')
        closeButton.clicked.connect(self.close)
        mainLayout.addWidget(closeButton)
        self.setLayout(mainLayout)

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
        #TODO(fukatani): temporal.
        TrainParamServer()['opt_learning_rate'] = 1e-1
        TrainParamServer()['opt_vvaaabbb'] = 1e-2
        self.parent().open_train_config()
        self.close()


class AbstractTrainEdit(QSpinBox):
    def __init__(self, settings, parent, default, valType=int):
        self.parent = parent
        self.settings = settings
        super(AbstractTrainEdit, self).__init__()
        self.globals_key = self.__class__.__name__[:-4]
        v = settings.value(self.globals_key, type=valType)
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
        super(GPUEdit, self).__init__(settings, parent, -1)


class OptimizerEdit(QLineEdit):
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


class NetNameEdit(QLineEdit):
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


class OptimizeParamEdit(AbstractTrainEdit):
    def __init__(self, settings, parent, key, default_value=1):
        super(OptimizeParamEdit, self).__init__(settings, parent, default_value)
        TrainParamServer()[key] = self.value()
