import chainer

from chainer_wing.node import Input, Output, Link


class VGG16(Link):
    Input('in_array', (chainer.Variable,))
    Input('pretrained_model', (str,))
    Output('out_array', (chainer.Variable,))
    is_image_node = True

    def call_init(self):
        return 'VGG16Layers({pretrained_model}),' \
            .format(pretrained_model=self._pretrained_model)

    @classmethod
    def register_chainer_impl(cls):
        return chainer.links.VGG16Layers
