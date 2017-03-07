from PyQt5 import QtWidgets


def disp_error(message: str):
    error = QtWidgets.QErrorMessage()
    error.showMessage(message)
    error.exec_()


class AbnormalCode(Exception):
    pass
