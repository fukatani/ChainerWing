import chainer

from lib.node import Input, Loss


class SoftmaxCrossEntropy(Loss):
    Input('in_array', chainer.Variable)

    def call(self):
        return 'softmax_cross_entropy(self.y, t)'


class SigmoidCrossEntropy(Loss):
    Input('in_array', chainer.Variable)

    def call(self):
        return 'sigmoid_cross_entropy(self.y, t)'


class MeanSquaredError(Loss):
    Input('in_array', chainer.Variable)

    def call(self):
        return 'mean_squared_error(self.y, t)'


class HuberLoss(Loss):
    Input('in_array', chainer.Variable)
    Input('delta', float)

    def call(self):
        return 'huber_loss(self.y, t, delta={0})'.format(self._delta)
