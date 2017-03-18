import chainer

from lib.node import Input, Output, Function


class Relu(Function):
    Input('in_array', chainer.Variable)
    Output('out_array', chainer.Variable)

    def call(self):
        return self.node_id + ' = relu('


class Sigmoid(Function):
    Input('in_array', chainer.Variable)
    Output('out_array', chainer.Variable)

    def call(self):
        return self.node_id + ' = sigmoid('


class Tanh(Function):
    Input('in_array', chainer.Variable)
    Output('out_array', chainer.Variable)

    def call(self):
        return self.node_id + ' = tanh('


class Dropout(Function):
    Input('in_array', chainer.Variable)
    Input('ratio', float)
    Output('out_array', chainer.Variable)

    def call(self):
        return self.node_id + ' = dropout(ratio={0}, x='.format(self._ratio)
