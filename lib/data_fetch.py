import csv
from importlib import machinery

from chainer.datasets import tuple_dataset
import numpy as np

from lib.subwindows.train_config import TrainParamServer
from lib import util


class DataManager(object):
    def __init__(self):
        self.train_columns = 0

    def get_data_from_file(self, file_name, is_supervised, shuffle=False):
        if file_name.endswith('.csv'):
            return self.csv_to_ndarray(file_name, is_supervised, shuffle)
        elif file_name.endswith('.npz'):
            data = np.load(file_name)
            if shuffle:
                np.random.shuffle(data)
            if is_supervised:
                return data['x'], data['y']
            else:
                return data['x'], None
        else:
            raise util.UnexpectedFileExtension()

    def csv_to_ndarray(self, csv_file, is_supervised, shuffle):
        exists_header = 0
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            for line in reader:
                if isinstance(line[0], str):
                    exists_header = 1
                break
        array = np.loadtxt(csv_file, dtype=np.float32,
                           delimiter=',', skiprows=exists_header)
        if shuffle:
            np.random.shuffle(array)
        if is_supervised:
            return array[:, :-1], np.atleast_2d(array[:, -1]).T
        return array, None

    def pack_data(self, data, label):
        return tuple_dataset.TupleDataset(data, label)

    def get_data_train(self):
        train_server = TrainParamServer()
        if train_server['TrainData'].endswith('.py'):
            module = machinery.SourceFileLoader('data_getter',
                                                train_server['TrainData'])
            try:
                module = module.load_module()
                return module.main()
            except Exception as e:
                raise util.AbnormalCode(e.args)
        if train_server['UseSameData']:
            data_file = train_server['TrainData']
            data, label = self.get_data_from_file(data_file, True,
                                                  train_server['Shuffle'])
            if train_server['Shuffle']:
                np.random.shuffle(data)
            split_idx = int(data.shape[0] * train_server['TestDataRatio'])
            train_data = data[:split_idx]
            train_label = label[:split_idx]
            test_data = data[split_idx:]
            test_label = label[:split_idx]
        else:
            train_file = train_server['TrainData']
            train_data, train_label = self.get_data_from_file(train_file, True,
                                                              train_server['Shuffle'])
            test_file = train_server['TestData']
            test_data, test_label = self.get_data_from_file(test_file, True)

        test_data = self.pack_data(test_data, test_label)
        train_data = self.pack_data(train_data, train_label)
        return train_data, test_data

    def get_data_pred(self):
        train_server = TrainParamServer()
        if train_server['PredInputData'].endswith('.py'):
            module = machinery.SourceFileLoader('data_getter',
                                                train_server['PredInputData'])
            try:
                module = module.load_module()
                return module.main()
            except Exception as e:
                raise util.AbnormalCode(e.args)
        else:
            data_file = train_server['PredInputData']
            data = self.get_data_from_file(data_file, False)
            return data


if __name__ == '__main__':
    train_x, train_y = DataManager().get_data_from_file('sample_data.csv', True)
    train_x, train_y = DataManager().get_data_from_file('sample_data.npz', True)
