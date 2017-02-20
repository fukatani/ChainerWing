import chainer

from floppy.node import Input, Output, Function


class Relu(Function):
    Input('in_array', chainer.Variable)
    Output('out_array', chainer.Variable)

    def call(self):
        return "relu("
