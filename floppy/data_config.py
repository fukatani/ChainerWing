from floppy.train_config import TrainParamServer

from PyQt5 import QtWidgets


class DataDialog(QtWidgets.QDialog):
    def __init__(self, *args, settings=None):
        self.settings = settings
        train_edit = DataFileEdit(settings, self, 'TrainData')
        test_edit = DataFileEdit(settings, self, 'TrainData')
        self.dialogs = [('Train data Settings', None),
                        ('Set Train Data', train_edit),
                        ('', train_edit.label),
                        ('Test data Settings', None),
                        ('Same data with training',
                         DataCheckBox(settings, self, 'UseSameData')),
                        ('Shuffle',
                         DataCheckBox(settings, self, 'Shuffle')),
                        ('Test data ratio',
                         DataLineEdit(settings, self, 'TestDataRatio')),
                        ('Set Test Data', test_edit),
                        ('', test_edit.label),
                        ]
        super(DataDialog, self).__init__(*args)
        self.setStyleSheet('''DataDialog {
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
        self.resize(300, 300)

    def close(self):
        for name, widget in self.dialogs:
            try:
                widget.commit()
            except AttributeError:
                pass
        self.settings.sync()
        super(DataDialog, self).close()

    def redraw(self):
        self.parent().drawer.repaint()


class DataFileEdit(QtWidgets.QPushButton):
    def __init__(self, settings, parent, key):
        self.parent = parent
        self.settings = settings
        super(DataFileEdit, self).__init__('Browse')
        v = settings.value(key, type=str)
        v = v if v else './'
        self.value = v
        self.clicked.connect(self.open_dialog)
        self.key = key
        TrainParamServer()[self.key] = self.value
        self.label = DataFileLabel(settings, parent, key)

    def commit(self):
        self.settings.setValue(self.key, self.value)
        TrainParamServer()[self.key] = self.value

    def open_dialog(self):
        init_path = TrainParamServer().get_data_dir()
        data_file = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Select data File', init_path,
            filter='(*.csv, *.npz, *.py);; Any (*.*)')[0]
        if data_file:
            self.value = data_file
            self.label.setText(self.value)


class DataFileLabel(QtWidgets.QLabel):
    def __init__(self, settings, parent, key):
        self.parent = parent
        self.settings = settings
        super(DataFileLabel, self).__init__(TrainParamServer()[key])


class DataCheckBox(QtWidgets.QCheckBox):
    def __init__(self, settings, parent, key):
        self.parent = parent
        self.settings = settings
        super(DataCheckBox, self).__init__()
        self.key = key
        v = settings.value(key, type=str)
        self.value = v
        TrainParamServer()[key] = self.value

    def commit(self):
        self.settings.setValue(self.key, self.value)
        TrainParamServer()[self.key] = self.value


class DataLineEdit(QtWidgets.QLineEdit):
    def __init__(self, settings, parent, key):
        self.parent = parent
        self.settings = settings
        super(DataLineEdit, self).__init__()
        self.key = key
        v = settings.value(key, type=float)
        v = v if v else 0.5
        self.setText(str(v))

    def commit(self):
        try:
            value = float(self.text())
            self.settings.setValue(self.key, value)
            TrainParamServer()[self.key] = value
        except ValueError:
            return
