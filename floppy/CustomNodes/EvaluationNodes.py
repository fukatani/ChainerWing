from floppy.node import Node, Input, Output

import chainer
from chainer import functions

import numpy

#TODO(fukatani) make abstract class

class Accuracy(Node):
    Input('in_array', chainer.Variable)
    Output('accuracy', numpy.ndarray)

    def run(self):
        self._accuracy = functions.accuracy(self._in_array)
