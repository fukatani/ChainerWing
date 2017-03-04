# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'prediction.ui'
#
# Created by: PyQt5 UI code generator 5.7.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_PredictionWindow(object):
    def setupUi(self, PredictionWindow):
        PredictionWindow.setObjectName("PredictionWindow")
        PredictionWindow.resize(1250, 629)
        PredictionWindow.setMinimumSize(QtCore.QSize(300, 300))
        self.prediction_widget = QtWidgets.QWidget(PredictionWindow)
        self.prediction_widget.setObjectName("prediction_widget")
        self.gridLayout = QtWidgets.QGridLayout(self.prediction_widget)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout()
        self.verticalLayout_5.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.verticalLayout_5.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_5.setSpacing(6)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.label = QtWidgets.QLabel(self.prediction_widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName("label")
        self.verticalLayout_5.addWidget(self.label)
        self.max_disp_rows = QtWidgets.QSpinBox(self.prediction_widget)
        self.max_disp_rows.setObjectName("max_disp_rows")
        self.verticalLayout_5.addWidget(self.max_disp_rows)
        self.result_table = QtWidgets.QTableView(self.prediction_widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.result_table.sizePolicy().hasHeightForWidth())
        self.result_table.setSizePolicy(sizePolicy)
        self.result_table.setMinimumSize(QtCore.QSize(2, 2))
        self.result_table.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.result_table.setObjectName("result_table")
        self.verticalLayout_5.addWidget(self.result_table)
        self.gridLayout.addLayout(self.verticalLayout_5, 0, 2, 1, 1)
        self.verticalLayout_6 = QtWidgets.QVBoxLayout()
        self.verticalLayout_6.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.verticalLayout_6.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_6.setSpacing(6)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_5 = QtWidgets.QLabel(self.prediction_widget)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout.addWidget(self.label_5)
        self.model_sel_button = QtWidgets.QPushButton(self.prediction_widget)
        self.model_sel_button.setObjectName("model_sel_button")
        self.horizontalLayout.addWidget(self.model_sel_button)
        self.verticalLayout_6.addLayout(self.horizontalLayout)
        self.model_name = QtWidgets.QLabel(self.prediction_widget)
        self.model_name.setObjectName("model_name")
        self.verticalLayout_6.addWidget(self.model_name)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_2.setSpacing(6)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_6 = QtWidgets.QLabel(self.prediction_widget)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_2.addWidget(self.label_6)
        self.input_sel_button = QtWidgets.QPushButton(self.prediction_widget)
        self.input_sel_button.setObjectName("input_sel_button")
        self.horizontalLayout_2.addWidget(self.input_sel_button)
        self.verticalLayout_6.addLayout(self.horizontalLayout_2)
        self.input_data_name = QtWidgets.QLabel(self.prediction_widget)
        self.input_data_name.setObjectName("input_data_name")
        self.verticalLayout_6.addWidget(self.input_data_name)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_3.setSpacing(6)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_7 = QtWidgets.QLabel(self.prediction_widget)
        self.label_7.setObjectName("label_7")
        self.horizontalLayout_3.addWidget(self.label_7)
        self.output_sel_button = QtWidgets.QPushButton(self.prediction_widget)
        self.output_sel_button.setObjectName("output_sel_button")
        self.horizontalLayout_3.addWidget(self.output_sel_button)
        self.verticalLayout_6.addLayout(self.horizontalLayout_3)
        self.output_name = QtWidgets.QLabel(self.prediction_widget)
        self.output_name.setObjectName("output_name")
        self.verticalLayout_6.addWidget(self.output_name)
        self.gridLayout.addLayout(self.verticalLayout_6, 0, 0, 1, 1)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName("verticalLayout")
        self.exe_button = QtWidgets.QToolButton(self.prediction_widget)
        self.exe_button.setObjectName("exe_button")
        self.verticalLayout.addWidget(self.exe_button)
        self.gridLayout.addLayout(self.verticalLayout, 0, 1, 1, 1)
        PredictionWindow.setCentralWidget(self.prediction_widget)
        self.menuBar = QtWidgets.QMenuBar(PredictionWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 1250, 25))
        self.menuBar.setObjectName("menuBar")
        PredictionWindow.setMenuBar(self.menuBar)
        self.toolBar = QtWidgets.QToolBar(PredictionWindow)
        self.toolBar.setObjectName("toolBar")
        PredictionWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)

        self.retranslateUi(PredictionWindow)
        QtCore.QMetaObject.connectSlotsByName(PredictionWindow)

    def retranslateUi(self, PredictionWindow):
        _translate = QtCore.QCoreApplication.translate
        PredictionWindow.setWindowTitle(_translate("PredictionWindow", "Do Prediction"))
        self.label.setText(_translate("PredictionWindow", "Max display rows:"))
        self.label_5.setText(_translate("PredictionWindow", "Prediction Model"))
        self.model_sel_button.setText(_translate("PredictionWindow", "Browse"))
        self.model_name.setText(_translate("PredictionWindow", "TextLabel"))
        self.label_6.setText(_translate("PredictionWindow", "Input Data"))
        self.input_sel_button.setText(_translate("PredictionWindow", "Browse"))
        self.input_data_name.setText(_translate("PredictionWindow", "TextLabel"))
        self.label_7.setText(_translate("PredictionWindow", "Output File"))
        self.output_sel_button.setText(_translate("PredictionWindow", "Browse"))
        self.output_name.setText(_translate("PredictionWindow", "TextLabel"))
        self.exe_button.setText(_translate("PredictionWindow", "..."))
        self.toolBar.setWindowTitle(_translate("PredictionWindow", "toolBar"))

