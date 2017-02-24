from collections import OrderedDict
from copy import copy

from PyQt5.QtGui import QColor

NODECLASSES = {}


# STOREDVALUES = {}


class InputNotAvailable(Exception):
    pass


class InputAlreadySet(Exception):
    pass


def abstractNode(cls: type):
    """
    Removes a Node class from the NODECLASSES dictionary and then returns the class object.
    Use this as a decorator to stop a not fully implemented Node class from being available in the editor.
    :param cls: Node class object.
    :return: Unmodified node class object.
    :rtype: Node
    """
    del NODECLASSES[cls.__name__]
    return cls


def Input(*args, **kwargs):
    pass


def Output(*args, **kwargs):
    pass


def Tag(*args, **kwargs):
    pass


class Info(object):
    """
    Class for handling all information related to both inputs and outputs.
    """

    def __init__(self, name, var_type, hints=None, default='', select=None,
                 owner=False, list=False, optional=False):
        self.name = name
        self.connected = False
        self.var_type = var_type
        self.optional = optional
        if not hints:
            self.hints = [var_type.__name__]
        else:
            self.hints = [var_type.__name__] + hints
        self.default = default
        self.valueSet = False
        self.value = None
        self.select = select
        self.owner = owner
        self.list = list
        self.loopLevel = 0
        self.usedDefault = False
        self.pure = 0

    def setOwner(self, owner):
        self.owner = owner

    def setDefault(self, value):
        if not self.var_type == object:
            try:
                self.default = self.var_type(value)
            except ValueError:
                self.default = ''
            if self.var_type == bool:
                try:
                    if value.upper() == 'TRUE':
                        self.default = True
                    else:
                        self.default = False
                except:
                    self.default = value
        else:
            self.default = value

    def __str__(self):
        return 'INFO'

    def reset(self, nodeLoopLevel=0, force=False):
        if nodeLoopLevel > self.loopLevel and not force:
            # print('Not resetting Input {} because owing node has higher node\n'
            #       'level than the node setting the Input: {}vs.{}'.format(self.name, nodeLoopLevel, self.loopLevel))
            return
        self.default = None
        self.valueSet = False
        self.value = None


class InputInfo(Info):
    def __call__(self, noException=False):
        if self.valueSet:
            if not self.var_type == object:
                if self.list:
                    return [self.var_type(i) for i in self.value]
                return self.var_type(self.value)
            else:
                return self.value
        elif self.default is not None and not self.connected:
            self.usedDefault = True if self.loopLevel > 0 else False
            if not self.var_type == object and self.default:
                return self.var_type(self.default)
            else:
                return self.default
        else:
            if noException:
                return None
            elif self.name == 'in_array':  # treat as start node.
                return ""
            else:
                raise InputNotAvailable('Input not set for node.')

    def set(self, value, override=False, loopLevel=0):
        if self.valueSet and not override:
            raise InputAlreadySet(
                'Input \'{}\' of node \'{}\' is already set.'.format(self.name,
                                                                     str(
                                                                         self.owner)))
        self.value = value
        self.valueSet = True
        if not self.name == 'Control':
            self.loopLevel = loopLevel

    def setPure(self):
        self.pure = 1

    def setConnected(self, value: bool):
        self.connected = value

    def isAvailable(self, info=False):
        if info:
            if self.valueSet:
                return True
            elif self.default is not None and not self.connected and not self.usedDefault and self.pure < 2:
                return True
            return False
        if self.valueSet:
            # print('^^^^^^^^^^^^^^^^^^', self.name, self.value, self.valueSet)
            return True
        elif self.default is not None and not self.connected and not self.usedDefault and self.pure < 2:
            if self.pure == 1:
                self.pure = 2
            # self.usedDefault = True
            # print('+++++++++++++++++', self.name, self.value, self.valueSet, self.owner, self.usedDefault, self.pure)
            return True
        return False


class OutputInfo(Info):
    def __call__(self, value):
        try:
            value.__FloppyType__ = self.var_type
        except AttributeError:
            pass
        self.value = value
        self.valueSet = True


