from floppy.node import Node, Input, Output

from chainer import datasets
import numpy

#TODO(fukatani) make abstract class

class GetMNIST(Node):
    Output('Train', numpy.ndarray)
    Output('TEST', numpy.ndarray)

    def run(self):
        # TODO(fukatani) link
        return datasets.get_mnist()

