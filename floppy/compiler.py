from floppy.node import Link, Loss
from floppy.templates import TEMPLATES
from floppy.train_configuration import TrainParamServer
from PyQt5.QtWidgets import QErrorMessage


class Compiler(object):
    def __call__(self, nodes, **kwargs):
        if not nodes:
            error = QErrorMessage()
            error.showMessage('Please place node and connect them before compile.')
            error.exec_()
            return
        net_name = TrainParamServer()['NetName']
        init_impl = self.compile_init(nodes)
        call_impl, pred_impl = self.compile_call(nodes)
        classification = 'Class' in TrainParamServer()['TrainMode']
        net_file = open(net_name + '.py', 'w')
        net_file.write(TEMPLATES['NetTemplate']()(net_name,
                                                  init_impl,
                                                  call_impl,
                                                  pred_impl,
                                                  classification))
        net_file.write(TEMPLATES['TrainerTemplate']()(TrainParamServer()))

    def compile_init(self, nodes):
        links = []
        for node in nodes.values():
            if issubclass(type(node), Link):
                links.append('            l{0}={1}'.format(node.link_id, node.call_init()))
        return '\n'.join(links)

    def compile_call(self, nodes):
        call_all_loss = []
        call_all_pred = []
        for node in nodes.values():
            if issubclass(type(node), Loss):
                chains = self.compile_node(node, nodes, [])
                loss = chains[0]
                funcs = chains[1:]

                compiled_pred = "".join([func.call() for func in funcs])
                compiled_pred += 'x' + ')' * (len(funcs))
                call_all_pred.append(compiled_pred)

                compiled_loss = loss.call() + node.call_end()
                call_all_loss.append(compiled_loss)

        return ', '.join(call_all_loss), ', '.join(call_all_pred)

    def compile_node(self, cursor, nodes, decode):
        decode.append(cursor)
        for connect in cursor.get_input_connections():
            if 'in_array' in connect.input_name:
                return self.compile_node(connect.output_node, nodes, decode)
        return decode
