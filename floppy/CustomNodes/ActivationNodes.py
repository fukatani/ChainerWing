from floppy.node import Node, Input, Output, Function

import chainer
from chainer import functions


class Relu(Node):
    Input('in_array', chainer.Variable)
    Output('out_array', chainer.Variable)

    def run(self):
        self._out_array = functions.relu(self._in_array)
