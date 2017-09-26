from importlib import machinery
import os

import chainer
import numpy

from chainer_wing.data_fetch import DataManager
from chainer_wing.data_fetch import ImageDataManager
from chainer_wing.extension.cw_progress_bar import CWProgressBar
from chainer_wing.extension.plot_extension import cw_postprocess
from chainer_wing.subwindows.train_config import TrainParamServer


class PreprocessedDataset(chainer.dataset.DatasetMixin):

    def __init__(self, path, mean, dtype=numpy.float32):
        root = TrainParamServer().get_work_dir()
        self.base = chainer.datasets.LabeledImageDataset(path, root)
        self.mean = mean.astype('f')
        self.dtype = dtype

    def __len__(self):
        return len(self.base)

    def get_example(self, i):
        if isinstance(self.base[i], tuple):
            image, label = self.base[i]
        else:
            image = self.base[i]
            label = None

        image -= self.mean
        image *= (1.0 / 255.0)  # Scale to [0, 1]
        if label is not None:
            return image.astype(self.dtype, copy=False), label
        else:
            return image.astype(self.dtype, copy=False)


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
        return result, label
