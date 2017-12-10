from collections import OrderedDict
from copy import copy
import inspect

from chainer import variable
from PyQt5.QtGui import QColor

from chainer_wing import util

NODECLASSES = {}


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

    def __init__(self, name, var_type, hints=None,
                 value=util.NotSettedParameter(), select=None,
                 owner=False, optional=False):
        self.name = name
        self.connected = False
        self.var_type = var_type
        self.optional = optional
        if not hints:
            self.hints = [var_type[0].__name__]
        else:
            self.hints = [var_type[0].__name__] + hints
        self.value = value
        self.select = select
        self.owner = owner
        self.pure = 0

    def setOwner(self, owner):
        self.owner = owner

    def convert_var_type(self, value):
        if None in self.var_type and value == 'None':
            return None
        elif int in self.var_type and value.isdigit():
            return int(value)
        elif float in self.var_type and util.isfloat(value):
            return float(value)
        elif str in self.var_type:
            return value
        else:
            raise ValueError

    def set_value_from_text(self, text):
        if not self.var_type == (object,):
            try:
                self.value = self.convert_var_type(text)
            except TypeError:
                if int in self.var_type:
                    self.value = 0
                elif float in self.var_type:
                    self.value = 0.0
                elif bool in self.var_type:
                    self.value = False
                elif str in self.var_type:
                    self.value = ''
            except ValueError:
                self.value = None
            if bool in self.var_type:
                try:
                    if text.upper() == 'TRUE':
                        self.value = True
                    else:
                        self.value = False
                except:
                    self.value = text
        else:
            self.value = text

    def set_value(self, value):
        self.value = value

    def __str__(self):
        return 'INFO'

    def has_value_set(self):
        return not isinstance(self.value, util.NotSettedParameter)


class InputInfo(Info):
    def __call__(self, no_exception=False):
        if self.has_value_set():
            return self.value
        elif self.value is not None and not self.connected:
            if not self.var_type == (object,) and self.value:
                return self.var_type(self.value)
            else:
                return self.value
        else:
            if no_exception:
                return util.NotSettedParameter
            elif self.name == 'in_array':  # treat as start node.
                return ''
            else:
                raise InputNotAvailable('Input not set for node.')

    def setPure(self):
        self.pure = 1

    def setConnected(self, value):
        assert isinstance(value, bool)
        self.connected = value

    def isAvailable(self, info=False):
        if info:
            if self.has_value_set():
                return True
            elif self.value is not None and not self.connected and self.pure < 2:
                return True
            return False
        if self.has_value_set():
            return True
        elif self.value is not None and not self.connected and self.pure < 2:
            if self.pure == 1:
                self.pure = 2
            return True
        return False


