import chainer

from lib.node import Input, Loss


class SoftmaxCrossEntropy(Loss):
    Input('in_array', chainer.Variable)
    Input('ground_truth', chainer.Variable)

    def call(self):
        return "softmax_cross_entropy("
