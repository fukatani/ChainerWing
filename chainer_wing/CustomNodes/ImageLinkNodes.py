import chainer

from chainer_wing.node import Input, Output, Link


class Convolution2D(Link):
    Input('in_array', (chainer.Variable,))
    Input('out_channels', (int,))
    Input('ksize', (int,))
    Input('stride', (int,))
    Input('pad', (int,))
    Input('nobias', (bool,), select=[True, False])
    Output('out_array', (chainer.Variable,))
    is_image_node = True

    def call_init(self):
        return 'Convolution2D({in_channels}, {out_channels}, {ksize}, ' \
               '{stride}, {pad}, {nobias}),' \
            .format(in_channels='None',
                    out_channels=self._out_channels,
                    ksize=self._ksize,
                    stride=self._stride,
                    pad=self._pad,
                    nobias=self._nobias)

    @classmethod
    def register_chainer_impl(cls):
        return chainer.links.Convolution2D


class Deconvolution2D(Link):
    Input('in_array', (chainer.Variable,))
    Input('out_channels', (int,))
    Input('ksize', (int,))
    Input('stride', (int,))
    Input('pad', (int,))
    Input('nobias', (bool,), select=[True, False])
    Output('out_array', (chainer.Variable,))
    is_image_node = True

    def call_init(self):
        return 'Deconvolution2D({in_channels}, {out_channels}, {ksize}, ' \
               '{stride}, {pad}, {nobias}),' \
            .format(in_channels='None',
                    out_channels=self._out_channels,
                    ksize=self._ksize,
                    stride=self._stride,
                    pad=self._pad,
                    nobias=self._nobias)

    @classmethod
    def register_chainer_impl(cls):
        return chainer.links.Deconvolution2D


class DepthwiseConvolution2D(Link):
    Input('in_array', (chainer.Variable,))
    Input('channel_multiplier', (int,))
    Input('ksize', (int,))
    Input('stride', (int,))
    Input('pad', (int,))
    Input('nobias', (bool,), select=[True, False])
    Output('out_array', (chainer.Variable,))

    is_image_node = True

    def call_init(self):
        return 'DepthwiseConvolution2D({in_channels}, {channel_multiplier}, ' \
               '{ksize}, {stride}, {pad}, {nobias}),' \
            .format(in_channels='None',
                    channel_multiplier=self._channel_multiplier,
                    ksize=self._ksize,
                    stride=self._stride,
                    pad=self._pad,
                    nobias=self._nobias)

    @classmethod
    def register_chainer_impl(cls):
        return chainer.links.DepthwiseConvolution2D


class BatchNormalization(Link):
    Input('in_array', (chainer.Variable,))
    Input('size', (int,))
    Input('decay', (float,))
    Input('eps', (float,))
    Input('use_gamma', (bool,), select=[True, False])
    Input('use_beta', (bool,), select=[True, False])
    Output('out_array', (chainer.Variable,))
    is_image_node = True

    def call_init(self):
        return 'BatchNormalization({size}, {decay}, {eps}, numpy.float32, {use_gamma}, {use_beta}),' \
            .format(size=self._size,
                    decay=self._decay,
                    eps=self._eps,
                    use_gamma=self._use_gamma,
                    use_beta=self._use_beta)

    @classmethod
    def register_chainer_impl(cls):
        return chainer.links.BatchNormalization
