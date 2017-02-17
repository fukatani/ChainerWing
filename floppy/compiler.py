from floppy.templates import TEMPLATES
from floppy.node import Link, Function, Loss
from floppy.settings import ParamServer


class Compiler(object):
    def __call__(self, nodes, **kwargs):
        #TODO(fukatani)
        net_name = 'ExampleNet'
        init_impl = self.compile_init(nodes)
        call_impl = self.compile_call(nodes)
        net_file = open(net_name + '.py', 'w')
        net_file.write(TEMPLATES['NetTemplate']()(net_name, init_impl, call_impl))
        train_dict = {'BatchSize': ParamServer()['BatchSize'],
                      'Epoch': ParamServer()['Epoch'],
                      'GPU': ParamServer()['GPU'],
                      'Optimizer': ParamServer()['Optimizer']}
        net_file.write(TEMPLATES['TrainerTemplate']()(train_dict))

    def compile_init(self, nodes):
        links = []
        for node in nodes.values():
            if issubclass(type(node), Link):
                links.append('            l{0}={1}'.format(node.link_id, node.call_init()))
        return '\n'.join(links)

    def compile_call(self, nodes):
        call_all_loss = []
        for node in nodes.values():
            if issubclass(type(node), Loss):
                compiled_loss = self.compile_node(node, nodes)
                compiled_loss = "".join([func.call() for func in compiled_loss]) + "x" + ")" * len(compiled_loss)
                compiled_loss += node.call_end()
                call_all_loss.append(compiled_loss)

        return ", ".join(call_all_loss)

    def compile_node(self, cursor, nodes, decode=[]):
        decode.append(cursor)
        for connect in cursor.get_input_connections():
            if 'in_array' in connect['inputName']:
                return self.compile_node(connect.outputNode, nodes, decode)
        return decode
