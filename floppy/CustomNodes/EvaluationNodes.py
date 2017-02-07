from floppy.node import Node, Input, Output, Tag, abstractNode

import chainer
import numpy

#TODO(fukatani) make abstract class

class Accuracy(Node):
    Input('InputArray', chainer.Variable)
    Output('OutArray', numpy.ndarray)

    def run(self):
        # TODO(fukatani) link
        pass
