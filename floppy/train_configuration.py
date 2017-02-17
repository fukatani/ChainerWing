from PyQt5.QtWidgets import *
from floppy.settings import AbstractEdit
from floppy.settings import ParamServer

class TrainDialog(QDialog):
    def __init__(self, *args, settings=None):
        self.settings= settings
        self.dialogs = [('Train Settings', None),
                        ('Batch Size', BatchSizeEdit(settings, self)),
                        ('Epoch', EpochEdit(settings, self)),
                        ('GPU', GPUEdit(settings, self)),
                        ('Optimizer', OptimizerEdit(settings, self)),
                        ]
        super(TrainDialog, self).__init__(*args)
        self.setStyleSheet('''TrainDialog {
                                background: rgb(75,75,75);
                            }
                            QLineEdit {
                                background-color: rgb(195,95,95);
                                border: 1px solid gray;
                                color: white;
                            }
                            QSpinBox {
                                background-color: rgb(95,95,95);
                                color: white;
                                border: 1px solid gray;
                            }
                            QPushButton {
                                background-color: rgb(95,95,95);
                                color: white;
                            }
                            QLabel {
                                color: white;
                            }
        ''')
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
