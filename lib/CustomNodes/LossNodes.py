import chainer

from lib.node import Input, Loss


class SoftmaxCrossEntropy(Loss):
    Input('in_array', chainer.Variable)

    def call(self):
        return 'softmax_cross_entropy(self.y, t)'

    @classmethod
    def register_chainer_impl(cls):
        return chainer.functions.softmax_cross_entropy


class SigmoidCrossEntropy(Loss):
    Input('in_array', chainer.Variable)

    def call(self):
        return 'sigmoid_cross_entropy(self.y, t)'

    @classmethod
    def register_chainer_impl(cls):
        return chainer.functions.sigmoid_cross_entropy


class MeanSquaredError(Loss):
    Input('in_array', chainer.Variable)

    def call(self):
        return 'mean_squared_error(self.y, t)'

    @classmethod
    def register_chainer_impl(cls):
        return chainer.functions.mean_squared_error


# class HuberLoss(Loss):
#     Input('in_array', chainer.Variable)
#     Input('delta', float)
#
#     def call(self):
#         self.check_member(('_delta',))
#         return 'huber_loss(self.y, t, delta={0})'.format(self._delta)
