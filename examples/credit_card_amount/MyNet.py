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
            l0=Linear(None, 40, nobias=True),
            l1=Linear(None, 1, nobias=True),
        )

    def _predict(self, x):
        l0 = self.l0(x)
        f1 = relu(l0)
        f0 = dropout(ratio=0.5, x=f1)
        l1 = self.l1(f0)
        return l1

    def predict(self, x):
        return self._predict(x).data

    def predict_class(self, x):
        predicted = numpy.argmax(self.predict(x), axis=1)
        return numpy.atleast_2d(predicted).T

    def __call__(self, x, t):
        self.y = self._predict(x)
        self.loss = mean_squared_error(self.y, t)
        reporter.report({'loss': self.loss}, self)
        return self.loss

def get_optimizer():
    return Adam(alpha=0.001, beta2=0.999, beta1=0.9, eps=1e-06)


def training_main(train, test, pbar=None, plot_postprocess=None):
    model = MyNet()

    optimizer = get_optimizer()
    optimizer.setup(model)

    train_iter = chainer.iterators.SerialIterator(train, 30)
    test_iter = chainer.iterators.SerialIterator(test, 30,
                                                 repeat=False,
                                                 shuffle=False)

    # Set up a trainer
    updater = training.StandardUpdater(train_iter, optimizer,
                                       device=-1)
    
    if pbar is None:
        trainer = training.Trainer(updater, (20, 'epoch'))
    else:
        trainer = training.Trainer(updater, pbar.get_stop_trigger)
    
    trainer.extend(extensions.Evaluator(test_iter, model, device=-1))
    
    trainer.extend(extensions.LogReport(log_name='/home/ryo/workspace/github/CW_gui/examples/credit_card_amount/result/chainer.log'))
    trainer.extend(
        extensions.PlotReport(['main/loss', 'validation/main/loss'],
                               'epoch',
                               file_name='/home/ryo/workspace/github/CW_gui/examples/credit_card_amount/result/loss.png',
                               postprocess=plot_postprocess))
    
    if pbar is not None:
        trainer.extend(pbar)
    else:
        trainer.extend(extensions.ProgressBar())

    trainer.run()
    serializers.save_npz('/home/ryo/workspace/github/CW_gui/examples/credit_card_amount/result/MyModel.npz', model)


def prediction_main(input, classification=False):
    with chainer.using_config('train', False):
        model = MyNet()
        serializers.load_npz('/home/ryo/workspace/github/CW_gui/examples/credit_card_amount/result/MyModel.npz', model)
        if classification:
            return model.predict_class(input)
        else:
            return model.predict(input)


if __name__ == '__main__':
    training_main(False)
