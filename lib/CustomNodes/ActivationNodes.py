import chainer

from lib.node import Input, Output, Function


class Relu(Function):
    Input('in_array', chainer.Variable)
    Output('out_array', chainer.Variable)

    def call(self):
        return "relu("


class Sigmoid(Function):
    Input('in_array', chainer.Variable)
    Output('out_array', chainer.Variable)

    def call(self):
        return "sigmoid("


class Tanh(Function):
    Input('in_array', chainer.Variable)
    Output('out_array', chainer.Variable)

    def call(self):
        return "tanh("
