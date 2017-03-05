import chainer
from chainer.functions import *
from chainer.links import *
from chainer.optimizers import *

from chainer import training
from chainer.training import extensions
from chainer import reporter
from chainer import serializers


class MyNet(chainer.Chain):

    def __init__(self):
        super(MyNet, self).__init__(
            l0=Linear(None, 200, nobias=False),
            l1=Linear(None, 300, nobias=True),
        )

    def predict(self, x):
        return relu(self.l1(relu(self.l0(x))))

    def __call__(self, x, t):
        self.y = self.predict(x)
        self.loss = softmax_cross_entropy(self.y, t)
        reporter.report({'loss': self.loss}, self)
        self.accuracy = accuracy(self.y, t)
        reporter.report({'accuracy': self.accuracy}, self)
        return self.loss


def training_main(train, test, pbar=None):
    model = MyNet()

    optimizer = AdaDelta()
    optimizer.setup(model)

    train_iter = chainer.iterators.SerialIterator(train, 20)
    test_iter = chainer.iterators.SerialIterator(test, 20,
                                                 repeat=False,
                                                 shuffle=False)

    # Set up a trainer
    updater = training.StandardUpdater(train_iter, optimizer,
                                       device=0)
    
    if pbar is None:
        trainer = training.Trainer(updater, (20, 'epoch'))
    else:
        trainer = training.Trainer(updater, pbar.get_stop_trigger)
    
    trainer.extend(extensions.Evaluator(test_iter, model, device=0))
    
    trainer.extend(extensions.snapshot(), trigger=(20, 'epoch'))
    
    trainer.extend(extensions.LogReport())
    trainer.extend(
        extensions.PlotReport(['main/loss', 'validation/main/loss'],
                               'epoch',
                               file_name='loss.png'))
    
    trainer.extend(
        extensions.PlotReport(['main/accuracy', 'validation/main/accuracy'],
                               'epoch', file_name='accuracy.png'))
    
    if pbar is not None:
        trainer.extend(pbar)
    else:
        trainer.extend(extensions.ProgressBar())

    trainer.run()
    serializers.save_npz("MyNet.npz", model)


def prediction_main(input, pbar=None):
    model = MyNet()
    serializers.load_npz("MyNet.npz", model)
    return model(input)


if __name__ == '__main__':
    training_main(False)
