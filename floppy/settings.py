from PyQt5.QtWidgets import *


class ParamServer(object):
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
        pass


class SettingsDialog(QDialog):
    def __init__(self, *args, settings=None):
        self.settings= settings
        self.dialogs = [('Node Graph Render Settings', None),
                        ('Node Font Size', FontSizeEdit(settings, self)),
                        ('Node Font Offset', FontOffsetEdit(settings, self)),
                        ('Node Title Font Size', NodeTitleFontSizeEdit(settings, self)),
                        ('Connection Line Width', ConnectionLineWidthEdit(settings, self)),
                        ('Node Width Scale', NodeWidthEdit(settings, self)),
                        ('Pin Size', PinSizeEdit(settings, self)),
                        ('Temporary File Settings', None),
                        ('Work File Directory', WorkFileDirEdit(settings, self)),
                        ('Remote Interpreter Settings', None),
                        ('Frame Rate', RGIFrameRateEdit(settings, self)),
                        ]
        super(SettingsDialog, self).__init__(*args)
        self.setStyleSheet('''SettingsDialog {
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
        super(SettingsDialog, self).close()

    def closeEvent(self, e):
        for name, widget in self.dialogs:
            try:
                widget.commit()
            except AttributeError:
                pass
        self.settings.sync()
        super(SettingsDialog, self).closeEvent(e)

    def redraw(self):
        self.parent().drawer.repaint()


class AbstractEdit(QSpinBox):
    def __init__(self, settings, parent, default, valType=int):
        self.parent = parent
        self.settings = settings
        super(AbstractEdit, self).__init__()
        self.globals_key = self.__class__.__name__[:-4]
        v = settings.value(self.globals_key, type=valType)
        v = v if v else default
        self.setValue(v)
        self.valueChanged.connect(self.redraw)

    def commit(self):
        self.settings.setValue(self.globals_key, self.value())
        ParamServer()[self.globals_key] = self.value()

    def redraw(self):
        ParamServer()[self.globals_key] = self.value()
        self.parent.redraw()


class FontSizeEdit(AbstractEdit):
    def __init__(self, settings, parent):
        super(FontSizeEdit, self).__init__(settings, parent, 8)


class FontOffsetEdit(AbstractEdit):
    def __init__(self, settings, parent):
        super(FontOffsetEdit, self).__init__(settings, parent, 0)
        self.setRange(-10, 10)


class NodeTitleFontSizeEdit(AbstractEdit):
    def __init__(self, settings, parent):
        super(NodeTitleFontSizeEdit, self).__init__(settings, parent, 11)
        self.setRange(1, 20)


class ConnectionLineWidthEdit(AbstractEdit):
    def __init__(self, settings, parent):
        super(ConnectionLineWidthEdit, self).__init__(settings, parent, 2)
        self.setRange(1, 20)


class NodeWidthEdit(AbstractEdit):
    def __init__(self, settings, parent):
        super(NodeWidthEdit, self).__init__(settings, parent, 100)
        self.setRange(50, 250)


class PinSizeEdit(AbstractEdit):
    def __init__(self, settings, parent):
        super(PinSizeEdit, self).__init__(settings, parent, 8)
        self.setRange(1, 25)


class WorkFileDirEdit(QPushButton):
    def __init__(self, settings,  parent):
        self.parent = parent
        self.settings = settings
        super(WorkFileDirEdit, self).__init__('Browse')
        v = settings.value('WorkDir', type=str)
        v = v if v else './'
        self.value = v
        self.clicked.connect(self.openDialog)

    def commit(self):
        self.settings.setValue('WorkDir', self.value)

    def openDialog(self):
        dirName = QFileDialog.getExistingDirectory(self, 'Temporary file storage', self.value)
        self.value = dirName


class RGIFrameRateEdit(QLineEdit):
    def __init__(self, settings, parent):
        self.parent = parent
        self.settings = settings
        super(RGIFrameRateEdit, self).__init__()
        v = settings.value('FrameRate', type=float)
        v = v if v else .1
        self.setText(str(v))

    def commit(self):
        self.settings.setValue('FrameRate', float(self.text()))
