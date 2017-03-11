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

import numpy


class {0}(chainer.Chain):

    def __init__(self):
        super({0}, self).__init__(
{1}
        )

    def _predict(self, x):
        return {3}

    def predict(self, x):
        return self._predict(x).data

    def predict_class(self, x):
        predicted = numpy.argmax(self.predict(x), axis=1)
        return numpy.atleast_2d(predicted).T

    def __call__(self, x, t):
        self.y = self._predict(x)
        self.loss = {2}
'''.format(net_name, init_impl, call_impl, pred_impl)
        rtn += "        reporter.report({'loss': self.loss}, self)\n"
        if classification:
            rtn += "        self.accuracy = accuracy(self.y, t)\n"
            rtn += "        reporter.report({'accuracy': self.accuracy}, self)\n"
        rtn += "        return self.loss"
        return rtn


class OptimizerTemplate(Template):
    def __call__(self, train_server):
        opt_params = []
        for param in train_server.iter_for_opt_params():
            opt_params.append(''.join((param[4:], '=', str(train_server[param]))))
        return '''

def get_optimizer():
    return {0}({1})
'''.format(train_server['Optimizer'], ', '.join(opt_params))


class TrainerTemplate(Template):
    def __call__(self, kwargs):
        call_train = '''


def training_main(train, test, pbar=None):
    model = {3}()

    optimizer = get_optimizer()
    optimizer.setup(model)

    train_iter = chainer.iterators.SerialIterator(train, {1})
    test_iter = chainer.iterators.SerialIterator(test, {1},
                                                 repeat=False,
                                                 shuffle=False)

    # Set up a trainer
    updater = training.StandardUpdater(train_iter, optimizer,
                                       device={2})
    '''.format(kwargs['Optimizer'], kwargs['BatchSize'],
               kwargs['GPU']-1, kwargs['NetName']) + '''
    if pbar is None:
        trainer = training.Trainer(updater, ({0}, 'epoch'))
    else:
        trainer = training.Trainer(updater, pbar.get_stop_trigger)
    '''.format(kwargs['Epoch']) + '''
    trainer.extend(extensions.Evaluator(test_iter, model, device={0}))
    '''.format(kwargs['GPU']-1) + '''
    trainer.extend(extensions.LogReport(log_name='{0}/chainer.log'))
    trainer.extend(
        extensions.PlotReport(['main/loss', 'validation/main/loss'],
                               'epoch',
                               file_name='{0}/loss.png'))
    '''.format(kwargs.get_result_dir())
        if 'Class' in kwargs['TrainMode']:
            call_train += '''
    trainer.extend(
        extensions.PlotReport(['main/accuracy', 'validation/main/accuracy'],
                               'epoch', file_name='{0}/accuracy.png'))
    '''.format(kwargs.get_result_dir())
        call_train += '''
    if pbar is not None:
        trainer.extend(pbar)
    else:
        trainer.extend(extensions.ProgressBar())

    trainer.run()
    serializers.save_npz('{1}.npz', model)


def prediction_main(input, classification=False):
    with chainer.using_config('train', False):
        model = {0}()
        serializers.load_npz('{1}.npz', model)
        if classification:
            return model.predict_class(input)
        else:
            return model.predict(input)


if __name__ == '__main__':
    training_main(False)
'''.format(kwargs['NetName'], kwargs.get_model_name())
        return call_train
