from lib import util
from lib.node import InputNotAvailable
from lib.node import Link
from lib.node import Loss
from lib.subwindows.train_config import TrainParamServer
from lib.templates import TEMPLATES


class Compiler(object):
    def __call__(self, nodes, **kwargs):
        if not nodes:
            util.disp_error('Please place nodes and connect them'
                            ' before compilation.')
            return
        net_name = TrainParamServer()['NetName']
        init_impl = self.compile_init(nodes)
        if not init_impl:
            return False
        call_impl, pred_impl = self.compile_call(nodes)
        if not call_impl:
            return False
        classification = 'Class' in TrainParamServer()['TrainMode']
        net_file = open(net_name + '.py', 'w')
        net_file.write(TEMPLATES['NetTemplate']()(TrainParamServer()['NetName'],
                                                  init_impl,
                                                  call_impl,
                                                  pred_impl,
                                                  classification))
        net_file.write(TEMPLATES['TrainerTemplate']()(TrainParamServer()))
        return True

    def compile_init(self, nodes):
        links = []
        for node in nodes.values():
            if issubclass(type(node), Link):
                try:
                    links.append('            l{0}={1}'.
                                 format(node.link_id, node.call_init()))
                except:
                    util.disp_error(
                        'Unset parameter was found in {0}'.format(node))
                    return ''
        return '\n'.join(links)

    def compile_call(self, nodes):
        call_all_loss = []
        call_all_pred = []
        for node in nodes.values():
            if issubclass(type(node), Loss):
                chains = self.compile_node(node, nodes, [])
                loss = chains[0]
                funcs = chains[1:]

                try:
                    compiled_pred = "".join([func.call() for func in funcs])
                except InputNotAvailable:
                    util.disp_error('Unset parameter was found in {0}'.format(node))
                    return ''
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
