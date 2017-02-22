TEMPLATES = {}


class MetaTemplate(type):
    def __new__(cls, name, bases, classdict):
        result = type.__new__(cls, name, bases, classdict)
        # result.__dict__['Input'] = result._addInput
        TEMPLATES[name] = result
        return result


class Template(object, metaclass=MetaTemplate):
    ELEMENTS = []

    def __init__(self):
        self.elements = [element() for element in self.ELEMENTS]

    def __call__(self, data, cache, fileBase, width):
        return '''
<HTML>

    <BODY bgcolor="#606060">
        <P>This is an abstract Base Template.
        Please don't use me.</P>
    </BODY>
</HTML>
    '''


class NetTemplate(Template):

    def __call__(self, net_name, init_impl, call_impl, pred_impl,
                 classification):
        rtn = '''import chainer
from chainer.functions import *
from chainer.links import *
from chainer.optimizers import *

from chainer import training
from chainer.training import extensions
from chainer import reporter
from chainer import serializers

from floppy.cw_progress_bar import CWProgressBar


class {0}(chainer.Chain):

    def __init__(self):
        super({0}, self).__init__(
{1}
        )

    def predict(self, x):
        return {3}

    def __call__(self, x, t):
        self.y = self.predict(x)
        self.loss = {2}
'''.format(net_name, init_impl, call_impl, pred_impl)
        rtn += "        reporter.report({'loss': self.loss}, self)\n"
        if classification:
            rtn += "        self.accuracy = accuracy(self.y, t)\n"
            rtn += "        reporter.report({'accuracy': self.accuracy}, self)\n"
        rtn += "        return self.loss"
        return rtn


class TrainerTemplate(Template):
    def __call__(self, kwargs):
        call_train = '''


def training_main(call_by_gui=False):
    model = {3}()

    optimizer = {0}()
    optimizer.setup(model)

    train, test = chainer.datasets.get_mnist()

    train_iter = chainer.iterators.SerialIterator(train, {1})
    test_iter = chainer.iterators.SerialIterator(test, {1},
                                                 repeat=False,
                                                 shuffle=False)

    # Set up a trainer
    updater = training.StandardUpdater(train_iter, optimizer,
                                       device={2})
    '''.format(kwargs['Optimizer'], kwargs['BatchSize'],
               kwargs['GPU'], kwargs['NetName']) + '''
    trainer = training.Trainer(updater, ({0}, 'epoch'))
    '''.format(kwargs['Epoch']) + '''
    trainer.extend(extensions.Evaluator(test_iter, model, device={0}))
    '''.format(kwargs['GPU']) + '''
    trainer.extend(extensions.snapshot(), trigger=({0}, 'epoch'))
    '''.format(kwargs['Epoch']) + '''
    trainer.extend(extensions.LogReport())
    trainer.extend(
        extensions.PlotReport(['main/loss', 'validation/main/loss'],
                               'epoch',
                               file_name='loss.png'))
    '''
        if 'Class' in kwargs['TrainMode']:
            call_train += '''
    trainer.extend(
        extensions.PlotReport(['main/accuracy', 'validation/main/accuracy'],
                               'epoch', file_name='accuracy.png'))
    '''
        call_train += '''
    if call_by_gui:
        trainer.extend(CWProgressBar())
    else:
        trainer.extend(extensions.ProgressBar())

    trainer.run()
    serializers.save_npz("{0}.npz", model)
'''.format(kwargs['ModelName'])
        return call_train


class PredTemplate(Template):
    def __call__(self, *args, **kwargs):
        return '''
def prediction_main(x):
    model = {0}()
    serializers.load_npz("{0}.npz", model)
    return model.predict(x)
'''.format(kwargs['NetName'])
