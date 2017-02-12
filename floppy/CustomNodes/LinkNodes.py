from floppy.node import Node, Input, Output, Link

import chainer
from chainer import links


class Linear(Link):
    Input('in_array', chainer.Variable)
    Input('out_size', int)
    Input('nobias', bool, select=[True, False])
    Output('out_array', chainer.Variable)

    def run(self):
        self._out_array = links.Linear(None, self._out_size, nobias=self._nobias)


class Convolution2D(Link):
    Input('in_array', chainer.Variable)
    Input('in_channels', int)
    Input('out_channels', int)
    Input('ksize', int)
    Input('stride', int)
    Input('pad', int)
    Input('nobias', bool, select=[True, False])
    Output('out_array', chainer.Variable)

    def run(self):
        self._out_array = links.Convolution2D(self._in_channels,
                                              self._out_channels,
                                              self._ksize,
                                              nobias=self._nobias)