class MetaNode(type):
    """
    Meta class for the Node class. Makes node declaration objects available in the class's scope and registers each
    Node object to have a convenient way of accessing all subclasses of Node.
    """
    inputs = []
    outputs = []

    @classmethod
    def __prepare__(metacls, name, bases):
        MetaNode.inputs = []
        MetaNode.outputs = []
        MetaNode.tags = []
        return {'Input': MetaNode.addInput,
                'input': MetaNode.addInput,
                'Output': MetaNode.addOutput,
                'output': MetaNode.addOutput,
                'Tag': MetaNode.addTag,
                'tag': MetaNode.addTag}

    def addTag(*args):
        for arg in args:
            MetaNode.tags.append(arg)

    def addInput(name: str,
                 var_type: object,
                 hints=None,
                 default='',
                 select=None,
                 list=False,
                 optional=False):
        MetaNode.inputs.append({'name': name,
                                'var_type': var_type,
                                'hints': hints,
                                'default': default,
                                'select': select,
                                'list': list,
                                'optional': optional})

    def addOutput(name: str,
                  var_type: object,
                  hints=None,
                  default='',
                  select=None,
                  list=False):
        MetaNode.outputs.append({'name': name,
                                 'var_type': var_type,
                                 'hints': hints,
                                 'default': default,
                                 'select': select,
                                 'list': list})

    def __new__(cls, name, bases, classdict):
        result = type.__new__(cls, name, bases, classdict)
        # result.__dict__['Input'] = result._addInput
        NODECLASSES[name] = result
        try:
            result.__inputs__ = result.__bases__[0].__inputs__.copy()
        except AttributeError:
            result.__inputs__ = OrderedDict()
        try:
            result.__outputs__ = result.__bases__[0].__outputs__.copy()
        except AttributeError:
            result.__outputs__ = OrderedDict()

        try:
            result.__tags__ = result.__bases__[0].__tags__.copy()
        except AttributeError:
            result.__tags__ = []

        for inp in MetaNode.inputs:
            result._addInput(data=inp, cls=result)

        for out in MetaNode.outputs:
            result._addOutput(data=out, cls=result)

        for tag in MetaNode.tags:
            result._addTag(tag)
        return result


