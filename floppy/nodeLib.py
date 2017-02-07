from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QPoint, QModelIndex
from PyQt5.QtGui import *
from floppy.node import NODECLASSES
import os
from importlib.machinery import SourceFileLoader
customNodesPath = os.path.join(os.path.realpath(__file__)[:-10], 'CustomNodes')
# try:
#     [SourceFileLoader(str(i), os.path.join(customNodesPath, path)).load_module() for i, path in enumerate(os.listdir(customNodesPath)) if path.endswith('py')]
# except Exception as e:
#     print('Warning: error in custom node:\n{}'.format(str(e)))

for i, path in enumerate(os.listdir(customNodesPath)):
    if path.endswith('py'):
        try:
            SourceFileLoader(str(i), os.path.join(customNodesPath, path)).load_module()
        except Exception as e:
            print('Warning: error in custom node:\n{}'.format(str(e)))




class NodeFilter(QLineEdit):
    """
    Widget for filtering a list of available nodes by user specified characteristics.
    """
    def __init__(self, parent=None):
        super(NodeFilter, self).__init__(parent)
        self.textEdited.connect(self.check)
        self.setStyleSheet("NodeFilter {background-color:rgb(75,75,75) ;border:1px solid rgb(0, 0, 0); "
                           "border-color:black; color: white }")

    def focusInEvent(self, event):
        """
        This is supposed to selected the whole text whenever the widget is focused. Apparently, things don't work that
        way here.
        :param event: QFocusEvent.
        :return: None
        """
        super(NodeFilter, self).focusInEvent(event)
        self.selectAll()

    def check(self, text):
        """
        Interpret the text in the LineEdit and send the filtered node list to the registered NodeList widget.
        :param text: string that is used for filtering the node list.
        :return: None
        """
        text = text.lower()
        # nodes = [str(node) for node in nodeList if text in str(node).lower()]
        if not text.startswith('$'):
            nodes = [node for node in NODECLASSES.keys() if text in node.lower()]
        else:
            # nodes = set(self.nodeScanner.getHints(text[1:]) + self.nodeScanner.getHints(text[1:], False))
            text = text[1:]
            nodes = set([nodeName for nodeName, node in NODECLASSES.items() if node.matchHint(text)])
        model = QStandardItemModel()
        for node in sorted(nodes):
            item = QStandardItem()
            item.setText(node)
            model.appendRow(item)
        self.listView.setModel(model)

    def registerNodeListLayout(self, layout, widget):
        """
        Do I still need this? It doesn't look like it.
        :param layout:
        :param widget:
        :return:
        """
        self.check('')
        # print layout.children()

    def registerListView(self, view):
        """
        Establishes a reference to the NodeList instance used for displaying the filtering results.
        :param view: Reference to a NodeList instance.
        :return: None
        """
        self.listView = view
        self.check('')

    def getSelectedNode(self):
        """
        Do I still need this? It doesn't look like it.
        """
        pass

    def keyPressEvent(self, event):
        """
        Handling navigation through the nodeLib widgets by key presses.
        :param event: QKeyEvent.
        :return: None
        """
        super(NodeFilter, self).keyPressEvent(event)
        self.parent().keyPressEvent(event)
        if event.key() == Qt.Key_Down:
            self.listView.setFocus()
            self.listView.setCurrentIndex(self.listView.model().index(0, 0))


class NodeList(QListView):
    """
    Widget for displaying the available (and filtered) list of nodes and handling drag&drop spawning of nodes.
    """
    def __init__(self,  parent=None):
        super(NodeList, self).__init__(parent)
        self.filter = None
        self.graph = None
        self.down = False
        self.selectedClass = None
        self.setStyleSheet('''
        NodeList {background-color:rgb(75,75,75) ;border:1px solid rgb(0, 0, 0);
                  border-color:black}
        NodeList::item {color: white}
        ''')

    def setup(self, nodeFilter, graph):
        self.filter = nodeFilter
        self.graph = graph
        self.filter.registerListView(self)

    def mousePressEvent(self, event):
        """
        Handling drag&drop of nodes in the list into the diagram.
        :param event: QMouseEvent
        :return: None
        """
        if not self.down:
            super(NodeList, self).mousePressEvent(event)
            self.down = True
            name = self.filter.listView.selectedIndexes()[0].data()
            self.selectedClass = NODECLASSES[name]
            # self.blockSignals(True)
            # self.selectionChanged()

    def mouseReleaseEvent(self, event):
        """
        Handling drag&drop of nodes in the list into the diagram.
        :param event: QMouseEvent
        :return: None
        """
        super(NodeList, self).mouseReleaseEvent(event)
        self.down = False
        if event.pos().x() < 0:
            # transform = self.graph.painter.transform
            pos = QCursor.pos()
            topLeft = self.graph.painter.mapToGlobal(self.graph.painter.pos())
            pos -= topLeft

            pos -= self.graph.painter.center
            # pos -= self.graph.painter.center
            # print(pos, self.graph.painter.center, pos*transform)
            pos /= self.graph.painter.scale
            # print(transform)

            self.graph.spawnNode(self.selectedClass, position=(pos.x(), pos.y()))
            self.graph.update()


    def mouseMoveEvent(self, event):
        """
        Handling drag&drop of nodes in the list into the diagram.
        :param event: QMouseEvent
        :return: None
        """
        if not self.down:
            super(NodeList, self).mouseMoveEvent(event)


