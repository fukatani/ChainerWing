from floppy.node import Node, Input, Output, Function

import chainer
from chainer import functions


class Relu(Function):
    Input('in_array', chainer.Variable)
    Output('out_array', chainer.Variable)

    def call(self):
        return "relu("
