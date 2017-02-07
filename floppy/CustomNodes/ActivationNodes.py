from floppy.node import Node, Input, Output, Tag, abstractNode

import chainer


#TODO(fukatani) make abstract class

class Relu(Node):
    Input('InputArray', chainer.Variable)
    Output('OutArray', chainer.Variable)

    def run(self):
        # TODO(fukatani) link
        pass

