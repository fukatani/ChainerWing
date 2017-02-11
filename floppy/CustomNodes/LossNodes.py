from floppy.node import Node, Input, Output

import chainer
from chainer import functions

#TODO(fukatani) make abstract class

class SoftmaxCrossEntropy(Node):
    Input('in_array', chainer.Variable)
    Input('ground_truth', chainer.Variable)
    Output('out_array', chainer.Variable)

    def run(self):
        self._out_array = functions.softmax_cross_entropy(self._in_array,
                                                          self._ground_truth)

