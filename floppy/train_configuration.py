from PyQt5.QtWidgets import *
from floppy.settings import AbstractEdit
from floppy.settings import ParamServer

class TrainDialog(QDialog):
    def __init__(self, *args, settings=None):
        self.settings = settings
        self.dialogs = [('Train Settings', None),
                        ('Batch Size', BatchSizeEdit(settings, self)),
                        ('Epoch', EpochEdit(settings, self)),
                        ('GPU', GPUEdit(settings, self)),
                        ('Optimizer', OptimizerEdit(settings, self)),
                        ]
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

    def draw(self, *args, settings=None, opt_params=None):
        if opt_params is not None:
            for key in opt_params:
                self.dialogs.append(key, OptimizeParamEdit(settings, self, key, opt_params[key]))

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
        edit_opt_detail_btn = QPushButton("Edit Opt Parameter")
        edit_opt_detail_btn.clicked.connect(self.edit_opt_param)
        mainLayout.addWidget(edit_opt_detail_btn)
        closeButton = QPushButton('Close')
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

    def closeEvent(self, e):
        for name, widget in self.dialogs:
            try:
                widget.commit()
            except AttributeError:
                pass
        self.settings.sync()
        super(TrainDialog, self).closeEvent(e)

    def redraw(self):
        self.parent().drawer.repaint()

    def edit_opt_param(self, e):
        opt_params = {'learning_rate': 1e-1, 'vvaaabbb': 1e-2}
        self.dialogs = self.dialogs[:5]
        self.draw(self.settings, opt_params=opt_params)


class BatchSizeEdit(AbstractEdit):
    def __init__(self, settings, parent):
        super(BatchSizeEdit, self).__init__(settings, parent, 20)


class EpochEdit(AbstractEdit):
    def __init__(self, settings, parent):
        super(EpochEdit, self).__init__(settings, parent, 0)


class GPUEdit(AbstractEdit):
    def __init__(self, settings, parent):
        super(GPUEdit, self).__init__(settings, parent, 11)


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
        ParamServer()['Optimizer'] = self.text()


class OptimizeParamEdit(AbstractEdit):
    def __init__(self, settings, parent, key, default_value=1):
        super(OptimizeParamEdit, self).__init__(settings, parent, default_value)
        ParamServer()[key] = self.value()
