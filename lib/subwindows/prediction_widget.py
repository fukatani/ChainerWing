import os

from chainer.utils import type_check
import numpy

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from lib.subwindows.prediction import Ui_PredictionWindow
from lib.subwindows.train_config import TrainParamServer
from lib.runner import PredictionRunner
from lib import util


class PredictionWindow(QtWidgets.QMainWindow, Ui_PredictionWindow):
    def __init__(self, *args, settings=None):
        self.settings = settings
        super(PredictionWindow, self).__init__(*args)
        self.setupUi(self)

        self.input_sel_button.clicked.connect(self.set_input)
        self.input_config = PredInputDataConfig(self.input_data_name, self)
        self.output_sel_button.clicked.connect(self.set_output)
        self.output_config = PredOutputDataConfig(self.output_name, self)
        self.model_sel_button.clicked.connect(self.set_model)
        self.model_config = PredModelConfig(self.model_name, self)

        self.exe_button.clicked.connect(self.exe_prediction)
        self.including_label.stateChanged.connect(self.set_including_label)
        if 'IncludingLabel' in TrainParamServer().__dict__:
            self.including_label.setChecked(TrainParamServer()['IncludingLabel'])
        if 'PredClass' in TrainParamServer().__dict__:
            self.classification.setChecked(TrainParamServer()['PredClass'])

    def set_input(self):
        self.input_config.set_data()

    def set_model(self):
        self.model_config.set_data()

    def set_output(self):
        self.output_config.set_data()

    def set_including_label(self, value):
        TrainParamServer()['IncludingLabel'] = value

    def set_classification(self, value):
        TrainParamServer()['PredClass'] = value

    def exe_prediction(self):
        self.pred_progress.setText('Processing...')
        try:
            runner = PredictionRunner()
            result, label = runner.run(self.classification.isChecked(),
                                       self.including_label.isChecked())
            if 'PredOutputData' in TrainParamServer().__dict__:
                numpy.savetxt(TrainParamServer()['PredOutputData'],
                              result,
                              delimiter=",")
            result = result[:self.max_disp_rows.value(), :]
            if label is not None:
                label = label[:self.max_disp_rows.value(), :]
                result = numpy.hstack((result, label))
            self.result_table.setModel(ResultTableModel(result))
            self.pred_progress.setText('Prediction Finished!')
        except KeyError as ke:
            if ke.args[0] == 'PredInputData':
                util.disp_error('Input Data for prediction is not set.')
            elif ke.args[0] == 'PredModel':
                util.disp_error('Model for prediction is not set.')
            else:
                util.disp_error(ke.args[0][0])
        except util.AbnormalDataCode as ac:
            if not os.path.isfile(TrainParamServer()['PredInputData']):
                util.disp_error('{} is not found'.format(
                    TrainParamServer()['PredInputData']))
                return
            if not os.path.isfile(TrainParamServer()['PredModel']):
                util.disp_error(
                    '{} is not found'.format(TrainParamServer()['PredModel']))
                return
            util.disp_error(ac.args[0][0] + ' @' +
                            TrainParamServer()['PredInputData'])
        except ValueError:
            util.disp_error('Irregal data was found @' +
                            TrainParamServer()['PredInputData'])
        except type_check.InvalidType as error:
            last_node = util.get_executed_last_node()
            util.disp_error(str(error.args) + ' @node: ' + last_node)


class DataConfig(object):
    def __init__(self, label, window, is_save=False):
        self.param_name = self.__class__.__name__[:-6]  # remove 'Config'
        self.label = label
        train_server = TrainParamServer()
        if self.param_name in train_server.__dict__:
            self.label.setText(train_server[self.param_name])
        self.window = window
        self.direction = ''
        self.filter = ''
        self.is_save = is_save

    def set_data(self):
        train_server = TrainParamServer()
        if self.param_name in train_server.__dict__:
            init_path = train_server[self.param_name]
            init_path = os.path.abspath(init_path)
        else:
            init_path = train_server['WorkDir']
        if self.is_save:
            data_file = QtWidgets.QFileDialog.getSaveFileName(
                self.window, self.direction, init_path,
                filter=self.filter)[0]
        else:
            data_file = QtWidgets.QFileDialog.getOpenFileName(
                self.window, self.direction, init_path,
                filter=self.filter)[0]
        if data_file:
            self.label.setText(data_file)
            train_server[self.param_name] = data_file
        else:
            self.label.setText(self.direction)
            if 'self.param_name' in train_server.__dict__:
                del train_server[self.param_name]


class PredInputDataConfig(DataConfig):
    def __init__(self, label, window):
        super(PredInputDataConfig, self).__init__(label, window)
        self.direction = 'Input Data File is not selected.'
        self.filter = '(*.csv *.npz *.py);; Any (*.*)'


class PredOutputDataConfig(DataConfig):
    def __init__(self, label, window):
        super(PredOutputDataConfig, self).__init__(label, window, True)
        self.direction = 'Output Data File is not selected.'
        self.filter = '(*.csv);; Any (*.*)'


class PredModelConfig(DataConfig):
    def __init__(self, label, window):
        super(PredModelConfig, self).__init__(label, window)
        self.direction = 'Model File is not selected.'
        self.filter = '(*.npz);; Any (*.*)'


class ResultTableModel(QtCore.QAbstractTableModel):
    def __init__(self, array_data, parent=None, *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.array_data = array_data

    def headerData(self, column, orientation, role=QtCore.Qt.DisplayRole):
        if role!=QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        if orientation==QtCore.Qt.Horizontal:
            if (TrainParamServer()['IncludingLabel'] and
                        column == self.array_data.shape[1] - 1):
                return QtCore.QVariant('Label')
            else:
                return QtCore.QVariant('Pred {0}'.format(column))
        else:
            return QtCore.QVariant(column)

    def rowCount(self, parent):
        return min(1000, self.array_data.shape[0])

    def columnCount(self, parent):
        return self.array_data.shape[1]

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()
        elif role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        return float(self.array_data[index.row()][index.column()])