@abstractNode
class Node(object, metaclass=MetaNode):
    """
    Base class for Nodes.

    To add Inputs to a custom Node class call 'Input(name, var_type, hints, list)' in the class's
    body e.g.:

        class MyNode(Node):
            Input('myStringInput', str, list=True)

    To access the value of an input during the Node's 'run' method or 'check' method use
    'myNodeInstance._myStringInput'. An 'InputNotAvailable' Exception is raised is the input is not set yet.
    """
    Input('TRIGGER', object, optional=True)
    Tag('Node')

    def __init__(self, nodeID, graph):
        self.loopLevel = 0
        self.__pos__ = (0, 0)
        self.graph = graph
        self.locked = False
        self.subgraph = 'main'
        self.ID = nodeID
        self.buffered = False
        self.inputs = OrderedDict()
        self.outputs = OrderedDict()
        self.outputBuffer = {}
        self.inputPins = OrderedDict()
        self.outputPins = OrderedDict()
        for i, inp in enumerate(self.__inputs__.values()):
            inp = copy(inp)
            inp.setOwner(self)
            inpID = '{}:I{}'.format(self.ID, inp.name)
            newPin = Pin(inpID, inp, self)
            self.inputPins[inp.name] = newPin
            self.inputs[inp.name] = inp

        for i, out in enumerate(self.__outputs__.values()):
            out = copy(out)
            out.setOwner(self)
            outID = '{}:O{}'.format(self.ID, out.name)
            newPin = Pin(outID, out, self)
            self.outputPins[out.name] = newPin
            self.outputs[out.name] = out
            self.outputBuffer[out.name] = None
        if not self.inputs.keys():
            raise AttributeError('Nodes without any input are not valid.')
        if len(self.inputs.keys()) == 2:
            self.inputs[list(self.inputs.keys())[1]].setPure()
        self.setup()

    def setup(self):
        """
        This method will be called after a node instance is initialized.
        Override this to initialize attributes required for custom node behavior.
        This way the annoying calls of super(Node, self).__init__(*args, **kwargs) calls can be avoided.
        :return:
        """
        pass

    def __str__(self):
        return '{}-{}'.format(self.__class__.__name__, self.ID)

    def __hash__(self):
        return hash(str(self))

    def lock(self):
        self.locked = True

    def unlock(self):
        self.locked = False
        self.graph.runningNodes.remove(self.ID)

    def run(self):
        """
        Execute the node. Override this to implement logic.
        :rtype: None
        """
        raise NotImplementedError('This method should be override')

    def notify(self):
        """
        Manage the node's state after execution and set input values of subsequent nodes.
        :return: None
        :rtype: None
        """
        for con in self.graph.getConnectionsFrom(self):
            self.buffered = False
            output_name = con.output_name
            next_node = con.input_node
            next_input = con.input_name
            # next_node.prepare()
            if self.outputs[output_name].valueSet:
                next_node.setInput(next_input,
                                   self.outputs[output_name].value,
                                   override=True,
                                   loopLevel=self.loopLevel)
            else:
                next_node.setInput(next_input,
                                   self.outputs[output_name].default,
                                   override=True,
                                   loopLevel=self.loopLevel)
        if not self.graph.getConnectionsFrom(self):
            self.buffered = True
            for out in self.outputs.values():
                self.outputBuffer[out.name] = out.value
        [Info.reset(inp, self.loopLevel) for inp in self.inputs.values()]

    def setInput(self, input_name, value, override=False, loopLevel=False):
        """
        Sets the value of an input.
        :param input_name: str representing the name of the input.
        :param value: object of the appropriate type for that input.
        :param override: boolean specifying whether the input should be overridden if it was set already.
        :param looped: boolean. Set to True if the input is set by a looped node. If True, the node becomes a looped
        node itself. Defaults to False.
        :return: None
        """
        self.loopLevel = max([self.loopLevel, loopLevel])
        self.inputs[input_name].set(value, override=override,
                                    loopLevel=loopLevel)

    def check(self):
        """
        Checks whether all prerequisites for executing the node instance are met.
        Override this to implement custom behavior.
        By default the methods returns True if all inputs have been set. False otherwise.
        :return: Boolean; True if ready, False if not ready.
        :rtype: bool
        """
        if self.locked:
            return False
        if self.buffered and self.outputs.keys():
            print(
                'Node {} has buffered output. Trying to notify outgoing connections.'.format(
                    self))
            return self.notify()
        for inp in self.inputs.values():
            if not inp.isAvailable():
                if inp.optional and not inp.connected:
                    continue
                return False
        return True

    def report(self):
        """
        Creates and returns a dictionary encoding the current state of the Node instance.
        Override this method to implement custom reporting behavior. Check the ReportWidget documentation for details
        on how to implement custom templates.

        The 'keep' key can be used to cache data by the editor. The value assigned to 'keep' must be another key of
        the report dictionary or 'CLEAR'. If it is a key, the value assigned to that key will be cached. If it is
        'CLEAR' the editors cache will be purged. This can be useful for plotting an ongoing stream of data points
        in the editor.

        The 'ready' item is set to True when all inputs are available. This is mainly useful for debugging graph
        applications.
        """
        ready = all(
            [inp.isAvailable(info=True) for inp in self.inputs.values()])
        return {'template': 'DefaultTemplate',
                'class': self.__class__.__name__,
                'ID': self.ID,
                'inputs': [(i, v.var_type.__name__,
                            str(v.value) if len(str(v.value)) < 10 else str(
                                v.value)[:10] + '...') for i, v in
                           self.inputs.items()],
                'outputs': [(i, v.var_type.__name__,
                             str(v.value) if len(str(v.value)) < 10 else str(
                                 v.value)[:10] + '...') for i, v in
                            self.outputs.items()],
                'keep': None,
                'ready': 'Ready' if ready else 'Waiting'}

    # def prepare(self):
    #     """
    #     Method for preparing a node for execution.
    #     This method is called on each node before the main execution loop of the owning graph instance is started.
    #     The methods makes sure that artifacts from previous execution are reset to their original states and default
    #     values of inputs that are connected to other nodes' outputs are removed.
    #     :return:
    #     """
    #     return
    #     [InputInfo.reset(inp) for inp in self.inputs.values()]

    def _addInput(*args, data='', cls=None):
        """
        This should be a classmethod.
        :param args:
        :param data:
        :param cls:
        :return:
        """
        inputInfo = InputInfo(**data)
        cls.__inputs__[data['name']] = inputInfo

    def _addOutput(*args, data='', cls=None):
        """
        This should be a classmethod.
        :param args:
        :param data:
        :param cls:
        :return:
        """
        outputInfo = OutputInfo(**data)
        cls.__outputs__[data['name']] = outputInfo

    @classmethod
    def _addTag(cls, tag='Node'):
        """
        Adds a Tag to a Node class object.
        :param tag:
        :return:
        """
        cls.__tags__.append(tag)

    def __getattr__(self, item):
        """
        Catches self._<Input/Ouptput> accesses and calls the appropriate methods.
        :param item: str; Attribute name.
        :return: object; Attribute
        :rtype: object
        """
        if item.startswith('_') and not item.startswith('__'):
            try:
                return self.inputs[item.lstrip('_')]()
            except KeyError:
                try:
                    return self.outputs[item.lstrip('_')]
                except KeyError:
                    raise AttributeError(
                        'No I/O with name {} defined.'.format(item.lstrip('_')))
                    # raise AttributeError('No Input with name {} defined.'.format(item.lstrip('_')))
        else:
            return super(Node, self).__getattr__(item)

    def getInputPin(self, input_name):
        """
        Returns a reference to the Pin instance associated with the input with the given name.
        :param input_name: str; Name of the input.
        :return: Pin instance
        :rtype: Pin
        """
        return self.inputPins[input_name]

    def getOutputPin(self, output_name):
        return self.outputPins[output_name]

    def getInputInfo(self, input_name):
        return self.inputs[input_name]

    def getOutputInfo(self, output_name):
        return self.outputs[output_name]

    def getInputID(self, input_name):
        return '{}:I{}'.format(self.ID, input_name)

    def getOutputID(self, output_name):
        return '{}:O{}'.format(self.ID, output_name)

    def getInputofType(self, var_type):
        for inp in self.inputs.values():
            if issubclass(var_type, inp.var_type) or issubclass(inp.var_type,
                                                              var_type):
                return inp

    def getOutputofType(self, var_type):
        for out in self.outputs.values():
            if issubclass(var_type, out.var_type) or issubclass(out.var_type,
                                                              var_type):
                return out

    def save(self):
        """
        Returns a dictionary containing all data necessary to reinstanciate the Node instance with the same properties
        it currently has. A list of the dictionaries of each node instance in a graph is all the data necessary to
        reinstanciate the whole graph.
        :return:
        """
        inputConns = self.get_input_connect_dict()
        outputConns = {out.name: self.graph.getConnectionsOfOutput(out) for out
                       in self.outputs.values()}
        for key, conns in outputConns.items():
            conns = [outputConn.input_node.getInputID(outputConn.input_name) for
                     outputConn in conns]
            outputConns[key] = conns
        return {'class': self.__class__.__name__,
                'position': self.__pos__,
                'inputs': [
                    (input_name, inp.var_type.__name__, inp(True), inp.default)
                    for input_name, inp in self.inputs.items()],
                'inputConnections': inputConns,
                'outputs': [
                    (output_name, out.var_type.__name__, out.value, out.default)
                    for output_name, out in self.outputs.items()],
                'outputConnections': outputConns,
                'subgraph': self.subgraph}

    def get_input_connections(self):
        connects = []
        for inp in self.inputs.values():
            if self.graph.getConnectionOfInput(inp) is not None:
                connects.append(self.graph.getConnectionOfInput(inp))
        return connects

    def get_input_connect_dict(self):
        input_connect_dict = {}
        for connect in self.get_input_connections():
            input_connect_dict[connect.input_name] = connect.output_node. \
                getOutputID(connect.output_name)
        return input_connect_dict

    @classmethod
    def matchHint(cls, text: str):
        return cls.matchInputHint(text) or cls.matchOutputHint(
            text) or cls.matchClassTag(text)

    @classmethod
    def matchClassTag(cls, text: str):
        return any([tag.lower().startswith(text) for tag in cls.__tags__])

    @classmethod
    def matchInputHint(cls, text: str):
        if text == 'object':
            return True
        if any([any([hint.startswith(text) for hint in inp.hints]) for inp in
                cls.__inputs__.values()]):
            return True

    @classmethod
    def matchOutputHint(cls, text: str):
        if text == 'object':
            return True
        if any([any([hint.startswith(text) for hint in out.hints]) for out in
                cls.__outputs__.values()]):
            return True


