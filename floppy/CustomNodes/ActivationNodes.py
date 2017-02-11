from floppy.node import Node, Input, Output

import chainer
from chainer import functions

#TODO(fukatani) make abstract class

class Relu(Node):
    Input('in_array', chainer.Variable)
    Output('out_array', chainer.Variable)

    def run(self):
        self._out_array = functions.relu(self._in_array)
