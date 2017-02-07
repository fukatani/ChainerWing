from floppy.node import MetaNode, Node, InputInfo
from collections import OrderedDict

node = MetaNode('xxxxxxProxyNode', (Node,), {'inputs': []})
node.__inputs__ = OrderedDict()
node._addInput(data={'name': 'testInput',
                     'hints': None,
                     'select': None,
                     'list': None,
                     'default': '',
                     'varType': str,
                     'optional': False}, cls=node)

n = node(1,2)
n.setInput('testInput', 'foo')
print(n._testInput)
#n = node(1,2)
#print(n.inputs.values())
