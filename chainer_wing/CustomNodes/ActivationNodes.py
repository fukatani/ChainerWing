import chainer

from chainer_wing.node import Input, Output, Function


class Relu(Function):
    Input('in_array', (chainer.Variable,))
    Output('out_array', (chainer.Variable,))

    def call(self):
        return self.ID + ' = relu('

    @classmethod
    def register_chainer_impl(cls):
        return chainer.functions.relu


class Sigmoid(Function):
    Input('in_array', (chainer.Variable,))
    Output('out_array', (chainer.Variable,))

    def call(self):
        return self.ID + ' = sigmoid('

    @classmethod
    def register_chainer_impl(cls):
        return chainer.functions.sigmoid


class Tanh(Function):
    Input('in_array', (chainer.Variable,))
    Output('out_array', (chainer.Variable,))

    def call(self):
        return self.ID + ' = tanh('

    @classmethod
    def register_chainer_impl(cls):
        return chainer.functions.tanh


class Dropout(Function):
    Input('in_array', (chainer.Variable,))
    Input('ratio', (float,))
    Output('out_array', (chainer.Variable,))

    def call(self):
        self.check_member(('_ratio',))
        return self.ID + ' = dropout(ratio={0}, x='.format(self._ratio)

    @classmethod
    def register_chainer_impl(cls):
        return chainer.functions.dropout


class Elu(Function):
    Input('in_array', (chainer.Variable,))
    Input('alpha', (float,))
    Output('out_array', (chainer.Variable,))

    def call(self):
        self.check_member(('_alpha',))
        return self.ID + ' = elu(alpha={0}, x='.format(self._elu)

    @classmethod
    def register_chainer_impl(cls):
        return chainer.functions.elu


class ClippedRelu(Function):
    Input('in_array', (chainer.Variable,))
    Input('z', (float,))
    Output('out_array', (chainer.Variable,))

    def call(self):
        self.check_member(('_alpha',))
        return self.ID + ' = clipped_relu(z={0}, x='.format(self._elu)

    @classmethod
    def register_chainer_impl(cls):
        return chainer.functions.clipped_relu


class HardSigmoid(Function):
    Input('in_array', (chainer.Variable,))
    Output('out_array', (chainer.Variable,))

    def call(self):
        return self.ID + ' = hard_sigmoid('

    @classmethod
    def register_chainer_impl(cls):
        return chainer.functions.hard_sigmoid
