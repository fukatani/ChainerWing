from PyQt5 import QtWidgets

from chainer_wing.subwindows.train_config import TrainParamServer


class AbstractDataDialog(QtWidgets.QDialog):
    def __init__(self, *args, settings=None):
        self.settings = settings
        self.configure_window()

        super(AbstractDataDialog, self).__init__(*args)
        self.setStyleSheet('''DataDialog {
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
        self.state_changed(0)

    def configure_window(self):
        raise NotImplementedError()

    def close(self):
        for name, widget in self.dialogs:
            try:
                widget.commit()
            except AttributeError:
                pass
        self.settings.sync()
        self.parent().update_data_label()
        super(AbstractDataDialog, self).close()

    def redraw(self):
        self.parent().drawer.repaint()

    def state_changed(self, _):
        if self.train_edit.python_selected():
            self.same_data_check.setDisabled(True)
            self.ratio_edit.setDisabled(True)
            self.test_edit.setDisabled(True)
            self.shuffle_check.setDisabled(True)
        else:
            self.same_data_check.setDisabled(False)
        if self.same_data_check.isChecked():
            self.ratio_edit.setDisabled(False)
            self.test_edit.setDisabled(True)
            self.shuffle_check.setDisabled(False)
        else:
            self.ratio_edit.setDisabled(True)
            self.test_edit.setDisabled(False)
            self.shuffle_check.setDisabled(True)


class DataDialog(AbstractDataDialog):
    def configure_window(self):
        settings = self.settings
        self.train_edit = DataFileEdit(settings, self, 'TrainData')
        self.test_edit = DataFileEdit(settings, self, 'TestData')
        self.same_data_check = DataCheckBox(settings, self, 'UseSameData')
        self.same_data_check.stateChanged.connect(self.state_changed)
        self.shuffle_check = DataCheckBox(settings, self, 'Shuffle')
        self.ratio_edit = DataLineEdit(settings, self, 'TestDataRatio')
        self.preprocessor = PreProcessorEdit(settings, self)

        self.dialogs = [('Train data Settings', None),
                        ('Set Train Data', self.train_edit),
                        ('', self.train_edit.label),
                        ('Test data Settings', None),
                        ('Same data with training', self.same_data_check),
                        ('Shuffle', self.shuffle_check),
                        ('Test data ratio', self.ratio_edit),
                        ('Set Test Data', self.test_edit),
                        ('', self.test_edit.label),
                        ('Preprocess', None),
                        ('Preprocessor', self.preprocessor),
                        ]


class DataFileEdit(QtWidgets.QPushButton):
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
        data_file = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Select Data File', init_path,
            filter='(*.csv *.npz *.py);; Any (*.*)')[0]
        if data_file:
            self.value = data_file
            self.label.setText(self.value)
            self.parent.state_changed(0)

    def python_selected(self):
        return self.value.endswith('.py')


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
        v = settings.value(key, type=bool)
        if key in TrainParamServer().__dict__:
            v = TrainParamServer()[key]
        else:
            TrainParamServer()[key] = v
        self.setChecked(v)
        TrainParamServer()[key] = self.isChecked()

    def commit(self):
        self.settings.setValue(self.key, self.isChecked())
        TrainParamServer()[self.key] = self.isChecked()


class DataLineEdit(QtWidgets.QLineEdit):
    def __init__(self, settings, parent, key, data_type=float):
        super(DataLineEdit, self).__init__()

        self.parent = parent
        self.settings = settings
        self.data_type = data_type
        self.key = key
        v = settings.value(key, type=data_type)
        v = v if v else 0.5
        if key in TrainParamServer().__dict__:
            v = TrainParamServer()[key]
        else:
            TrainParamServer()[key] = v
        self.setText(str(v))

    def commit(self):
        try:
            value = self.data_type(self.text())
            self.settings.setValue(self.key, value)
            TrainParamServer()[self.key] = value
        except ValueError:
            return


class PreProcessorEdit(QtWidgets.QComboBox):
    def __init__(self, settings, parent):
        menu = ('Do Nothing', 'MinMax Scale')
        self.parent = parent
        self.settings = settings
        super(PreProcessorEdit, self).__init__()
        self.addItems(menu)
        if 'PreProcessor_idx' in TrainParamServer().__dict__:
            self.setCurrentIndex(TrainParamServer()['PreProcessor_idx'])
        else:
            self.setCurrentIndex(settings.value('PreProcessor', type=int))
        TrainParamServer()['PreProcessor'] = self.currentText()

    def commit(self):
        self.settings.setValue('PreProcessor', self.currentIndex())
        TrainParamServer()['PreProcessor'] = self.currentText()
        TrainParamServer()['PreProcessor_idx'] = self.currentIndex()
