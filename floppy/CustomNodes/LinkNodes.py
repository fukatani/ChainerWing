from floppy.node import Node, Input, Output

import chainer


#TODO(fukatani) make abstract class

class Linear(Node):
    Input('InputArray', chainer.Variable)
    Input('OutSize', int)
    Input('nobias', bool, select=[True, False])
    Output('OutArray', chainer.Variable)

    def run(self):
        # TODO(fukatani) link
        self._Int1
        self._Int2(self._Int1 + 1)


class Convolution(Node):
    Input('InputArray', chainer.Variable)
    Input('InChannels', int)
    Input('OutChannels', int)
    Input('nobias', bool, select=[True, False])
    Output('OutArray', chainer.Variable)

    def run(self):
        pass
