import json
from collections import OrderedDict

from lib import compiler
from lib import runner
from lib.node import ControlNode, Node, MetaNode
from lib.node import NODECLASSES


def dummy(node_class):
    return node_class


class Graph(object):
    """
    Class for managing all nodes. The class provides interfaces for spawning/removing nodes and connections.
    It also provides interfaces for spawning and connecting to graph interpreters and for communicating with them.
    Since a Graph interpreter is nothing but a small program able to load a Graph instance and listening to commands,
    the Graph class also provides methods for executing the implemented logic.
    """
    nextFreeNodeID = 0
    nodes = {}

    def __init__(self, painter=None):
        self.slave = False
        self._requestUpdate = False
        self._requestReport = ''
        self.currentReport = ''
        self.runningNodes = []
        self.statusLock = None
        self.connected = False
        self.nextFreeNodeID = 0
        self.nodes = {}
        self.STOREDVALUES = {}
        self.connections = {}
        self.runner = runner.Runner()
        self.status = None
        self.reverseConnections = {}
        # self.statusLock = Lock()
        if painter:
            self.painter = painter
            painter.registerGraph(self)
        else:
            self.painter = dummy

    def __getattr__(self, item):
        if item == 'newID':
            newID = self.nextFreeNodeID
            self.nextFreeNodeID += 1
            return newID
        else:
            return super(Graph, self).__getattr__(item)

    def requestUpdate(self):
        """
        Tells the graph painter that changes to the graph were made that require a redraw.
        Use this method instead of a direct call of the painter update method if the request is not made by the main
        thread.
        :return:
        """
        self._requestUpdate = True

    def requestReport(self, nodeID):
        self._requestReport = nodeID

    def getReport(self):
        r = self.currentReport
        self.currentReport = {}
        return r

    def needsUpdate(self):
        """
        Called by the painter instance periodically to check whether a repaint was requested by another thread.
        :return:
        """
        if self.connected:
            status = self.status
            if status:
                IDs = status['STATUS']['ran']
                self.currentReport = status['REPORT']
                if IDs:
                    return True
        if self._requestUpdate:
            self._requestUpdate = False
            return True

    def spawnNode(self, nodeClass, connections=None, position=(0, 0),
                  silent=False, useID=False):
        """
        Spawns a new node of a given class at a given position with optional connections to other nodes.
        :param nodeClass: subclass object of 'Node'.
        :param connections: Dictionary
        :param position: Tuple of two integer representing the nodes position on the screen relative the the graph's
        origin.
        :param silent: Boolean. Suppresses all notifications that a node was spawned if True.
        :return: newly created Node instance.
        """
        # nodeClass = self.decorator(nodeClass, position)
        newNode = nodeClass(self.newID, self)
        if useID:
            newNode.ID = useID
        self.reverseConnections[newNode] = set()
        self.connections[newNode] = set()
        if connections:
            self._spawnConnections(connections, newNode)
        try:
            self.painter.registerNode(newNode, position, silent)
        except AttributeError:
            pass
        self.nodes[newNode.ID] = newNode
        self.newestNode = newNode

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
                         'default': None,
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
                         'default': None,
                         'select': info.select,
                         'list': info.list,
                         'optional': info.optional})
        nodeClass = self.createCustomNodeClass(name, inps, outs)
        if spawnAt:
            return self.spawnNode(nodeClass, position=spawnAt)

    def createCustomNodeClass(self, name, inputs, outputs, parents=(Node,)):
        NodeClass = MetaNode(name, parents, {})
        NodeClass.__inputs__ = OrderedDict()
        NodeClass.__outputs__ = OrderedDict()
        for inp in inputs:
            NodeClass._addInput(data=inp, cls=NodeClass)
        for out in outputs:
            NodeClass._addOutput(data=out, cls=NodeClass)
        NODECLASSES[name] = NodeClass
        return NodeClass

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
        Before the actual connection is established checks will be performed to make sure that the input is actually
        legal.
        If necessary, previously created connections that are in conflict with the new one will be deleted.
        :param outNode: Node instance that has the output involved in the connection.
        :param out: string representing the Output's name.
        :param inpNode: Node instance that has the input involved in the connection.
        :param inp: string representing the Input's name.
        :return:
        """
        if type(outNode) == str:
            outNode = self.nodes[int(outNode)]
        if type(inpNode) == str:
            inpNode = self.nodes[int(inpNode)]
        outInfo = outNode.getOutputInfo(out)
        inpInfo = inpNode.getInputInfo(inp)
        # if not outInfo.var_type == inpInfo.var_type:
        if not issubclass(outInfo.var_type, inpInfo.var_type) and not issubclass(
                inpInfo.var_type, outInfo.var_type):
            raise TypeError(
                'Output \'{}\' of node {} and input \'{}\' of not {} don\'t match.'.format(
                    out,
                    str(outNode),
                    inp,
                    str(inpNode)))
        # print('Connect output \'{1}\' of node {0} to input \'{3}\' of node {2}'.format(str(outNode),
        #                                                                                out,
        #                                                                                str(inpNode),
        #                                                                                inp))
        conn = Connection(outNode, out, inpNode, inp)
        if not issubclass(type(inpNode), ControlNode) or not inp == 'Control':
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
                self.nodes[int(inp.ID.partition(':')[0])]):
            if con.input_name == inp.name:
                return con

    def getConnectionsOfOutput(self, output):
        """
        Returns a list of connections involving an output.
        :param output: OutputInfo instance.
        :return: list of Connection instances.
        """
        node = self.nodes[int(output.ID.partition(':')[0])]
        return [con for con in self.getConnectionsFrom(node) if
                con.output_name == output.name]

    def update(self):
        """
        Updates and repaints the painter instance.
        WARNING: Only call this method from the main thread. Other threads must use the Graph.requestUpdate method which
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
        :return:
        """
        compiler.Compiler()(self.nodes)

    def run(self):
        self.runner.run(do_train=True)

    def print(self, message):
        print(message)

    def save(self, fp):
        """
        Saves the graph as a JSON string to the disk
        :param fp: file pointer for writing JSON.
        :return:
        """
        net_state = self.to_json()
        fp.write(net_state)

    def to_json(self, subgraph=None):
        """
        Encodes the graph as a JSON string and returns the string.
        :param subgraph: Returns whole graph is 'subgraph=None' else only the nodes corresponding to the subgraph.
        :return:
        """
        if subgraph:
            return json.dumps(
                [(node.ID, node.save()) for node in self.nodes.values() if
                 node.subgraph == subgraph], sort_keys=True)
        return json.dumps(
            [(node.ID, node.save()) for node in self.nodes.values()],
            sort_keys=True)

    def killRunner(self):
        """
        Send KILL command to the graph interpreter telling it to terminate itself.
        :return:
        """
        self.runner.kill()

    def load_from_json(self, line, callback=None):
        """
        :param line: string
        :param callback:
        :return:
        """
        graph_state = json.loads(line)
        self.loadState(graph_state, callback)

    def loadState(self, graph_state, callback=None, reuseIDs=False):
        """
        Reconstruct a Graph instance from a JSON string representation
        created by the Graph.to_json() method.
        :param graph_state:
        :return: Dictionary mapping the saved nodeIDs to the newly created
        nodes's IDs.
        """
        idMap = {}
        for id, nodeData in graph_state:
            useID = id if reuseIDs else False
            try:
                restoredNode = self.spawnNode(NODECLASSES[nodeData['class']],
                                              position=nodeData['position'],
                                              silent=True, useID=useID)
            except KeyError:
                try:
                    dynamic = nodeData['dynamic']
                except KeyError:
                    dynamic = False
                if not dynamic:
                    if callback:
                        callback('Unknown Node class **{}**'.format(
                            nodeData['class']))
                    else:
                        raise Exception('Unknown Node class <{}>.'.format(
                            nodeData['class']))
                    continue
                else:
                    print('I need to create a custom class now.')
            else:
                try:
                    restoredNode.subgraph = nodeData['subgraph']
                except KeyError:
                    restoredNode.subgraph = 'main'
            idMap[int(id)] = restoredNode.ID
            inputs = nodeData['inputs']
            for input in inputs:
                if input[1] in ('bool', 'int', 'float'):
                    restoredNode.inputs[input[0]].setDefault(input[-1])
                    # outputs = nodeData['outputs']
                    # for output in outputs:
                    #     restoredNode.outputs[output[0]].setDefault(output[-1])
        for id, nodeData in graph_state:
            id = int(id)
            for input_name, outputID in nodeData['inputConnections'].items():
                if input_name == 'Control':
                    continue
                output_node, output_name = outputID.split(':O')
                try:
                    output_node = idMap[int(output_node)]
                    # print(id, nodeData['inputConnections'], output_node, output_name)

                    self.connect(str(output_node), output_name, str(idMap[id]),
                                 input_name)
                except KeyError:
                    print(
                        'Warning: Could not create connection due to missing node.')

            for output_name, inputIDs in nodeData['outputConnections'].items():
                for inputID in inputIDs:
                    if 'Control' not in inputID:
                        continue
                    input_node, input_name = inputID.split(':I')
                    try:
                        input_node = idMap[int(input_node)]
                        # print(id, nodeData['inputConnections'], output_node, output_name)
                        self.connect(str(idMap[id]), output_name,
                                     str(input_node), input_name)
                    except KeyError:
                        print(
                            'Warning: Could not create connection due to missing node.')

        self.update()
        return idMap

    def updateState(self, data, reuseIDs=False):
        """
        Updates the current the Graph instance with the json representation of another, similar Graph instance.
        New Node instances are created for Nodes in the json data that are not already present.
        Also, all connections are removed and re-instanciated based on the provided json data.
        :param data:
        :return:
        """
        self.connections = {key: set() for key in self.connections.keys()}
        self.reverseConnections = {key: set() for key in
                                   self.reverseConnections.keys()}
        idMap = {}
        removeNodes = set(self.nodes.keys())
        for id, nodeData in data:
            useID = id if reuseIDs else False
            idMap[int(id)] = int(id)
            if not int(id) in self.nodes.keys():
                restoredNode = self.spawnNode(NODECLASSES[nodeData['class']],
                                              position=nodeData['position'],
                                              silent=True, useID=useID)
                thisNode = restoredNode
            else:
                thisNode = self.nodes[int(id)]
            removeNodes.discard(thisNode.ID)
            inputs = nodeData['inputs']
            outputs = nodeData['outputs']
            for input in inputs:
                thisNode.inputs[input[0]].setDefault(input[-1])
            for output in outputs:
                thisNode.outputs[output[0]].setDefault(output[-1])
        for id, nodeData in data:
            id = int(id)
            for input_name, outputID in nodeData['inputConnections'].items():
                if input_name == 'Control':
                    continue
                output_node, output_name = outputID.split(':O')
                output_node = idMap[int(output_node)]
                # print(id, nodeData['inputConnections'], output_node, output_name)
                self.connect(str(output_node), output_name, str(idMap[id]),
                             input_name)

            for output_name, inputIDs in nodeData['outputConnections'].items():
                for inputID in inputIDs:
                    if 'Control' not in inputID:
                        continue
                    input_node, input_name = inputID.split(':I')
                    input_node = idMap[int(input_node)]
                    # print(id, nodeData['inputConnections'], output_node, output_name)
                    self.connect(str(idMap[id]), output_name, str(input_node),
                                 input_name)
        for nodeID in removeNodes:
            self.deleteNode(self.nodes[nodeID])
        self.update()
        return idMap

    def loadDict(self, saveState):
        """
        Reconstruct a Graph instance from a JSON string representation
        created by the Graph.to_json() method.
        :param saveState:
        :return: Dictionary mapping the saved nodeIDs to the newly created nodes's IDs.
        """
        idMap = {}
        for id, nodeData in saveState.items():
            restoredNode = self.spawnNode(NODECLASSES[nodeData['class']],
                                          position=nodeData['position'],
                                          silent=True)
            idMap[int(id)] = restoredNode.ID
            inputs = nodeData['inputs']
            outputs = nodeData['outputs']
            for input in inputs:
                restoredNode.inputs[input[0]].setDefault(input[-1])
            for output in outputs:
                restoredNode.outputs[output[0]].setDefault(output[-1])
        for id, nodeData in saveState.items():
            id = int(id)
            for input_name, outputID in nodeData['inputConnections'].items():
                if input_name == 'Control':
                    continue
                output_node, output_name = outputID.split(':O')
                output_node = idMap[int(output_node)]
                # print(id, nodeData['inputConnections'], output_node, output_name)
                self.connect(str(output_node), output_name, str(idMap[id]),
                             input_name)

            for output_name, inputIDs in nodeData['outputConnections'].items():
                for inputID in inputIDs:
                    if 'Control' not in inputID:
                        continue
                    input_node, input_name = inputID.split(':I')
                    input_node = idMap[int(input_node)]
                    # print(id, nodeData['inputConnections'], output_node, output_name)
                    self.connect(str(idMap[id]), output_name, str(input_node),
                                 input_name)

        self.update()
        return idMap

    def getPinWithID(self, pinID):
        """
        Get a reference to the pin object with pinID.
        :param pinID: string representing a Pin instance's ID.
        :return: Pin instance.
        """
        nodeID, pinName = pinID.split(':')
        pinName = pinName[1:]
        node = self.nodes[int(nodeID)]
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
        pinName = pinName[1:]
        return self.nodes[int(nodeID)]

    def getNewestNode(self):
        """
        Get a reference to the node instance that was created last.
        :return:
        """
        return self.newestNode

    def removeConnection(self, pinID):
        """
        Remove the connection that involves the Pin instance with pinID.
        :param pinID: string representing a Pin instance's ID.
        :return:
        """
        node = self.getNodeFromPinID(pinID)
        pinName = self.getPinWithID(pinID).name
        thisConn = None
        for conn in self.reverseConnections[node]:
            if any([conn.input_name == pinName, conn.output_name == pinName]):
                thisConn = conn
                break
        if thisConn:
            self.reverseConnections[node].remove(thisConn)
            self.connections[conn.output_node].remove(thisConn)
            return
        thisConn = None
        for conn in self.connections[node]:
            if any([conn.input_name == pinName, conn.output_name == pinName]):
                thisConn = conn
                break
        if thisConn:
            self.connections[node].remove(thisConn)
            self.reverseConnections[conn.input_node].remove(thisConn)

    def deleteNode(self, node):
        """
        Delete the node.
        :param node: Node instance.
        :return:
        """
        for inp in node.inputs.values():
            self.removeConnection(inp.ID)
        for out in node.outputs.values():
            self.removeConnection(out.ID)
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
