import chainer
from chainer.functions import *
from chainer.links import *
from chainer.optimizers import *

from chainer import training
from chainer.training import extensions
from chainer import reporter

from floppy.cw_progress_bar import CWProgressBar


class MyNet1(chainer.Chain):

    def __init__(self):
        super(MyNet1, self).__init__(
            l0=Linear(None, 300, nobias=True),
            l1=Linear(None, 200, nobias=False),
        )

    def __call__(self, x, y):
        self.loss = softmax_cross_entropy(relu(self.l0(relu(self.l1(x)))), y)
        reporter.report({'loss': self.loss}, self)
        return self.loss

def main(call_by_gui=False):
    model = MyNet1()

    optimizer = AdaDelta()
    optimizer.setup(model)

    train, test = chainer.datasets.get_mnist()

    train_iter = chainer.iterators.SerialIterator(train, 20)
    test_iter = chainer.iterators.SerialIterator(test, 20,
                                                 repeat=False,
                                                 shuffle=False)

    # Set up a trainer
    updater = training.StandardUpdater(train_iter, optimizer,
                                       device=0)
    
    trainer = training.Trainer(updater, (10, 'epoch'))
    
    trainer.extend(extensions.Evaluator(test_iter, model, device=0))
    
    trainer.extend(extensions.snapshot(), trigger=(10, 'epoch'))
    
    trainer.extend(extensions.LogReport())
    trainer.extend(
        extensions.PlotReport(['main/loss', 'validation/main/loss'],
                               'epoch',
                               file_name='loss.png'))
    
    if call_by_gui:
        trainer.extend(CWProgressBar())
    else:
        trainer.extend(extensions.ProgressBar())
    trainer.run()


if __name__ == '__main__':
    main(False)
    