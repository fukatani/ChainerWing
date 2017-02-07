from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QPoint, QSettings

class SettingsDialog(QDialog):
    def __init__(self, *args, settings=None, globals=None):
        self.globals = globals
        self.settings= settings
        self.dialogs = [('Network Settings', None),
                        ('Default Connection', DefaultConnectionEdit(settings, globals, self)),
                        ('Local Interpreter Port', LocalInterpreterPortEdit(settings, globals, self)),
                        ('Node Graph Render Settings', None),
                        ('Node Font Size', FontSizeEdit(settings, globals, self)),
                        ('Node Font Offset', FontOffsetEdit(settings, globals, self)),
                        ('Node Title Font Size', TitleFontSizeEdit(settings, globals, self)),
                        ('Connection Line Width', ConnectionLineWidthEdit(settings, globals, self)),
                        ('Node Width Scale', NodeWidthEdit(settings, globals, self)),
                        ('Pin Size', PinSizeEdit(settings, globals, self)),
                        ('Temporary File Settings', None),
                        ('Work File Directory', WorkFileDirEdit(settings, globals, self)),
                        ('Remote Interpreter Settings', None),
                        ('Frame Rate', RGIFrameRateEdit(settings, globals, self)),
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
        # self.parent().drawer.update()
        # print('xxxx')


class DefaultConnectionEdit(QLineEdit):
    def __init__(self, settings, globals, parent):
        self.parent = parent
        self.globals = globals
        self.settings = settings
        super(DefaultConnectionEdit, self).__init__()
        v = settings.value('DefaultConnection', type=str)
        v = v if v else '127.0.0.1:7234'
        self.setText(v)

    def commit(self):
        self.settings.setValue('DefaultConnection', self.text())


class FontSizeEdit(QSpinBox):
    def __init__(self, settings, globals, parent):
        self.parent = parent
        self.globals = globals
        self.settings = settings
        super(FontSizeEdit, self).__init__()
        v = settings.value('NodeFontSize', type=int)
        v = v if v else 8
        self.setValue(v)
        self.valueChanged.connect(self.redraw)

    def commit(self):
        self.settings.setValue('NodeFontSize', self.value())
        self.globals['LINEEDITFONTSIZE'] = self.value()

    def redraw(self):
        self.globals['LINEEDITFONTSIZE'] = self.value()
        self.parent.redraw()


class FontOffsetEdit(QSpinBox):
    def __init__(self, settings, globals, parent):
        self.parent = parent
        self.globals = globals
        self.settings = settings
        super(FontOffsetEdit, self).__init__()
        v = settings.value('NodeFontOffset', type=int)
        v = v if v else 0
        self.setRange(-10, 10)
        self.setValue(v)
        self.valueChanged.connect(self.redraw)

    def commit(self):
        self.settings.setValue('NodeFontOffset', self.value())
        self.globals['TEXTYOFFSET'] = self.value()

    def redraw(self):
        self.globals['TEXTYOFFSET'] = self.value()
        self.parent.redraw()


class TitleFontSizeEdit(QSpinBox):
    def __init__(self, settings, globals, parent):
        self.parent = parent
        self.globals = globals
        self.settings = settings
        super(TitleFontSizeEdit, self).__init__()
        v = settings.value('TitleFontSize', type=int)
        v = v if v else 11
        self.setRange(1, 20)
        self.setValue(v)
        self.valueChanged.connect(self.redraw)

    def commit(self):
        self.settings.setValue('TitleFontSize', self.value())
        self.globals['NODETITLEFONTSIZE'] = self.value()

    def redraw(self):
        self.globals['NODETITLEFONTSIZE'] = self.value()
        self.parent.redraw()


class ConnectionLineWidthEdit(QSpinBox):
    def __init__(self, settings, globals, parent):
        self.parent = parent
        self.globals = globals
        self.settings = settings
        super(ConnectionLineWidthEdit, self).__init__()
        v = settings.value('ConnectionLineWidth', type=int)
        v = v if v else 2
        self.setRange(1, 20)
        self.setValue(v)
        self.valueChanged.connect(self.redraw)

    def commit(self):
        self.settings.setValue('ConnectionLineWidth', self.value())
        self.globals['CONNECTIONLINEWIDTH'] = self.value()

    def redraw(self):
        self.globals['CONNECTIONLINEWIDTH'] = self.value()
        self.parent.redraw()


class NodeWidthEdit(QSpinBox):
    def __init__(self, settings, globals, parent):
        self.parent = parent
        self.globals = globals
        self.settings = settings
        super(NodeWidthEdit, self).__init__()
        v = settings.value('NodeWidthScale', type=int)
        v = v if v else 100
        self.setRange(50, 250)
        self.setValue(v)
        self.valueChanged.connect(self.redraw)

    def commit(self):
        self.settings.setValue('NodeWidthScale', self.value())
        self.globals['NODEWIDTHSCALE'] = self.value()

    def redraw(self):
        self.globals['NODEWIDTHSCALE'] = self.value()
        self.parent.redraw()


class PinSizeEdit(QSpinBox):
    def __init__(self, settings, globals, parent):
        self.parent = parent
        self.globals = globals
        self.settings = settings
        super(PinSizeEdit, self).__init__()
        v = settings.value('PinSize', type=int)
        v = v if v else 8
        self.setRange(1, 25)
        self.setValue(v)
        self.valueChanged.connect(self.redraw)

    def commit(self):
        self.settings.setValue('PinSize', self.value())
        self.globals['PINSIZE'] = self.value()

    def redraw(self):
        self.globals['PINSIZE'] = self.value()
        self.parent.redraw()


class WorkFileDirEdit(QPushButton):
    def __init__(self, settings, globals, parent):
        self.parent = parent
        self.globals = globals
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


class LocalInterpreterPortEdit(QSpinBox):
    def __init__(self, settings, globals, parent):
        self.parent = parent
        self.globals = globals
        self.settings = settings
        super(LocalInterpreterPortEdit, self).__init__()
        v = settings.value('LocalPort', type=int)
        v = v if v else 8080
        self.setRange(1, 99999)
        self.setValue(v)

    def commit(self):
        self.settings.setValue('LocalPort', self.value())
        self.globals['LOCALPORT'] = self.value()


class RGIFrameRateEdit(QLineEdit):
    def __init__(self, settings, globals, parent):
        self.parent = parent
        self.globals = globals
        self.settings = settings
        super(RGIFrameRateEdit, self).__init__()
        v = settings.value('FrameRate', type=float)
        v = v if v else .1
        self.setText(str(v))

    def commit(self):
        self.settings.setValue('FrameRate', float(self.text()))