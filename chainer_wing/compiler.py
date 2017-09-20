from chainer_wing import util
from chainer_wing.node import InputNotAvailable
from chainer_wing.node import Link
from chainer_wing.node import Loss
from chainer_wing.subwindows.train_config import TrainParamServer
from chainer_wing.templates import TEMPLATES


class NoLossError(Exception):
    pass


class Compiler(object):
    def __call__(self, nodes, **kwargs):
        if not nodes:
            util.disp_error('Please place nodes and connect them'
                            ' before compilation.')
            return False
        init_impl = self.compile_init(nodes)
        if not init_impl:
            return False
        call_impl, pred_impl, lossID = self.compile_call(nodes)
        if not (call_impl and pred_impl):
            return False
        classification = 'Class' in TrainParamServer()['Task']
        net_file = open(TrainParamServer().get_net_name(), 'w')
        net_file.write(TEMPLATES['NetTemplate']()(TrainParamServer()['NetName'],
                                                  init_impl,
                                                  call_impl,
                                                  pred_impl,
                                                  lossID,
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
                                 format(node.get_name(), node.call_init()))
                except:
                    util.disp_error(
                        'Unset parameter was found in {0}'.format(node))
                    return ''
        return '\n'.join(links)

    def compile_call(self, nodes):
        call_all_loss = []
        call_all_pred = []
        loss = None
        for node in nodes.values():
            if not issubclass(type(node), Loss):
                continue

            chains = self.compile_node(node, nodes, [])
            loss = chains[0]
            funcs = chains[1:]
            compiled_pred = []
            previous_ID = ''
            try:
                for func in reversed(funcs):
                    if previous_ID:
                        pred_call = ''.join((' '*8, func.call(), previous_ID, ')'))
                    else:
                        pred_call = ''.join((' '*8, func.call(), 'x)'))
                    compiled_pred.append(pred_call)
                    previous_ID = func.get_name()
            except InputNotAvailable:
                util.disp_error('Unset parameter was found in {0}'.format(node))
                return ''

            compiled_pred.append('        return ' + previous_ID)
            compiled_pred = '\n'.join(compiled_pred)
            call_all_pred.append(compiled_pred)
            call_all_loss.append(loss.call())

        if loss is None:
            raise NoLossError('Please plase loss function.')
        return ', '.join(call_all_loss), ', '.join(call_all_pred), loss.get_name()

    def compile_node(self, cursor, nodes, decode):
        decode.append(cursor)
        for connect in cursor.get_input_connections():
            if 'in_array' in connect.input_name:
                return self.compile_node(connect.output_node, nodes, decode)
        return decode
