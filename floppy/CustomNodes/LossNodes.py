from floppy.node import Node, Input, Output

import chainer


#TODO(fukatani) make abstract class

class SoftmaxCrossEntropy(Node):
    Input('InputArray', chainer.Variable)
    Output('OutArray', chainer.Variable)

    def run(self):
        # TODO(fukatani) link
        pass

