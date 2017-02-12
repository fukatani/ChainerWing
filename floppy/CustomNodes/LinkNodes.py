from floppy.node import Node, Input, Output, Link

import chainer
from chainer import links


class Linear(Link):
    Input('in_array', chainer.Variable)
    Input('out_size', int)
    Input('nobias', bool, select=[True, False])
    Output('out_array', chainer.Variable)

    def run(self):
        #TODO(fukatani): implement systematically.
        if not self._out_size or not self._out_size:
            #TODO(fukatani): error display
            raise Exception
        return "links.Linear(None, {out_size}, nobias={nobias})" \
                    .format(out_size=self._out_size,
                            nobias=self._nobias)


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
        return "links.Convolution2D({in_channels}, {out_channels}, {ksize}, {nobias})"\
                    .format(in_channels=self._in_channels,
                            out_channels=self._out_channels,
                            ksize=self._ksize,
                            nobias=self._nobias)
