from floppy.node import Node


class MyNode(Node):
    Input('Hello', str,
          default='World')


class MyNode2(Node):
    Input('abc', str)

print(MyNode.__name__, MyNode._inputs['Hello'].__dict__.items())
print(MyNode2.__name__, MyNode2._inputs['abc'].__dict__.items())
myNode = MyNode()
print(myNode._Hello)