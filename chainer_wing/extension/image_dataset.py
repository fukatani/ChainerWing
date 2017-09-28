import os
import random

import chainer
from chainer.datasets.image_dataset import ImageDataset
from chainer.datasets.image_dataset import _read_image_as_array
import numpy

from chainercv import transforms

from chainer_wing.subwindows.train_config import TrainParamServer


def augment_data(image, resize_width, resize_height,
                 use_random_x_flip, use_random_y_flip, use_random_rotate,
                 use_pca_lighting, crop_edit, crop_width, crop_height):
    # image = image.transpose(2, 0, 1).astype(numpy.float32)
    image = transforms.random_flip(image, use_random_x_flip,
                                   use_random_y_flip)
    if use_random_rotate:
        image = transforms.random_rotate(image)
    image = transforms.pca_lighting(image,
                                    sigma=use_pca_lighting)

    if crop_edit == 'Center Crop':
        image = transforms.center_crop(image, (crop_width, crop_height))
    elif crop_edit == 'Random Crop':
        image = transforms.random_crop(image, (crop_width, crop_height))
    image = transforms.resize(image, (resize_width, resize_height))
    # return image.transpose(1, 2, 0).astype(numpy.uint8)
    return image


class PreprocessedDataset(chainer.dataset.DatasetMixin):

    def __init__(self, path, mean, dtype=numpy.float32):
        root = TrainParamServer().get_work_dir()
        self.base = chainer.datasets.LabeledImageDataset(path, root)
        self.mean = mean.astype('f')
        self.dtype = dtype

        self.resize_width = TrainParamServer()['ResizeWidth']
        self.resize_height = TrainParamServer()['ResizeHeight']

        self.crop_edit = TrainParamServer()['Crop']
        self.crop_width = TrainParamServer()['CropWidth']
        self.crop_height = TrainParamServer()['CropHeight']

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

        image = augment_data(image, self.resize_width,
                             self.resize_height, self.use_random_x_flip,
                             self.use_random_y_flip, self.use_random_rotate,
                             self.pca_lighting, self.crop_edit, self.crop_width,
                             self.crop_height)

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
