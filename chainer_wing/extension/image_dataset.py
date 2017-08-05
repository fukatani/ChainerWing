import os
import random

import chainer
from chainer.datasets.image_dataset import ImageDataset
from chainer.datasets.image_dataset import _read_image_as_array
import numpy

from chainer_wing.subwindows.train_config import TrainParamServer


class PreprocessedDataset(chainer.dataset.DatasetMixin):

    def __init__(self, path, root, mean, dtype=numpy.float32, **kwargs):
        self.base = chainer.datasets.LabeledImageDataset(path, root)
        self.mean = mean.astype('f')
        self.dtype = dtype

        self.use_resize = TrainParamServer()['UseResize']
        self.resize_width = TrainParamServer()['ResizeWidth']
        self.resize_height = TrainParamServer()['ResizeHeight']

        self.crop_edit = TrainParamServer()['Crop']
        self.crop_width = TrainParamServer()['CropWidth']
        self.crop_height = TrainParamServer()['CropHeight']

        self.use_random_crop = TrainParamServer()['UseRandomCrop']
        self.use_random_x_flip = TrainParamServer()['UseRandomXFlip']
        self.use_random_y_flip = TrainParamServer()['UseRandomYFlip']
        self.use_random_rotate = TrainParamServer()['UseRandomRotation']
        self.pca_lighting = TrainParamServer()['PCAlighting']

    def __len__(self):
        return len(self.base)

    def get_example(self, i):
        if isinstance(self.base[i], tuple):
            image, label = self.base[i]
        else:
            image = self.base[i]
            label = None

        if self.use_resize:
            image = transforms.resize(image, (self.resize_width, self.resize_height))
        image = transforms.random_flip(image, self.use_random_x_flip,
                                       self.use_random_y_flip)
        if self.use_random_rotate:
            image = transforms.random_rotate(image)
        image = transforms.pca_lighting(image,
                                        sigma=self.pca_lighting)

        if self.crop_edit == 'Center Crop':
            transforms.center_crop(image, (self.crop_width, self.crop_height))
        elif self.crop_edit == 'Random Crop':
            transforms.random_crop(image, (self.crop_width, self.crop_height))

        image -= self.mean
        image *= (1.0 / 255.0)  # Scale to [0, 1]

        if label is not None:
            return image.astype(self.dtype, copy=False), label
        else:
            return image.astype(self.dtype, copy=False)


class PreprocessedTestDataset(PreprocessedDataset):

    def __init__(self, path, root, mean,
                 dtype=numpy.float32):
        self.base = chainer.datasets.ImageDataset(path, root)
        self.mean = mean.astype('f')
        self.random = random
        self.dtype = dtype
