from floppy.node import Node, Input, Output

from chainer import datasets
import numpy

#TODO(fukatani) make abstract class

class GetMNIST(Node):
    Output('train', numpy.ndarray)
    Output('test', numpy.ndarray)

    def run(self):
        # TODO(fukatani) link
        self._train, self._test = datasets.get_mnist()