class ContextNodeList(NodeList):
    """
    A NodeList widget adapted to work in the context menu created when dragging a connection into open space in the
    diagram.
    """
    def registerDialog(self, dialog):
        """
        Establish a reference to the context menu holding the widget.
        :param dialog: Reference to a NodeDialog instance
        :return: None
        """
        self.dialog = dialog

    def registerGraph(self, graph):
        self.graph = graph

    def registerPainter(self, painter):
        self.painter = painter
        self.down = False

    # def mousePressEvent(self, event):
    #     """
    #     Handling drag&drop of nodes in the list into the diagram.
    #     :param event: QMouseEvent
    #     :return: None
    #     """
    #     # super(NodeList, self).mousePressEvent(event)
    #     self.down = True
    #     name = self.filter.listView.selectedIndexes()[0].data()
    #     self.selectedClass = NODECLASSES[name]

    def mouseReleaseEvent(self, event):
        """
        Handling the selection and spawning of nodes in the list.
        :param event: QMouseEvent.
        :return: None
        """
        super(NodeList, self).mouseReleaseEvent(event)
        # pos = QCursor.pos()
        pos = self.parent().mapToGlobal(self.parent().pos())
        topLeft = self.graph.painter.mapToGlobal(self.graph.painter.pos())
        pos -= topLeft

        pos -= self.graph.painter.center
        pos /= self.graph.painter.scale
        self.graph.spawnNode(self.selectedClass, position=(pos.x(), pos.y()))
        self.down = False
        self.graph.requestUpdate()
        self.dialog.close(True)

    def keyPressEvent(self, event):
        """
        Handling the selection and spawning of nodes in the list.
        :param event: QMouseEvent.
        :return: None
        """
        super(ContextNodeList, self).keyPressEvent(event)
        if event.key() == Qt.Key_Return:
            name = self.filter.listView.selectedIndexes()[0].data()
            self.selectedClass = NODECLASSES[name]
            pos = self.parent().mapToGlobal(self.parent().pos())
            topLeft = self.graph.painter.mapToGlobal(self.graph.painter.pos())
            pos -= topLeft

            pos -= self.graph.painter.center
            pos /= self.graph.painter.scale
            self.graph.spawnNode(self.selectedClass, position=(pos.x()-5, pos.y()-40))
            self.down = False
            self.graph.requestUpdate()
            self.dialog.close(True)


class ContextNodeFilter(NodeFilter):
    """
    A NodeFilter widget adapted to work in the context menu created when dragging a connection into open space in the
    diagram.
    """
    def registerDialog(self, dialog, back=False):
        """
        Establish a reference to the context menu holding the widget and specifying whether a connection to an InputPin
        or an OutputPin is about to be established.
        :param dialog: Reference to a NodeDialog instance
        :param back: boolean. True if the newly created node will be connected to the nodes input. False if otherwise.
        :return: None
        """
        self.dialog = dialog
        self.back = back

    def check(self, text):
        """
        Adapted method from base class to do hinting by default.
        :param text: string interpreted for filtering the node list.
        :return: None
        """
        try:
            text = text.lower()
        except AttributeError:
            text = ''
        # nodes = [str(node) for node in nodeList if text in str(node).lower()]
        if self.dialog.cB.checkState():
            if text:
                text = '$' + text
            else:
                text = '$' + self.dialog.getTypeHint()
        if not text.startswith('$'):
            nodes = [node for node in NODECLASSES.keys() if text in node.lower()]
        else:
            text = text[1:]
            nodes = set([nodeName for nodeName, node in NODECLASSES.items() if node.matchHint(text)])
        model = QStandardItemModel()
        for node in sorted(nodes):
            item = QStandardItem()
            item.setText(node)
            model.appendRow(item)
        self.listView.setModel(model)









