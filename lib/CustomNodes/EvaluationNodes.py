from lib.node import Node, Input, Output

import chainer
from chainer import functions

import numpy


# TODO(fukatani) make abstract class

class Accuracy(Node):
    Input('in_array', chainer.Variable)
    Input('ground_truth', chainer.Variable)
    Output('accuracy', numpy.ndarray)

    def run(self):
        self._accuracy = functions.accuracy(self._in_array, self._ground_truth)
