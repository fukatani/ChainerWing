
import chainer
from chainer.functions import *
from chainer.links import *
from chainer.optimizers import *

from chainer import training
from chainer.training import extensions


class TestNet(chainer.Chain):

    def __init__(self):
        super(TestNet, self).__init__(
            l0=Linear(None, 300, nobias=True),
            l1=Linear(None, 200, nobias=False),
        )

    def __call__(self, x, y):
        softmax_cross_entropy(relu(self.l0(relu(self.l1(x)))), y)
        
if __name__ == '__main__':
    model == TestNet()

    optimizer = AdaDelta()
    optimizer.setup(model)

    train, test = chainer.datasets.get_mnist()

    train_iter = chainer.iterators.SerialIterator(train, 20)
    test_iter = chainer.iterators.SerialIterator(test, 20,
                                                 repeat=False,
                                                 shuffle=False)

    # Set up a trainer
    updater = training.StandardUpdater(train_iter, optimizer,
                                       device=11)
    
    trainer = training.Trainer(updater, (20, 'epoch'))
    
    trainer.extend(extensions.Evaluator(test_iter, model, device=11))
    
    trainer.extend(extensions.snapshot(), trigger=(20, 'epoch'))
    
    trainer.extend(extensions.LogReport())
    trainer.extend(
        extensions.PlotReport(['main/loss', 'validation/main/loss'],
                               'epoch',
                               file_name='loss.png'))
    
    trainer.run()
    