from floppy.templates import TEMPLATES
from floppy.node import Link, Function, Loss

class Compiler(object):
    def __call__(self, nodes):
        links = []
        i = 0
        for node in nodes.values():
            if issubclass(type(node), Link):
                links.append('l{0}={1}'.format(i, node.run()))
                i += 1

        net_name = 'ExampleNet'
        init_impl = '\n'.join(links)
        call_impl = 'l1(x)'
        net_file = open(net_name + '.py', 'w')
        net_file.write(TEMPLATES['NetTemplate']()(net_name, init_impl, call_impl))
