import chainer
from chainer.functions import *
from chainer.links import *
from chainer.optimizers import *

from chainer import training
from chainer.training import extensions
from chainer import reporter
from chainer import serializers

import numpy


class MyNet(chainer.Chain):

    def __init__(self):
        super(MyNet, self).__init__(
            l0=Linear(None, 200, nobias=False),
            l1=Linear(None, 10, nobias=True),
        )

    def _predict(self, x):
        return relu(self.l1(dropout(ratio=0.5, x=relu(self.l0(x)))))

    def predict(self, x):
        return self._predict(x).data

    def predict_class(self, x):
        predicted = numpy.argmax(self.predict(x), axis=1)
        return numpy.atleast_2d(predicted).T

    def __call__(self, x, t):
        self.y = self._predict(x)
        self.loss = softmax_cross_entropy(self.y, t)
        reporter.report({'loss': self.loss}, self)
        self.accuracy = accuracy(self.y, t)
        reporter.report({'accuracy': self.accuracy}, self)
        return self.loss

def get_optimizer():
    return AdaDelta(eps=1e-06, rho=0.95)


def training_main(train, test, pbar=None, plot_postprocess=None):
    model = MyNet()

    optimizer = get_optimizer()
    optimizer.setup(model)

    train_iter = chainer.iterators.SerialIterator(train, 20)
    test_iter = chainer.iterators.SerialIterator(test, 20,
                                                 repeat=False,
                                                 shuffle=False)

    # Set up a trainer
    updater = training.StandardUpdater(train_iter, optimizer,
                                       device=0)
    
    if pbar is None:
        trainer = training.Trainer(updater, (10, 'epoch'))
    else:
        trainer = training.Trainer(updater, pbar.get_stop_trigger)
    
    trainer.extend(extensions.Evaluator(test_iter, model, device=0))
    
    trainer.extend(extensions.LogReport(log_name='/home/ryo/workspace/github/CW_gui/examples/mnist/result/chainer.log'))
    trainer.extend(
        extensions.PlotReport(['main/loss', 'validation/main/loss'],
                               'epoch',
                               file_name='/home/ryo/workspace/github/CW_gui/examples/mnist/result/loss.png',
                               postprocess=plot_postprocess))
    
    trainer.extend(
        extensions.PlotReport(['main/accuracy', 'validation/main/accuracy'],
                               'epoch', file_name='/home/ryo/workspace/github/CW_gui/examples/mnist/result/accuracy.png'))
    
    if pbar is not None:
        trainer.extend(pbar)
    else:
        trainer.extend(extensions.ProgressBar())

    trainer.run()
    serializers.save_npz('/home/ryo/workspace/github/CW_gui/examples/mnist/result/MyModel.npz', model)


def prediction_main(input, classification=False):
    with chainer.using_config('train', False):
        model = MyNet()
        serializers.load_npz('/home/ryo/workspace/github/CW_gui/examples/mnist/result/MyModel.npz', model)
        if classification:
            return model.predict_class(input)
        else:
            return model.predict(input)


if __name__ == '__main__':
    training_main(False)
