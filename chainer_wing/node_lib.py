from importlib.machinery import SourceFileLoader
import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from chainer_wing.node import NODECLASSES
from chainer_wing.subwindows.train_config import TrainParamServer

customNodesPath = os.path.join(os.path.dirname(__file__), 'CustomNodes')

for i, path in enumerate(os.listdir(customNodesPath)):
    if path.endswith('py'):
        try:
            full_path = os.path.join(customNodesPath, path)
            SourceFileLoader(str(i), full_path).load_module()
        except Exception as e:
            print('Warning: error in custom node:\n{}'.format(str(e)))


class NodeFilter(QLineEdit):
    """
    Widget for filtering a list of available nodes by user specified strings.
    """
    def __init__(self, parent=None):
        super(NodeFilter, self).__init__(parent)
        self.textEdited.connect(self.update_node_list)
        self.setStyleSheet("NodeFilter {background-color:rgb(75,75,75) ;"
                           "border:1px solid rgb(0, 0, 0); "
                           "border-color:black; color: white }")

    def focusInEvent(self, event):
        """
        This is supposed to selected the whole text whenever the widget is
         focused. Apparently, things don't work that way here.
        :param event: QFocusEvent.
        :return: None
        """
        super(NodeFilter, self).focusInEvent(event)
        self.selectAll()

    def update_node_list(self, text=''):
        """
        Interpret the text in the LineEdit and send the filtered node list to
         the registered NodeList widget.
        :param text: string that is used for filtering the node list.
                     If '', display all Nodes.
        :return: None
        """
        text = text.lower()
        # nodes = [str(node) for node in nodeList if text in str(node).lower()]
        text = text[1:]
        if 'Image' not in TrainParamServer()['Task']:
            nodes = [nodeName for nodeName, node in NODECLASSES.items()
                     if node.matchHint(text) and not node.is_image_node]
        else:
            nodes = [nodeName for nodeName, node in NODECLASSES.items()
                     if node.matchHint(text)]
        model = QStandardItemModel()
        for node in sorted(nodes):
            item = QStandardItem()
            item.setText(node)
            item.setToolTip(NODECLASSES[node].doc())
            model.appendRow(item)
        self.listView.setModel(model)

    def register_list_view(self, view, text=''):
        """
        Establishes a reference to the NodeList instance used for displaying
         the filtering results.
        :param view: Reference to a NodeList instance.
        :return: None
        """
        self.listView = view
        self.update_node_list(text)

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
    Widget for displaying the available (and filtered) list of nodes and
     handling drag & drop spawning of nodes.
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

    def setup(self, node_filter, graph):
        self.filter = node_filter
        self.graph = graph
        self.filter.register_list_view(self)

    def mousePressEvent(self, event):
        """
        Handling drag&drop of nodes in the list into the diagram.
        :param event: QMouseEvent
        :return: None
        """
        if not self.down:
            super(NodeList, self).mousePressEvent(event)
            self.down = True
            if self.filter.listView.selectedIndexes():
                name = self.filter.listView.selectedIndexes()[0].data()
                self.selectedClass = NODECLASSES[name]

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
            pos = self.graph.correct_pos(pos)

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