class Pin(object):
    """
    Class for storing all information required to represent a input/output pin.
    """

    def __init__(self, pinID, info, node):
        self.ID = pinID
        self.ID = pinID
        self.name = info.name
        self.info = info
        info.ID = pinID
        self.node = node


@abstractNode
class ControlNode(Node):
    """
    Base class for nodes controlling the program flow e.g. If/Else constructs and loops.
    Control nodes have an additional control input and a finalize output.

    The control input is a special input that supports multiple input connections. For example a loop node gets
    notified of a finished iteration over its body by setting the input of the control input. If all iterations are
    completed, the last set input is passed to the finalize output.
    An If/Else construct uses the control input to notify the node that the selected branch terminated. When that
    happens, the value of the control input is set to the finalize output.

    Restricting the option to have multiple connections to ControlNodes only makes sure that the node responsible for
    branches in the execution tree is also the node responsible for putting the pieces back together.
    """
    Input('Start', object)
    Input('Control', object)
    Output('Final', object)

    def __init__(self, *args, **kwargs):
        super(ControlNode, self).__init__(*args, **kwargs)
        self.waiting = False


@abstractNode
class ForLoop(ControlNode):
    """
    Generic loop node that iterates over all elements in a list.
    """

    # Input('Start', object, list=True)
    # Output('ListElement', object)

    def __init__(self, *args, **kwargs):
        super(ForLoop, self).__init__(*args, **kwargs)
        self.fresh = True
        self.counter = 0
        self.done = False
        self.loopLevel = 0

    def setInput(self, input_name, value, override=False, loopLevel=0):
        if input_name == 'Control':
            loopLevel = self.loopLevel
        super(ForLoop, self).setInput(input_name, value, override, loopLevel)

    def check(self):
        if self.fresh:
            for inp in self.inputs.values():
                if inp.name == 'Control':
                    continue
                if inp.name == 'TRIGGER' and not inp.connected:
                    continue
                if not inp.isAvailable():
                    # print('        {}: Prerequisites not met.'.format(str(self)))
                    return False
            return True
        else:
            if self.inputs['Control'].isAvailable():
                return True

    def run(self):
        super(ForLoop, self).run()
        self.fresh = False
        try:
            self._ListElement(self._Start[self.counter])
        except IndexError:
            self._Final(self._Start)
            self.done = True
        self.counter += 1

    def notify(self):
        if not self.done:
            for oName in self.outputs.keys():
                if oName == 'Final':
                    continue
                output = self.outputs[oName]
                for con in self.graph.getConnectionsOfOutput(output):
                    output_name = con.output_name
                    nextNode = con.input_node
                    nextInput = con.input_name
                    # nextNode.prepare()
                    nextNode.setInput(nextInput,
                                      self.outputs[output_name].value,
                                      override=True,
                                      loopLevel=self.loopLevel + 1)
            self.inputs['Control'].reset(force=True)

        else:
            output = self.outputs['Final']
            for con in self.graph.getConnectionsOfOutput(output):
                output_name = con.output_name
                nextNode = con.input_node
                nextInput = con.input_name
                nextNode.setInput(nextInput, self.outputs[output_name].value,
                                  loopLevel=self.loopLevel)
            # self.prepare()
            self.fresh = True
            for inp in self.inputs.values():
                if not inp.name == 'Iterations':
                    inp.reset()
            self.counter = 0
            self.fresh = True
            self.done = False

    def report(self):
        r = super(ForLoop, self).report()
        ready = any((self.inputs['Control'].isAvailable(info=True),
                     self.inputs['Start'].isAvailable(info=True)))
        r['ready'] = 'Ready' if ready else 'Waiting'
        return r


@abstractNode
class Link(Node):
    link_cnt = 0

    def __init__(self, nodeID, graph):
        super(Link, self).__init__(nodeID, graph)
        self.link_id = Link.link_cnt
        Link.link_cnt += 1

    def call(self):
        return "self.l{0}(".format(self.link_id)

    def color(self):
        return QColor(45, 95, 45)


@abstractNode
class Function(Node):
    def color(self):
        return QColor(95, 45, 45)


@abstractNode
class Loss(Function):
    def call_end(self):
        return "self.y, t)"

    def color(self):
        return QColor(45, 45, 95)