class OutputInfo(Info):
    def __call__(self, value):
        try:
            value.__FloppyType__ = self.var_type
        except AttributeError:
            pass
        self.value = value


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

    def addInput(name,
                 var_type,
                 hints=None,
                 value='',
                 select=None,
                 optional=False):
        MetaNode.inputs.append({'name': name,
                                'var_type': var_type,
                                'hints': hints,
                                'value': value,
                                'select': select,
                                'optional': optional})

    def addOutput(name,
                  var_type,
                  hints=None,
                  value='',
                  select=None):
        MetaNode.outputs.append({'name': name,
                                 'var_type': var_type,
                                 'hints': hints,
                                 'value': value,
                                 'select': select})

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

    To add Inputs to a custom Node class call 'Input(name, var_type, hints,
    list)' in the class's body.
    e.g.:

        class MyNode(Node):
            Input('myStringInput', str)

    An 'InputNotAvailable' Exception is raised is the input is not set yet.
    """
    Tag('Node')
    registered_id = []
    is_image_node = False

    def __init__(self, graph, id_proposal=None):
        self.__pos__ = (0, 0)
        self.graph = graph
        self.subgraph = 'main'
        self.inputs = OrderedDict()
        self.outputs = OrderedDict()
        self.outputBuffer = {}
        self.inputPins = OrderedDict()
        self.outputPins = OrderedDict()
        self.runtime_error_happened = False
        self.name = ''

        cnt = 0
        if id_proposal is None or id_proposal in Node.registered_id:
            while True:
                id_proposal = self.id_from_cnt(cnt)
                if id_proposal not in Node.registered_id:
                    self.ID = id_proposal
                    break
                cnt += 1
        else:
            self.ID = id_proposal
        Node.registered_id.append(self.ID)

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
            self.outputPins[out.name] = Pin(outID, out, self)
            self.outputs[out.name] = out
            self.outputBuffer[out.name] = None
        if not self.inputs.keys():
            raise AttributeError('Nodes without any input are not valid.')
        if len(self.inputs.keys()) == 2:
            self.inputs[list(self.inputs.keys())[1]].setPure()

        # self.set_inputs_to_initial()
        self.setup()

    # TODO()
    def set_inputs_to_initial(self):
        if not hasattr(self, 'register_chainer_impl'):
            return
        impl = self.register_chainer_impl()
        print(inspect.signature(impl))
        default_dict = {key: value.default for key, value in
                        inspect.signature(impl).parameters.items()
                        if repr(value.default) !="<class 'inspect._empty'>"}
        for key in self.inputs.keys():
            if key in default_dict:
                self.inputs[key].value = default_dict[key]

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

    @classmethod
    def doc(cls):
        if hasattr(cls, 'register_chainer_impl'):
            return cls.register_chainer_impl().__doc__
        return 'No detail for this function.'

    def run(self):
        """
        Execute the node. Override this to implement logic.
        :rtype: None
        """
        raise NotImplementedError('This method should be override')

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
        Add a Tag to a Node class object.
        :param tag:
        :return:
        """
        cls.__tags__.append(tag)

    def __getattr__(self, item):
        """
        Catch self._<Input/Output> accesses and calls the appropriate methods.
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

    def getInputPin(self, input_name):
        """
        Get a reference to the Pin associated with the given input name.
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

    def get_value_type(self, value):
        if value.value == '':
            return value.var_type[0].__name__
        else:
            return type(value.value).__name__

    def to_dict(self):
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
                'name': self.name,
                'position': self.__pos__,
                'inputs': [
                    (input_name, self.get_value_type(inp), inp.value)
                    for input_name, inp in self.inputs.items()],
                'inputConnections': inputConns,
                'outputs': [
                    (output_name, self.get_value_type(out), out.value)
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
    def matchHint(cls, text):
        assert isinstance(text, str)
        return cls.matchInputHint(text) or cls.matchOutputHint(
            text) or cls.matchClassTag(text)

    @classmethod
    def matchClassTag(cls, text):
        assert isinstance(text, str)
        return any([tag.lower().startswith(text) for tag in cls.__tags__])

    @classmethod
    def matchInputHint(cls, text):
        assert isinstance(text, str)
        if text == 'object':
            return True
        if any([any([hint.startswith(text) for hint in inp.hints]) for inp in
                cls.__inputs__.values()]):
            return True

    @classmethod
    def matchOutputHint(cls, text):
        assert isinstance(text, str)
        if text == 'object':
            return True
        if any([any([hint.startswith(text) for hint in out.hints]) for out in
                cls.__outputs__.values()]):
            return True

    def id_from_cnt(self, cnt):
        raise NotImplementedError

    def clear(self):
        Node.registered_id.remove(self.ID)

    def check_member(self, members):
        for member in members:
            if not hasattr(self, member):
                raise util.ExistsInvalidParameter(self.ID, member)

    def get_name(self):
        if self.name:
            return self.name
        return self.ID


class Pin(object):
    """
    Class for storing all information required to represent a input/output pin.
    """

    def __init__(self, pinID, info, node):
        self.ID = pinID
        self.name = info.name
        self.info = info
        info.ID = pinID
        self.node = node


@abstractNode
class Link(Node):

    def id_from_cnt(self, cnt):
        return 'l' + str(cnt)

    def call(self):
        return'{0} = self.{0}('.format(self.get_name())

    def color(self):
        return QColor(45, 95, 45)


@abstractNode
class Function(Node):
    def id_from_cnt(self, cnt):
        return 'f' + str(cnt)

    def color(self):
        return QColor(85, 85, 35)


@abstractNode
class Loss(Function):
    def id_from_cnt(self, cnt):
        return 'loss' + str(cnt)

    def color(self):
        return QColor(45, 45, 95)
