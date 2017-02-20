from PyQt5.QtWidgets import *


class SettingsDialog(QDialog):
    def __init__(self, *args, settings=None):
        self.settings = settings
        self.dialogs = [('Node Graph Render Settings', None),
                        ('Node Font Size', FontSizeEdit(settings, self)),
                        ('Node Font Offset', FontOffsetEdit(settings, self)),
                        ('Node Title Font Size',
                         NodeTitleFontSizeEdit(settings, self)),
                        ('Connection Line Width',
                         ConnectionLineWidthEdit(settings, self)),
                        ('Node Width Scale', NodeWidthEdit(settings, self)),
                        ('Pin Size', PinSizeEdit(settings, self)),
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
        super(SettingsDialog, self).close()

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

    def redraw(self):
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
