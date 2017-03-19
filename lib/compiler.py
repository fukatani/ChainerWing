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
            return False
        init_impl = self.compile_init(nodes)
        if not init_impl:
            return False
        call_impl, pred_impl = self.compile_call(nodes)
        if not (call_impl and pred_impl):
            return False
        classification = 'Class' in TrainParamServer()['Task']
        net_file = open(TrainParamServer().get_net_name(), 'w')
        net_file.write(TEMPLATES['NetTemplate']()(TrainParamServer()['NetName'],
                                                  init_impl,
                                                  call_impl,
                                                  pred_impl,
                                                  classification))
        net_file.write(TEMPLATES['OptimizerTemplate']()(TrainParamServer()))
        net_file.write(TEMPLATES['TrainerTemplate']()(TrainParamServer()))
        return True

    def compile_init(self, nodes):
        links = []
        for node in nodes.values():
            if issubclass(type(node), Link):
                try:
                    links.append('            {0}={1}'.
                                 format(node.node_id, node.call_init()))
                except:
                    util.disp_error(
                        'Unset parameter was found in {0}'.format(node))
                    return ''
        return '\n'.join(links)

    def compile_call(self, nodes):
        call_all_loss = []
        call_all_pred = []
        for node in nodes.values():
            if not issubclass(type(node), Loss):
                continue

            chains = self.compile_node(node, nodes, [])
            loss = chains[0]
            funcs = chains[1:]
            compiled_pred = []
            previous_node_id = ''
            try:
                for func in reversed(funcs):
                    if previous_node_id:
                        pred_call = ''.join((' '*8, func.call(), previous_node_id, ')'))
                    else:
                        pred_call = ''.join((' '*8, func.call(), 'x)'))
                    compiled_pred.append(pred_call)
                    previous_node_id = func.node_id
            except InputNotAvailable:
                util.disp_error('Unset parameter was found in {0}'.format(node))
                return ''

            compiled_pred.append('        return ' + previous_node_id)
            compiled_pred = '\n'.join(compiled_pred)
            call_all_pred.append(compiled_pred)
            call_all_loss.append(loss.call())

        return ', '.join(call_all_loss), ', '.join(call_all_pred)

    def compile_node(self, cursor, nodes, decode):
        decode.append(cursor)
        for connect in cursor.get_input_connections():
            if 'in_array' in connect.input_name:
                return self.compile_node(connect.output_node, nodes, decode)
        return decode
