from PyQt5 import QtWidgets


def disp_error(message: str):
    error = QtWidgets.QErrorMessage()
    error.showMessage(message)
    error.exec_()


class AbnormalDataCode(Exception):
    pass


class UnexpectedFileExtension(Exception):
    pass
