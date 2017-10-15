from importlib import machinery
import os

import numpy

from chainer_wing import util
from chainer_wing.data_fetch import DataManager
from chainer_wing.data_fetch import ImageDataManager
from chainer_wing.extension.cw_progress_bar import CWProgressBar
from chainer_wing.extension.image_dataset import PreprocessedDataset
from chainer_wing.extension.image_dataset import PreprocessedTestDataset
from chainer_wing.extension.plot_extension import cw_postprocess
from chainer_wing.subwindows.train_config import TrainParamServer


def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    e_x = numpy.exp(x - numpy.max(x, axis=1)[:, None])
    return e_x / e_x.sum(axis=1)[:, None] * 100


class TrainRunner(object):

    def __init__(self):
        train_server = TrainParamServer()
        module_file = machinery.SourceFileLoader('net_run',
                                                 train_server.get_net_name())
        self.module = module_file.load_module()

        # Progress bar should be initialized after loading module file.
        self.pbar = CWProgressBar(train_server['Epoch'])

    def run(self):
        train_server = TrainParamServer()
        if not os.path.isdir(train_server['WorkDir'] + '/result'):
            os.mkdir(train_server['WorkDir'] + '/result')
        if 'Image' in TrainParamServer()['Task']:
            ImageDataManager().get_data_train()
            train_label_file = os.path.join(train_server.get_work_dir(),
                                            'train_label.txt')
            test_label_file = os.path.join(train_server.get_work_dir(),
                                           'test_label.txt')
            mean_file = os.path.join(TrainParamServer().get_work_dir(),
                                     'mean.npy')
            mean = numpy.load(mean_file)
            train_data = PreprocessedDataset(train_label_file, mean)
            test_data = PreprocessedDataset(test_label_file, mean)
        else:
            train_data, test_data = DataManager().get_data_train()
        self.module.training_main(train_data, test_data, self.pbar,
                                  cw_postprocess)
        util.disp_message('Training is finished. Model file is saved to ' +
                          train_server.get_model_name() + '.npz')

    def kill(self):
        self.pbar.finalize()


class PredictionRunner(object):

    def __init__(self):
        train_server = TrainParamServer()
        module_file = machinery.SourceFileLoader('net_run',
                                                 train_server.get_net_name())
        self.module = module_file.load_module()

    def run(self, classification, including_label):
        input_data, label = DataManager().get_data_pred(including_label)
        result = self.module.prediction_main(input_data, classification)
        result = softmax(result)
        return result, label


class ImagePredictionRunner(PredictionRunner):
    def run(self, classification, including_label):
        pred_label_file = ImageDataManager().get_data_pred()
        mean_file = os.path.join(TrainParamServer().get_work_dir(),
                                 'mean.npy')
        mean = numpy.load(mean_file)

        input_data = PreprocessedTestDataset(pred_label_file, mean)
        arrays = []
        for i in range(len(input_data)):
            arrays.append(input_data.get_example(i))
        input_array = numpy.stack(arrays, axis=0)
        result = self.module.prediction_main(input_array, classification)
        result = softmax(result)
        return result, None
