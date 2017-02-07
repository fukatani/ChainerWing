from floppy.node import Node, Input, Output, Tag, abstractNode
import time
import random

class AMyNode(Node):
    Input('Inta', int)
    Input('Intb', int)
    Input('Int1', int, select=[1,2,3,4])
    Input('Int3', int, select=[1,2,3,4])
    Output('Int2', int)

    def run(self):
        self._Int1
        self._Int2(self._Int1 + 1)





























class PlotNode2(Node):
    Input('XX', str)
    Output('YY', str)

    def __init__(self, *args, **kwargs):
        super(PlotNode2, self).__init__(*args, **kwargs)
        self.time = time.time()
        self.points = []
        self.counts = 0

    def check(self):
        t = time.time()
        if t - self.time > 3:
            self.time = t
            return True

    def run(self):
        super(PlotNode2, self).run()
        self.counts += 1
        self.points.append(
            (self.counts, (random.randint(5, 20), random.randint(5, 20), random.randint(5, 20), random.randint(5, 20))))

    def report(self):
        r = super(PlotNode2, self).report()
        r['template'] = 'PlotTemplate'
        r['points'] = self.points[:]
        r['keep'] = 'points'
        self.points = []
        return r
