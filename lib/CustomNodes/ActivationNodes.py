import chainer

from lib.node import Input, Output, Function


class Relu(Function):
    Input('in_array', chainer.Variable)
    Output('out_array', chainer.Variable)

    def call(self):
        return self.ID + ' = relu('


class Sigmoid(Function):
    Input('in_array', chainer.Variable)
    Output('out_array', chainer.Variable)

    def call(self):
        return self.ID + ' = sigmoid('


class Tanh(Function):
    Input('in_array', chainer.Variable)
    Output('out_array', chainer.Variable)

    def call(self):
        return self.ID + ' = tanh('


class Dropout(Function):
    Input('in_array', chainer.Variable)
    Input('ratio', float)
    Output('out_array', chainer.Variable)

    def call(self):
        self.check_member(('_ratio',))
        return self.ID + ' = dropout(ratio={0}, x='.format(self._ratio)
