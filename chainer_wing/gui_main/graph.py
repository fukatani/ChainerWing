from collections import OrderedDict

from chainer.utils import type_check

from chainer_wing import compiler
from chainer_wing import runner
from chainer_wing.node import Node, MetaNode
from chainer_wing.node import NODECLASSES
from chainer_wing import util
from chainer_wing.subwindows.train_config import TrainParamServer


def dummy(node_class):
    return node_class


class Graph(object):
    """
    Managing all nodes. This class provides interfaces for spawning/removing nodes and connections.
    It also provides interfaces for spawning and connecting to graph interpreters and for communicating with them.
    Since a Graph interpreter is nothing but a small program able to load a Graph instance and listening to commands,
    the Graph class also provides methods for executing the implemented logic.
    """
    nextFreeNodeID = 0
    nodes = {}

    def __init__(self, painter=None):
        self.slave = False
        self.statusLock = None
        self.connected = False
        self.nextFreeNodeID = 0
        self.nodes = {}
        self.runner = None
        self.status = None
        # from self to other
        self.connections = {}
        # from other to self
        self.reverseConnections = {}
        # self.statusLock = Lock()
        if painter:
            self.painter = painter
            painter.registerGraph(self)
        else:
            self.painter = dummy

    def __getattr__(self, item):
        return super(Graph, self).__getattr__(item)

    def spawnNode(self, node_class, connections=None, position=(0, 0),
                  silent=False, id=None, name=None):
        """
        Spawns a new node of a given class at a given position with optional connections to other nodes.
        :param node_class: subclass object of 'Node'.
        :param connections: Dictionary
        :param position: Tuple of two integer representing the nodes position on the screen relative the the graph's
        origin.
        :param silent: Boolean. Suppresses all notifications that a node was spawned if True.
        :return: newly created Node instance.
        """
        newNode = node_class(self, id)
        newNode.name = name
        self.reverseConnections[newNode] = set()
        self.connections[newNode] = set()
        if connections:
            self._spawnConnections(connections, newNode)
        try:
            self.painter.registerNode(newNode, position, silent)
        except AttributeError:
            pass
        self.nodes[newNode.ID] = newNode

        return newNode

    def createSubGraphNode(self, name, subgraph_save, input_relays,
                           output_relays, spawnAt=None):
        inps = []
        names = set()
        for info, x, y in input_relays:
            iName = info.name
            while iName in names:
                iName += '_'
            names.add(iName)
            inps.append({'name': iName,
                         'var_type': info.var_type,
                         'hints': info.hints,
                         'value': None,
                         'select': info.select,
                         'list': info.list,
                         'optional': info.optional})
        outs = []
        names = set()
        for info, x, y in output_relays:
            oName = info.name
            while oName in names:
                oName += '_'
            names.add(oName)
            outs.append({'name': oName,
                         'var_type': info.var_type,
                         'hints': info.hints,
                         'value': None,
                         'select': info.select,
                         'list': info.list,
                         'optional': info.optional})
        node_class = self.createCustomNodeClass(name, inps, outs)
        if spawnAt:
            return self.spawnNode(node_class, position=spawnAt)

    def createCustomNodeClass(self, name, inputs, outputs, parents=(Node,)):
        node_class = MetaNode(name, parents, {})
        node_class.__inputs__ = OrderedDict()
        node_class.__outputs__ = OrderedDict()
        for inp in inputs:
            node_class._addInput(data=inp, cls=node_class)
        for out in outputs:
            node_class._addOutput(data=out, cls=node_class)
        NODECLASSES[name] = node_class
        return node_class

    def _spawnConnections(self, connections, newNode):
        try:
            outs = connections['outputs']
        except KeyError:
            pass
        else:
            for out in outs:
                self.connect(newNode, out[0], out[1], out[2])
        try:
            ins = connections['inputs']
        except KeyError:
            pass
        else:
            for inp in ins:
                self.connect(inp[1], inp[2], newNode, inp[0])

    def connect(self, outNode, out, inpNode, inp):
        """
        Creates a logical connection between two nodes.
        Before the actual connection is established checks will be performed
         to make sure that the input is actually legal.
        If necessary, previously created connections that are in conflict with the new one will be deleted.
        :param outNode: Node instance that has the output involved in the connection.
        :param out: string representing the Output's name.
        :param inpNode: Node instance that has the input involved in the connection.
        :param inp: string representing the Input's name.
        :return:
        """
        if isinstance(outNode, str):
            outNode = self.nodes[outNode]
        if isinstance(inpNode, str):
            inpNode = self.nodes[inpNode]
        outInfo = outNode.getOutputInfo(out)
        inpInfo = inpNode.getInputInfo(inp)
        if not set(outInfo.var_type) & set(inpInfo.var_type):
            raise TypeError(
                'Output \'{}\' of node {} and input \'{}\' of not {} don\'t match.'.format(
                    out,
                    str(outNode),
                    inp,
                    str(inpNode)))
        conn = Connection(outNode, out, inpNode, inp)
        for oldCon in self.reverseConnections[inpNode]:
            if oldCon.input_name == inp:
                self.reverseConnections[inpNode].remove(oldCon)
                self.connections[oldCon.output_node].remove(oldCon)
                break
        inpInfo.setConnected(True)
        self.connections[outNode].add(conn)
        self.reverseConnections[inpNode].add(conn)
        # self.update()

    def getConnectionsFrom(self, node):
        """
        Returns a list of all connections that involve 'node's' outputs.
        :param node:
        :return: List of connection dictionaries.
        :rtype: list
        """
        return self.connections[node]

    def getConnectionsTo(self, node):
        """
        Returns a list of all connections that involve 'node's' inputs.
        :param node:
        :return:
        """
        return self.reverseConnections[node]

    def getConnectionOfInput(self, inp):
        """
        Returns the connection involving an input
        :param inp: InputInfo instance.
        :return: Connection instance.
        """
        for con in self.getConnectionsTo(
                self.nodes[inp.ID.partition(':')[0]]):
            if con.input_name == inp.name:
                return con

    def getConnectionsOfOutput(self, output):
        """
        Returns a list of connections involving an output.
        :param output: OutputInfo instance.
        :return: list of Connection instances.
        """
        node = self.nodes[output.ID.partition(':')[0]]
        return [con for con in self.getConnectionsFrom(node) if
                con.output_name == output.name]

    def update(self):
        """
        Updates and repaints the painter instance.
        WARNING: Only call this method from the main thread.
        Other threads must use the Graph.requestUpdate method which
        has a slight delay.
        :return:
        """
        try:
            self.painter.repaint()
            self.painter.update()
        except AttributeError:
            pass

    def compile(self):
        """
        Compile the Graph as chainer code.
        :return: If compilation was succeeded, return True.
        """
        try:
            result = compiler.Compiler()(self.nodes)
        except util.ExistsInvalidParameter as error:
            util.disp_error('{0} is not set @{1}'.format(error.args[1][1:],
                                                         error.args[0]))
            self.nodes[error.args[0]].runtime_error_happened = True
            return False
        except compiler.NoLossError:
            util.disp_error('Please place loss function.')
            return False
        return result

    def run(self):
        """
        Run compiled chainer code.
        :return:
        """
        self.clear_error()
        if TrainParamServer()['GPU'] and not util.check_cuda_available():
            return

        try:
            self.runner = runner.TrainRunner()
        except SyntaxError:
            util.disp_error('Generated chainer script ({}) is not valid.'
                            .format(TrainParamServer().get_net_name()))
            return
        try:
            self.runner.run()
        except util.AbnormalDataCode as error:
            util.disp_error(str(error.args[0][0]) + ' @' +
                            TrainParamServer()['TrainData'])
        except ValueError as error:
            util.disp_error('{0}\n'.format(error.args[0]) +
                'Irregal data was found @' + TrainParamServer()['TrainData'])
        except FileNotFoundError as error:
            util.disp_error('{} is not found.'
                            .format(error.filename))
        except util.UnexpectedFileExtension:
            util.disp_error('Unexpected file extension was found.'
                            'data should be ".csv", ".npz" or ".py"')
        except type_check.InvalidType as error:
            last_nodeID = util.get_executed_last_node()
            util.disp_error(str(error.args) + ' @node: ' + last_nodeID)
            self.nodes[last_nodeID].runtime_error_happened = True

    def clear_error(self):
        for node in self.nodes.values():
            node.runtime_error_happened = False

    def to_dict(self, subgraph=None):
        """
        Encodes the graph as a JSON string and returns the string.
        :param subgraph: Returns whole graph is 'subgraph=None' else only the nodes corresponding to the subgraph.
        :return:
        """
        if subgraph:
            return [(node.ID, node.to_dict()) for node in self.nodes.values()
                    if node.subgraph == subgraph]
        return [(node.ID, node.to_dict()) for node in self.nodes.values()]

    def killRunner(self):
        """
        Kill chainer execution thread.
        :return:
        """
        if self.runner is not None:
            self.runner.kill()

    def load_from_dict(self, graph_state):
        """
        Reconstruct a Graph instance from a JSON string representation
        created by the Graph.to_json() method.
        :param graph_state:
        :return: Dictionary mapping the saved nodeIDs to the newly created
        nodes's IDs.
        """
        idMap = {}
        for id, nodeData in graph_state:
            try:
                restoredNode = self.spawnNode(NODECLASSES[nodeData['class']],
                                              position=nodeData['position'],
                                              id=id,
                                              name=nodeData['name'])
            except KeyError:
                try:
                    dynamic = nodeData['dynamic']
                except KeyError:
                    dynamic = False
                if not dynamic:
                    util.disp_error('Unknown Node class **{}**'
                                    .format(nodeData['class']))
                    continue
                else:
                    print('I need to create a custom class now.')
            else:
                try:
                    restoredNode.subgraph = nodeData['subgraph']
                except KeyError:
                    restoredNode.subgraph = 'main'
            idMap[id] = restoredNode.ID
            inputs = nodeData['inputs']
            for input in inputs:
                if input[1] in ('bool', 'int', 'float'):
                    restoredNode.inputs[input[0]].set_value(input[-1])
                    # outputs = nodeData['outputs']
                    # for output in outputs:
                    #     restoredNode.outputs[output[0]].setDefault(output[-1])
        for id, nodeData in graph_state:
            for input_name, outputID in nodeData['inputConnections'].items():
                output_node, output_name = outputID.split(':O')
                try:
                    output_node = idMap[output_node]
                    self.connect(str(output_node), output_name, str(idMap[id]),
                                 input_name)
                except KeyError:
                    print('Warning: Could not create connection '
                          'due to missing node.')

        self.update()
        return idMap

    def getPinWithID(self, pinID):
        """
        Get a reference to the pin object with pinID.
        :param pinID: string representing a Pin instance's ID.
        :return: Pin instance.
        """
        pinName, node = self.getNodeFromPinID(pinID)
        try:
            return node.getInputPin(pinName)
        except KeyError:
            return node.getOutputPin(pinName)

    def getNodeFromPinID(self, pinID):
        """
        Get a reference to the Node instance that has the pin object with pinID.
        :param pinID: string representing a Pin instance's ID.
        :return: Node instance.
        """
        nodeID, pinName = pinID.split(':')
        return pinName[1:], self.nodes[nodeID]

    def removeConnection(self, pinID, from_self):
        """
        Remove the connection that involves the Pin instance with pinID.
        :param pinID: string representing a Pin instance's ID.
        :return:
        """
        pinName, node = self.getNodeFromPinID(pinID)
        thisConn = None
        if from_self:
            connections = self.connections[node]
        else:
            connections = self.reverseConnections[node]
        for conn in connections:
            if from_self:
                target_pin = conn.output_name
            else:
                target_pin = conn.input_name
            if target_pin == pinName:
                thisConn = conn
                break
        if thisConn:
            if from_self:
                self.connections[node].remove(thisConn)
                self.reverseConnections[conn.input_node].remove(thisConn)
            else:
                self.reverseConnections[node].remove(thisConn)
                self.connections[conn.output_node].remove(thisConn)

    def deleteNode(self, node):
        """
        Delete the node.
        :param node: Node instance.
        :return:
        """
        for inp in node.inputs.values():
            self.removeConnection(inp.ID, from_self=False)
        for out in node.outputs.values():
            self.removeConnection(out.ID, from_self=True)
        del self.nodes[node.ID]


class Connection(object):
    """
    Class representing a connection between nodes.
    Storing information about involved Inputs and Outputs.
    """

    def __init__(self, output_node, output_name, input_node, input_name):
        self.output_node = output_node
        self.output_name = output_name
        self.input_node = input_node
        self.input_name = input_name
