from floppy.node import Node, Input, Output, Function

import chainer
from chainer import functions


class Relu(Node):
    Input('in_array', chainer.Variable)
    Output('out_array', chainer.Variable)

    def call(self):
        return "functions.relu("
