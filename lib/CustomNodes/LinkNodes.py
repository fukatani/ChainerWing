import chainer

from lib.node import Input, Output, Link


# TODO(fukatani): implement systematically.
class Linear(Link):
    Input('in_array', chainer.Variable)
    Input('out_size', int)
    Input('nobias', bool, select=[True, False])
    Output('out_array', chainer.Variable)

    def call_init(self):
        self.check_member(('_out_size', '_nobias'))
        return 'Linear(None, {out_size}, nobias={nobias}),' \
            .format(out_size=self._out_size,
                    nobias=self._nobias)

    @classmethod
    def register_chainer_impl(cls):
        return chainer.links.linear


class Maxout(Link):
    Input('in_array', chainer.Variable)
    Input('out_size', int)
    Input('pool_size', int)
    def call_init(self):
        self.check_member(('_out_size', '_pool_size'))
        return 'Maxout(None, {out_size}, {pool_size})' \
            .format(out_size=self._out_size, pool_size=self._pool_size)

    @classmethod
    def register_chainer_impl(cls):
        return chainer.links.maxout


# class Convolution2D(Link):
#     Input('in_array', chainer.Variable)
#     Input('in_channels', int)
#     Input('out_channels', int)
#     Input('ksize', int)
#     Input('stride', int)
#     Input('pad', int)
#     Input('nobias', bool, select=[True, False])
#     Output('out_array', chainer.Variable)
#
#     def call_init(self):
#         return 'Convolution2D({in_channels}, {out_channels}, {ksize}, {nobias}),' \
#             .format(in_channels=self._in_channels,
#                     out_channels=self._out_channels,
#                     ksize=self._ksize,
#                     nobias=self._nobias)
