from floppy.node import Node, Input, Output

from chainer import datasets
import chainer

#TODO(fukatani) make abstract class

class GetMNIST(Node):
    Output('train_x', chainer.Variable)
    Output('train_y', chainer.Variable)
    Output('test_x', chainer.Variable)
    Output('test_y', chainer.Variable)

    def run(self):
        train, test = datasets.get_mnist()
        self._train_x, self._train_y = train
        self._test_x, self._test_y = test
        self._train_x = chainer.Variable(self._train_x)
        self._train_y = chainer.Variable(self._train_y)
        self._test_x = chainer.Variable(self._test_x)
        self._test_y = chainer.Variable(self._test_y)
