import chainer

from lib.node import Input, Loss


class SoftmaxCrossEntropy(Loss):
    Input('in_array', chainer.Variable)
    Input('ground_truth', chainer.Variable)

    def call(self):
        return "softmax_cross_entropy("


class SigmoidCrossEntropy(Loss):
    Input('in_array', chainer.Variable)
    Input('ground_truth', chainer.Variable)

    def call(self):
        return "sigmoid_cross_entropy("


class MeanSquaredError(Loss):
    Input('in_array', chainer.Variable)
    Input('ground_truth', chainer.Variable)

    def call(self):
        return "mean_squared_error("


class HuberLoss(Loss):
    Input('in_array', chainer.Variable)
    Input('delta', float)
    Input('ground_truth', chainer.Variable)

    def call(self):
        return "huber_loss(delta={delta}"
