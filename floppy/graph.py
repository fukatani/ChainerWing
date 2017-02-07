import json
import zlib
import io
import time
from collections import OrderedDict
from floppy.node import ControlNode, Node, MetaNode
from floppy.runner import Runner, sendCommand, RGIConnection
from socket import AF_INET, SOCK_STREAM, socket #, SHUT_RDWR, timeout, SHUT_RDWR, SO_REUSEADDR, SOL_SOCKET
from floppy.node import NODECLASSES
from threading import Thread, Lock
from queue import Queue
import struct


def dummy(nodeClass):
    return nodeClass


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
        self.executedBuffer = []
        self.currentlyRunning = []
        self.currentReport = ''
        self.runningNodes = []
        self.statusLock = None
        self.connected = False
        self.nextFreeNodeID = 0
        self.nodes = {}
        self.STOREDVALUES = {}
        self.connections = {}
        self.runner = None
        self.status = None
        self.reverseConnections = {}
        # self.statusLock = Lock()
        if painter:
            self.painter = painter
            painter.registerGraph(self)
        else:
            self.painter = dummy

    def spawnAndConnect(self, port=8079):
        """
        Spawns a new graph interpreter instance and establishes a TCP/IP connection to it.
        :return:
        """
        if not self.runner:
            self.runner = Runner()
        self.connect2RemoteRunner(host='127.0.0.1', port=port)
        self.slave = True

    def connect2RemoteRunner(self, host='127.0.0.1', port=8079):
        self.cmdHost = host
        self.cmdPort = int(port)
        self.slave = False
        self.rgiConnection = RGIConnection()
        self.rgiConnection.connect(self.cmdHost, self.cmdPort)
        # self.connect2Runner(host, port)
        # self.statusLock = Lock()
        # self.statusQueue = Queue(100)
        self.connected = True
        # self.statusListener = StatusListener(self, self.clientSocket, self.statusQueue, self.statusLock)

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
            # IDs = self.requestRemoteStatus()
            # status = self.requestRemoteStatus()
            self.requestRemoteStatus()
            status = self.status
            if status:
                IDs = status['STATUS']['ran']
                self.currentlyRunning = status['STATUS']['running']
                self.currentReport = status['REPORT']
                if IDs:
                    self.executedBuffer += IDs
                    return True
        if self._requestUpdate:
            self._requestUpdate = False
            return True

    def spawnNode(self, nodeClass, connections=None, position=(0, 0), silent=False, useID=False):
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

    def createSubGraphNode(self, name, subgraphSave, inputRelays, outputRelays, spawnAt=None):
        inps = []
        names = set()
        for info, x, y in inputRelays:
            iName = info.name
            while iName in names:
                iName += '_'
            names.add(iName)
            inps.append({'name': iName,
                         'varType': info.varType,
                         'hints': info.hints,
                         'default': None,
                         'select': info.select,
                         'list': info.list,
                         'optional': info.optional})
        outs = []
        names = set()
        for info, x, y in outputRelays:
            oName = info.name
            while oName in names:
                oName += '_'
            names.add(oName)
            outs.append({'name': oName,
                         'varType': info.varType,
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
        # if not outInfo.varType == inpInfo.varType:
        if not issubclass(outInfo.varType, inpInfo.varType) and not issubclass(inpInfo.varType, outInfo.varType):
            raise TypeError('Output \'{}\' of node {} and input \'{}\' of not {} don\'t match.'.format(out,
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
                if oldCon['inputName'] == inp:
                    self.reverseConnections[inpNode].remove(oldCon)
                    self.connections[oldCon['outputNode']].remove(oldCon)
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
        for con in self.getConnectionsTo(self.nodes[int(inp.ID.partition(':')[0])]):
            if con['inputName'] == inp.name:
                return con

    def getConnectionsOfOutput(self, output):
        """
        Returns a list of connections involving an output.
        :param output: OutputInfo instance.
        :return: list of Connection instances.
        """
        node = self.nodes[int(output.ID.partition(':')[0])]
        return [con for con in self.getConnectionsFrom(node) if con['outputName'] == output.name]


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

    def getExecutionHistory(self):
        """
        Returns the current execution history: a list of nodeIDs in the order they were executed in.
        :return: list of nodIDs.
        """
        # self.statusLock.acquire()
        tT = time.time()
        history = {i: tT-t for i, t in self.executedBuffer if tT - t < 15}
        self.executedBuffer = [(i, t) for i, t in self.executedBuffer if tT - t < 15]
        if history:
            self.requestUpdate()
        # self.statusLock.release()
        return history, self.executedBuffer[-1] if self.executedBuffer else ('','')

    def getRunningNodes(self):
        return self.currentlyRunning


    def execute(self):
        """
        Execute the Graph instance.

        First, the execution loop will set itself up to terminate after the first iteration.
        Next, every node is given the chance to run if all prerequisites are met.
        If a node is executed, the loop termination criterion will be reset to allow an additional iteration over all
        nodes.
        If no node is execute during one iteration, the termination criterion will not be reset and the execution loop
        terminates.
        :return:
        """
        if not self.connected:
            self.spawnAndConnect()
        self.push2Runner()
        time.sleep(1)
        self.unpauseRunner()
        # running = True
        # i = 0
        # while running:
        #     i += 1
        #     print('\nExecuting iteration {}.'.format(i))
        #     running = False
        #     for node in self.nodes.values():
        #         checked = node.check()
        #         running = checked if not running else True
        #         if checked:
        #             node.run()
        #             node.notify()

    def runNodePar(self, node, cb=None, arg=None):
        self.runningNodes.append(node.ID)
        t = NodeThread(node, cb, arg)
        # t.join()

    # def testRun(self):
    #     if not self.runner:
    #         self.runner = Runner()
    #     sendCommand('PAUSE', self.cmdHost, self.cmdPort)
    #     data = self.serialize()
    #     self.sendUpdate(data)
    #     sendCommand('UPDATE', self.cmdHost, self.cmdPort)
    #     import time
    #     time.sleep(.5)
    #     sendCommand('UNPAUSE', self.cmdHost, self.cmdPort)
    #     return
    #
    #     import time
    #     time.sleep(2)
    #     sendCommand('PAUSE')
    #     time.sleep(1)
    #     sendCommand('KILL')
    #     del r

    def print(self, message):
        print(message)

    def updateRunner(self):
        """
        Serializes the graph and sends it to the connected graph interpreter telling it to load the new data.
        :return:
        """
        # self.executedBuffer = []
        self.rgiConnection.send('PAUSE', self.print)
        message = self.serialize()
        # msg = struct.pack('>I', len(message)) + message.encode('utf-8')
        # self.sendUpdate(data)
        self.rgiConnection.send('UPDATE'+message, self.print)

    def push2Runner(self):
        """
        Serializes the graph and sends it to the connected graph interpreter telling it to load the new data.
        :return:
        """
        self.executedBuffer = []
        self.STOREDVALUES = {}
        self.rgiConnection.send('PAUSE', self.print)
        message = self.serialize()
        # msg = struct.pack('>I', len(message)) + message.encode('utf-8')
        # self.sendUpdate(data)
        self.rgiConnection.send('PUSH'+message, self.print)

    def serialize(self):
        """
        Returns a serialized representation of the graph instance.
        :return:
        """
        data = self.toJson()
        return data
        return zlib.compress(data.encode('utf-8'))

    def save(self, fileName):
        """
        Saves the graph as a JSON string to the disk
        :param fileName: string representing the file name.
        :return:
        """
        saveState = self.toJson()
        with open(fileName, 'w') as fp:
            fp.write(saveState)

    def toJson(self, subgraph=None):
        """
        Encodes the graph as a JSON string and returns the string.
        :param subgraph: Returns whole graph is 'subgraph=None' else only the nodes corresponding to the subgraph.
        :return:
        """
        if subgraph:
            return json.dumps([(node.ID, node.save()) for node in self.nodes.values() if node.subgraph == subgraph])
        return json.dumps([(node.ID, node.save()) for node in self.nodes.values()])
        #return json.dumps({node.ID: node.save() for node in self.nodes.values()})

    def killRunner(self):
        """
        Send KILL command to the graph interpreter telling it to terminate itself.
        :return:
        """
        if not self.slave:
            return
        self.rgiConnection.send('KILL', self.print)
        # sendCommand('KILL', self.cmdHost, self.cmdPort)
        # self.clientSocket.close()
        del self.runner
        self.runner = None
        self.connected = False

    def pauseRunner(self):
        """
        Send PAUSE command to the graph interpreter.
        :return:
        """
        self.rgiConnection.send('PAUSE', self.print)
        # sendCommand('PAUSE', self.cmdHost, self.cmdPort)

    def unpauseRunner(self):
        """
        Send UNPAUSE command to the graph interpreter.
        :return:
        """
        self.rgiConnection.send('UNPAUSE', self.print)
        # sendCommand('UNPAUSE', self.cmdHost, self.cmdPort)

    def stepRunner(self):
        """
        Send Step command to the graph interpreter causing it to execute one node and then reenter the PAUSED state.
        :return:
        """
        self.rgiConnection.send('STEP', self.print)

    def gotoRunner(self, nextID):
        """
        Send GOTO<Node> command to the graph interpreter causing it to execute the node with the given ID next.
        :param nextID:
        :return:
        """
        self.rgiConnection.send('GOTO1', self.print)

    def dropGraph(self):
        self.rgiConnection.send('DROP', self.print)

    def setStatus(self, status):
        self.status = json.loads(status[10:])

    def requestRemoteStatus(self):
        if self.connected:
            try:
                self.rgiConnection.send('STATUS***{}'.format(self._requestReport), self.setStatus)
                # status = json.loads(status[10:])
            except BrokenPipeError:
                self.connected = False
                return []
            except ConnectionResetError:
                self.connected = False
                return []
            except socket.timeout:
                self.connected = False
                return []
            else:
                # return json.loads(status[10:])
                return []
        else:
            return []

    def load(self, fileName, callback=None):
        with open(fileName, 'r') as fp:
            saveState = json.loads(fp.read())
        self.loadState(saveState, callback)
        # self.loadDict(saveState)

    def loadState(self, saveState, callback=None, reuseIDs=False):
        """
        Reconstruct a Graph instance from a JSON string representation created by the Graph.toJson() method.
        :param saveState:
        :return: Dictionary mapping the saved nodeIDs to the newly created nodes's IDs.
        """
        idMap = {}
        for id, nodeData in saveState:
            useID = id if reuseIDs else False
            try:
                restoredNode = self.spawnNode(NODECLASSES[nodeData['class']], position=nodeData['position'], silent=True, useID=useID)
            except KeyError:
                try:
                    dynamic = nodeData['dynamic']
                except KeyError:
                    dynamic = False
                if not dynamic:
                    if callback:
                        callback('Unknown Node class **{}**'.format(nodeData['class']))
                    else:
                        raise Exception('Unknown Node class <{}>.'.format(nodeData['class']))
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
            outputs = nodeData['outputs']
            for input in inputs:
                restoredNode.inputs[input[0]].setDefault(input[-1])
            for output in outputs:
                restoredNode.outputs[output[0]].setDefault(output[-1])
        for id, nodeData in saveState:
            id = int(id)
            for inputName, outputID in nodeData['inputConnections'].items():
                if inputName == 'Control':
                    continue
                outputNode, outputName = outputID.split(':O')
                try:
                    outputNode = idMap[int(outputNode)]
                # print(id, nodeData['inputConnections'], outputNode, outputName)

                    self.connect(str(outputNode), outputName, str(idMap[id]), inputName)
                except KeyError:
                    print('Warning: Could not create connection due to missing node.')

            for outputName, inputIDs in nodeData['outputConnections'].items():
                for inputID in inputIDs:
                    if not 'Control' in inputID:
                        continue
                    inputNode, inputName = inputID.split(':I')
                    try:
                        inputNode = idMap[int(inputNode)]
                    # print(id, nodeData['inputConnections'], outputNode, outputName)
                        self.connect(str(idMap[id]), outputName, str(inputNode), inputName)
                    except KeyError:
                        print('Warning: Could not create connection due to missing node.')

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
        self.reverseConnections = {key: set() for key in self.reverseConnections.keys()}
        idMap = {}
        removeNodes = set(self.nodes.keys())
        for id, nodeData in data:
            useID = id if reuseIDs else False
            idMap[int(id)] = int(id)
            if not int(id) in self.nodes.keys():
                restoredNode = self.spawnNode(NODECLASSES[nodeData['class']],
                                              position=nodeData['position'], silent=True, useID=useID)
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
            for inputName, outputID in nodeData['inputConnections'].items():
                if inputName == 'Control':
                    continue
                outputNode, outputName = outputID.split(':O')
                outputNode = idMap[int(outputNode)]
                # print(id, nodeData['inputConnections'], outputNode, outputName)
                self.connect(str(outputNode), outputName, str(idMap[id]), inputName)

            for outputName, inputIDs in nodeData['outputConnections'].items():
                for inputID in inputIDs:
                    if not 'Control' in inputID:
                        continue
                    inputNode, inputName = inputID.split(':I')
                    inputNode = idMap[int(inputNode)]
                    # print(id, nodeData['inputConnections'], outputNode, outputName)
                    self.connect(str(idMap[id]), outputName, str(inputNode), inputName)
        for nodeID in removeNodes:
            self.deleteNode(self.nodes[nodeID])
        self.update()
        return idMap

    def loadDict(self, saveState):
        """
        Reconstruct a Graph instance from a JSON string representation created by the Graph.toJson() method.
        :param saveState:
        :return: Dictionary mapping the saved nodeIDs to the newly created nodes's IDs.
        """
        idMap = {}
        for id, nodeData in saveState.items():
            restoredNode = self.spawnNode(NODECLASSES[nodeData['class']], position=nodeData['position'], silent=True)
            idMap[int(id)] = restoredNode.ID
            inputs = nodeData['inputs']
            outputs = nodeData['outputs']
            for input in inputs:
                restoredNode.inputs[input[0]].setDefault(input[-1])
            for output in outputs:
                restoredNode.outputs[output[0]].setDefault(output[-1])
        for id, nodeData in saveState.items():
            id = int(id)
            for inputName, outputID in nodeData['inputConnections'].items():
                if inputName == 'Control':
                    continue
                outputNode, outputName = outputID.split(':O')
                outputNode = idMap[int(outputNode)]
                # print(id, nodeData['inputConnections'], outputNode, outputName)
                self.connect(str(outputNode), outputName, str(idMap[id]), inputName)

            for outputName, inputIDs in nodeData['outputConnections'].items():
                for inputID in inputIDs:
                    if not 'Control' in inputID:
                        continue
                    inputNode, inputName = inputID.split(':I')
                    inputNode = idMap[int(inputNode)]
                    # print(id, nodeData['inputConnections'], outputNode, outputName)
                    self.connect(str(idMap[id]), outputName, str(inputNode), inputName)

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
            if any([conn.inputName == pinName, conn.outputName == pinName]):
                thisConn = conn
                break
        if thisConn:
            self.reverseConnections[node].remove(thisConn)
            self.connections[conn.outputNode].remove(thisConn)
            return
        thisConn = None
        for conn in self.connections[node]:
            if any([conn.inputName == pinName, conn.outputName == pinName]):
                thisConn = conn
                break
        if thisConn:
            self.connections[node].remove(thisConn)
            self.reverseConnections[conn.inputNode].remove(thisConn)

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

    def configureInterpreter(self, options):
        self.rgiConnection.send('CONFIGURE{}'.format(json.dumps(options)), print)


class NodeThread(Thread):

    def __init__(self, node, cb, arg):
        # node.lock()
        self.node = node
        self.cb = cb

        self.arg = arg
        super(NodeThread, self).__init__()
        self.daemon = True
        self.start()

    def run(self):
        super(NodeThread, self).run()
        try:
            self.node.run()
        except Exception as a:
            print('Something bad happened in when executing {}.'.format(str(self.node)))
            print(a)
            self.node.unlock
            return
        self.node.notify()
        if self.cb:
            self.cb(self.arg)
        self.node.unlock()


class Connection(object):
    """
    Class representing a connection and storing information about involved Inputs and Outputs.
    """
    def __init__(self, outNode, outName, inpNode, inpName):
        self.outputNode = outNode
        self.outputName = outName
        self.inputNode = inpNode
        self.inputName = inpName

    def __hash__(self):
        return hash(''.join([str(i) for i in (self.outputNode, self.outputName, self.inputNode, self.inputName)]))

    def __getitem__(self, item):
        return self.__getattribute__(item)


class StatusListener(Thread):
    """
    Thread for listening to the remote graph interpreter for status updates.
    """
    def __init__(self, master, socket, statusQueue, statusLock):
        Thread.__init__(self)
        self.alive = True
        self.connection = socket
        self.master = master
        self.daemon = True
        self.statusQueue = statusQueue
        self.statusLock = statusLock
        self.start()

    # def kill(self):
    #     self.alive = False
    #     time.sleep(.1)
    #     self.listenSocket.shutdown(SHUT_RDWR)

    def run(self):
        while self.alive:
            try:
                message = self.connection.recv(1024).decode()
            except:
                pass
            else:
                self.statusLock.acquire()
                for ID in [i for i in message.split('#')if i]:
                    self.master.executedBuffer.append(int(ID))
                self.statusLock.release()
                self.master.requestUpdate()







