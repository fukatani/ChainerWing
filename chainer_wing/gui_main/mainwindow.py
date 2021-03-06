# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'chainer_wing/resources/mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.4
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtWidgets

from chainer_wing.node_lib import NodeList, NodeFilter
from chainer_wing.subwindows.report_widget import ReportWidget


class Ui_MainWindow(object):
    def setupUi(self, main_window):
        main_window.setObjectName("MainWindow")
        main_window.setStyleSheet(
            '''MainWindow { background-color: rgb(95,95,95); border-color: black }''')
        main_window.resize(1250, 629)
        self.centralWidget = QtWidgets.QWidget(main_window)
        self.centralWidget.setObjectName("centralWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralWidget)
        self.gridLayout.setObjectName("gridLayout")
        self.HorizontalSplitter = QtWidgets.QSplitter(self.centralWidget)
        self.HorizontalSplitter.setStyleSheet(
            "QSplitter::handle{background: rgb(85,85,85);}")
        self.HorizontalSplitter.setOrientation(QtCore.Qt.Horizontal)
        self.HorizontalSplitter.setObjectName("HorizontalSplitter")
        self.DrawArea = QtWidgets.QWidget(self.HorizontalSplitter)
        self.DrawArea.setObjectName("DrawArea")
        self.RightContainer = QtWidgets.QWidget(self.HorizontalSplitter)
        self.RightContainer.setEnabled(True)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                            QtWidgets.QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(
            self.RightContainer.sizePolicy().hasHeightForWidth())
        self.RightContainer.setSizePolicy(size_policy)
        self.RightContainer.setMaximumSize(QtCore.QSize(450, 16777215))
        self.RightContainer.setBaseSize(QtCore.QSize(0, 0))
        self.RightContainer.setObjectName("RightContainer")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.RightContainer)
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.VerticalSplitter = QtWidgets.QSplitter(self.RightContainer)
        self.VerticalSplitter.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.VerticalSplitter.setOrientation(QtCore.Qt.Vertical)
        self.VerticalSplitter.setObjectName("VerticalSplitter")
        self.TopContainer = QtWidgets.QWidget(self.VerticalSplitter)
        self.TopContainer.setObjectName("TopContainer")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.TopContainer)
        self.gridLayout_3.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.TopLayout = QtWidgets.QVBoxLayout()
        self.TopLayout.setObjectName("TopLayout")
        # self.FilterEdit = QtWidgets.QLineEdit(self.TopContainer)
        self.FilterEdit = NodeFilter(self.TopContainer)
        self.FilterEdit.setObjectName("FilterEdit")
        self.TopLayout.addWidget(self.FilterEdit)
        # self.NodeListView = QtWidgets.QListView(self.TopContainer)
        self.NodeListView = NodeList(self.TopContainer)
        self.NodeListView.setObjectName("NodeListView")
        self.TopLayout.addWidget(self.NodeListView)
        self.gridLayout_3.addLayout(self.TopLayout, 0, 0, 1, 1)
        # self.BottomWidget = QtWidgets.QWidget(self.VerticalSplitter)
        self.BottomWidget = ReportWidget(self.VerticalSplitter)
        self.BottomWidget.setObjectName("BottomWidget")
        self.gridLayout_2.addWidget(self.VerticalSplitter, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.HorizontalSplitter, 0, 0, 1, 1)
        main_window.setCentralWidget(self.centralWidget)
        self.menuBar = QtWidgets.QMenuBar(main_window)
        self.menuBar.setStyleSheet('''QMenuBar{background: rgb(75,75,75); border-color: black}

        QMenuBar::item {spacing: 3px; padding: 1px 4px;background: transparent; border-radius: 4px; color: white}
        QMenuBar::item:selected { /* when selected using mouse or keyboard */
        background: #a8a8a8;}

        QMenu {
        background-color: rgb(95,95,95); /* sets background of the menu */
        border: 1px solid black;
        }

        QMenu::item {
        /* sets background of menu item. set this to something non-transparent
        if you want menu color and menu item color to be different */
        background-color: transparent;
        color: white;
        }

        QMenu::item:selected { /* when user selects item using mouse or keyboard */
        background-color: rgb(0,85,100);
        }
        ''')
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 1250, 21))
        self.menuBar.setObjectName("menuBar")
        main_window.setMenuBar(self.menuBar)
        self.mainToolBar = QtWidgets.QToolBar(main_window)
        self.mainToolBar.setStyleSheet('''
        QToolBar {background: rgb(75,75,75); border:1px solid rgb(55,55,55)}
        QToolButton { color: white }
        QPushButton {
            background-color: rgb(155,95,95);
            color: white;
        }
        ''')
        self.mainToolBar.setObjectName("mainToolBar")
        main_window.addToolBar(QtCore.Qt.TopToolBarArea, self.mainToolBar)
        self.statusBar = QtWidgets.QStatusBar(main_window)
        self.statusBar.setObjectName("statusBar")
        main_window.setStatusBar(self.statusBar)

        self.retranslateUi(main_window)
        QtCore.QMetaObject.connectSlotsByName(main_window)

    def retranslateUi(self, main_window):
        _translate = QtCore.QCoreApplication.translate
        main_window.setWindowTitle(_translate("MainWindow", "MainWindow"))
