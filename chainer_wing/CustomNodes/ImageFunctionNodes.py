import chainer

from chainer_wing.node import Input, Output, Function


class AveragePooling2d(Function):
    Input('in_array', chainer.Variable)
    Input('ksize', int)
    Input('pad', int)
    Output('out_array', chainer.Variable)

    is_image_node = True

    def call(self):
        return self.ID + ' = average_pooling_2d(ksize={0}, pad={1}, x='.\
            format(self._ksize, self._pad)

    @classmethod
    def register_chainer_impl(cls):
        return chainer.functions.average_pooling_2d


class MaxPooling2d(Function):
    Input('in_array', chainer.Variable)
    Input('ksize', int)
    Input('pad', int)
    Output('out_array', chainer.Variable)

    is_image_node = True

    def call(self):
        return self.ID + ' = max_pooling_2d(ksize={0}, pad={1}, x='.\
            format(self._ksize, self._pad)

    @classmethod
    def register_chainer_impl(cls):
        return chainer.functions.max_pooling_2d
