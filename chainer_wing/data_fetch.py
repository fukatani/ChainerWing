import csv
from importlib import machinery
import glob
import os

from chainer.datasets import tuple_dataset
from chainer.datasets.image_dataset import _read_image_as_array
import numpy

from chainer_wing.extension.image_dataset import augment_data
from chainer_wing.subwindows.train_config import TrainParamServer
from chainer_wing import util


class DataManager(object):
    def __init__(self):
        self.train_columns = 0

    def get_data_from_file(self, file_name, is_supervised, shuffle=False):
        if file_name.endswith('.csv'):
            return self.csv_to_ndarray(file_name, is_supervised, shuffle)
        elif file_name.endswith('.npz'):
            data = numpy.load(file_name)
            if shuffle:
                numpy.random.shuffle(data)
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
        array = numpy.loadtxt(csv_file, dtype=numpy.float32,
                              delimiter=',', skiprows=exists_header)
        if shuffle:
            numpy.random.shuffle(array)
        if is_supervised:
            return array[:, :-1], numpy.atleast_2d(array[:, -1]).T
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
                train_data, test_data = module.main()
                train_data, train_label = train_data._datasets
                test_data, test_label = test_data._datasets
            except Exception as e:
                raise util.AbnormalDataCode(e.args)
        elif train_server['UseSameData']:
            data_file = train_server['TrainData']
            data, label = self.get_data_from_file(data_file, True,
                                                  train_server['Shuffle'])
            if train_server['Shuffle']:
                numpy.random.shuffle(data)
            split_idx = int(data.shape[0] * train_server['TestDataRatio'])
            train_data = data[:split_idx]
            train_label = label[:split_idx]
            test_data = data[split_idx:]
            test_label = label[split_idx:]
        else:
            train_file = train_server['TrainData']
            train_data, train_label = self.get_data_from_file(train_file, True,
                                                              train_server['Shuffle'])
            test_file = train_server['TestData']
            test_data, test_label = self.get_data_from_file(test_file, True)

        # minmax
        if TrainParamServer().use_minmax():
            test_data = self.minmax_scale(test_data)
            train_data = self.minmax_scale(train_data)
        test_data = self.pack_data(test_data, test_label)
        train_data = self.pack_data(train_data, train_label)
        return train_data, test_data

    def get_data_pred(self, including_label):
        train_server = TrainParamServer()
        if train_server['PredInputData'].endswith('.py'):
            module = machinery.SourceFileLoader('data_getter',
                                                train_server['PredInputData'])
            try:
                module = module.load_module()
                if including_label:
                    data, label = module.main()
                else:
                    data, label = module.main(), None
            except Exception as error:
                raise util.AbnormalDataCode(error.args)
        else:
            data_file = train_server['PredInputData']
            data, label = self.get_data_from_file(data_file, including_label)

        if TrainParamServer().use_minmax():
            data = self.minmax_scale(data)
        return data, label

    def minmax_scale(self, x, lower_limit=0., upper_limit=1.):
        data_min = numpy.min(x, axis=0)
        x = x - data_min + lower_limit
        data_max = numpy.max(x, axis=0)
        return x / data_max * upper_limit


class ImageDataManager(object):
    def get_label(self, label):
        return label.split('/')[-2]

    def get_all_images(self, dir_name):
        if not os.path.isdir(dir_name):
            raise Exception('Directory {} was not found.'.format(dir_name))
        image_files = glob.glob(dir_name + '/*/*.jpg')
        if not image_files:
            raise Exception('No jpg file in {}'.format(dir_name))

        labels = []
        for image_file in image_files:
            label = self.get_label(image_file)
            labels.append(label)
        return numpy.array(image_files), numpy.array(labels)

    def make_image_list(self, image_files, labels, list_file_name):
        assert len(image_files) == len(labels)
        with open(list_file_name, 'w') as fw:
            for image, label in zip(image_files, labels):
                fw.write(image + ' '+ label)

    def get_data_train(self):
        train_server = TrainParamServer()
        train_images, train_labels = self.get_all_images(train_server['TrainData'])

        if train_server['UseSameData']:
            split_idx = int(len(train_images) * train_server['TestDataRatio'])

            indices = numpy.arange(len(train_images))
            if train_server['Shuffle']:
                numpy.random.shuffle(indices)

            train_idx = indices[:split_idx]
            test_idx = indices[:split_idx]

            test_images = train_images[test_idx]
            test_labels = train_labels[test_idx]
            train_images = train_images[train_idx]
            train_labels = train_labels[train_idx]
        else:
            test_images, test_labels = self.get_all_images(train_server['TrainData'])

        train_label_file = os.path.join(train_server.get_work_dir(),
                                        'train_label.txt')
        self.make_image_list(train_images, train_labels, train_label_file)
        test_label_file = os.path.join(train_server.get_work_dir(),
                                        'test_label.txt')
        self.make_image_list(test_images, test_labels, test_label_file)

        self.compute_mean(train_images)

    def compute_mean(self, images):
        print('compute mean image')
        sum_image = 0
        N = len(images)

        resize_width = TrainParamServer()['ResizeWidth']
        resize_height = TrainParamServer()['ResizeHeight']

        crop_edit = TrainParamServer()['Crop']
        crop_width = TrainParamServer()['CropWidth']
        crop_height = TrainParamServer()['CropHeight']

        use_random_x_flip = TrainParamServer()['UseRandomXFlip']
        use_random_y_flip = TrainParamServer()['UseRandomYFlip']
        use_random_rotate = TrainParamServer()['UseRandomRotation']
        pca_lighting = TrainParamServer()['PCAlighting']

        for i, image in enumerate(images):
            image = _read_image_as_array(image, numpy.float32)
            image = image.transpose(2, 0, 1).astype(numpy.float32)
            image = augment_data(image, resize_width, resize_height,
                                 use_random_x_flip, use_random_y_flip,
                                 use_random_rotate, pca_lighting, crop_edit,
                                 crop_width, crop_height)
            sum_image += image

        mean_file = os.path.join(TrainParamServer().get_work_dir(),
                                 'mean.npy')
        mean = sum_image / N
        numpy.save(mean_file, mean)

    def get_data_pred(self):
        train_server = TrainParamServer()
        if os.path.isdir(train_server['PredInputData']):
            dir_name = train_server['PredInputData']
            image_files = glob.glob(dir_name + '/*.jpg')
            if not image_files:
                raise Exception('No jpg file in {}'.format(dir_name))

            pred_label_file = os.path.join(train_server.get_work_dir(),
                                       'train_label.txt')

        elif os.path.isfile(train_server['PredInputData']):
            image_files = (train_server['PredInputData'],)
            pred_label_file = os.path.join(train_server.get_work_dir(),
                                           'train_label.txt')
        else:
            raise FileNotFoundError(train_server['PredInputData'] +
                                    ' is not found.')

        with open(pred_label_file, 'w') as fw:
            for image, label in zip(image_files, pred_label_file):
                fw.write(image)

        return pred_label_file


if __name__ == '__main__':
    train_x, train_y = DataManager().get_data_from_file('sample_data.csv', True)
    train_x, train_y = DataManager().get_data_from_file('sample_data.npz', True)
