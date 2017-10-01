import json
import logging
import os

import chainer
import numpy
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

from chainer_wing import util
from chainer_wing.gui_main.mainwindow import Ui_MainWindow
from chainer_wing.subwindows.data_config import DataDialog
from chainer_wing.subwindows.image_data_config import ImageDataDialog
from chainer_wing.subwindows.settings import SettingsDialog
from chainer_wing.subwindows.train_config import TrainDialog
from chainer_wing.subwindows.train_config import TrainParamServer
from chainer_wing.subwindows.prediction_widget import PredictionWindow

logger = logging.getLogger('ChainerWing')

PINSIZE = 8
TEXTYOFFSET = 0


class Painter2D(QtWidgets.QWidget):
    PINCOLORS = {str: QtGui.QColor(255, 190, 0),
                 int: QtGui.QColor(0, 115, 130),
                 float: QtGui.QColor(0, 200, 0),
                 object: QtGui.QColor(190, 190, 190),
                 bool: QtGui.QColor(190, 0, 0),
                 chainer.Variable: QtGui.QColor(100, 0, 100),
                 numpy.ndarray: QtGui.QColor(100, 0, 200), }
    nodes = []
    scale = 1.
    globalOffset = QtCore.QPoint(0, 0)
    drag = False
    inputPinPositions = []
    clickedPin = None
    clickedNode = None
    nodePoints = []
    downOverNode = False

    def __init__(self, parent=None):
        super(Painter2D, self).__init__(parent)
        self.setMouseTracking(True)
        self.timer = QtCore.QTimer()
        self.timer.start(500)
        self.setFocusPolicy(Qt.ClickFocus)
        self.graph = None
        self.looseConnection = None
        self.reportWidget = None
        self.pinPositions = {}
        self.drawItems = []
        self.drawItemsOfNode = {}
        self.watchingItems = set()
        self.contextSensitive = False
        self.rightClickedNode = None
        self.mouseDownPos = None
        self.relayTo = None
        self.selectFrame = None
        self.selectFrame_End = None
        self.selectedSubgraph = ('main', None)
        self.groupSelection = []
        self.reset()

    def groupSelected(self):
        return len(self.groupSelection)

    def reset(self):
        self.nodes = []
        self.graph = None
        self.looseConnection = None
        self.reportWidget = None
        self.pinPositions = {}
        self.drawItems = []
        self.drawItemsOfNode = {}
        self.watchingItems = set()
        self.rightClickedNode = None
        self.contextSensitive = False
        self.mouseDownPos = None
        self.relayTo = None
        self.selectFrame = None
        self.selectFrame_End = None
        self.selectedSubgraph = ('main', None)
        self.groupSelection = []

    def createSubgraph(self, name):
        subgraph = set()
        relayInputs = set()
        for node in self.groupSelection:
            node.subgraph = name
            subgraph.add(node)
        allInputs = [i for i in self.getAllInputsOfSubgraph(name)]
        for inp in allInputs:
            con = self.graph.getConnectionOfInput(inp)
            if con:
                outNode = con.output_node
                if outNode not in subgraph:
                    relayInputs.add((inp, outNode, con.output_name))
            else:
                relayInputs.add((inp, None, None))

        relayOutputs = set()
        allOutputs = self.getAllOutputsOfSubgraph(name)
        for out in allOutputs:
            cons = self.graph.getConnectionsOfOutput(out)
            if cons:
                for con in cons:
                    if con.input_node not in subgraph:
                        relayOutputs.add((out, con.input_node, con.input_name))
                        break
            else:
                relayOutputs.add((out, None, None))
        # print('xxx', self.graph.toJson(subgraph=name))
        # print([i for i in relayInputs])
        relayOutputs = sorted(relayOutputs, key=lambda item: item[0].name)
        relayInputs = sorted(relayInputs, key=lambda item: item[0].name)
        pos = self.mapToGlobal(self.parent().pos())
        topLeft = self.mapToGlobal(self.pos())
        pos -= topLeft
        # pos -= self.center
        pos /= self.scale
        newNode = self.graph.createSubGraphNode(name, self.graph.to_json(
            subgraph=name), relayInputs,
                                                relayOutputs,
                                                spawnAt=(pos.x(), pos.y()))
        self.update()

    def setSelectedSubgraph(self, graph, parent=None):
        if not parent:
            parent = self.selectedSubgraph[0]
        self.selectedSubgraph = (graph, parent)

    def getAllSubgraphs(self):
        return {node.subgraph for node in self.nodes}

    def getAllInputsOfSubgraph(self, subgraph=None):
        if not subgraph:
            subgraph = self.selectedSubgraph[0]
        inputs = {node.inputs.values() for node in self.nodes if
                  node.subgraph == subgraph}
        return [j for i in inputs for j in i]

    def getAllOutputsOfSubgraph(self, subgraph=None):
        if not subgraph:
            subgraph = self.selectedSubgraph[0]
        outputs = {node.outputs.values() for node in self.nodes if
                   node.subgraph == subgraph}
        return [j for i in outputs for j in i]

    def relayInputEventsTo(self, drawItem):
        self.relayTo = drawItem

    def stopInputRelayingTo(self, drawItem):
        if self.relayTo == drawItem:
            self.relayTo = None

    def registerWatchingItem(self, item):
        self.watchingItems.add(item)

    def removeWatchingItem(self, item):
        self.watchingItems.remove(item)

    def registerGraph(self, graph):
        self.graph = graph

    def keyPressEvent(self, event):
        super(Painter2D, self).keyPressEvent(event)
        if self.relayTo:
            self.relayTo.keyPressEvent(event)

    def keyReleaseEvent(self, event):
        super(Painter2D, self).keyReleaseEvent(event)

    def wheelEvent(self, event):
        # self.scale += event.deltaX()
        up = event.angleDelta().y() > 0
        if up:
            x = 1.1
        else:
            x = .9
        self.scale *= x

        # Dirty trick to make sure the connection beziers are drawn
        # at the same zoom level as the nodes.
        self.repaint()
        self.update()

    def mousePressEvent(self, event):
        self.mouseDownPos = event.pos()
        if event.button() == Qt.RightButton:
            self.rightClickedNode = None
            for nodePoints in self.nodePoints:
                x1 = nodePoints[0].x()
                x2 = nodePoints[1].x()  # + x1
                y1 = nodePoints[0].y()
                y2 = nodePoints[1].y()  # + y1
                xx = event.pos()
                yy = xx.y()
                xx = xx.x()
                if x1 < xx < x2 and y1 < yy < y2:
                    self.rightClickedNode = nodePoints[-1]
                    break
            if not self.rightClickedNode:
                self.drag = event.pos()

        if event.button() == Qt.LeftButton:
            for item in self.watchingItems:
                item.watchDown(event.pos())
                item.collide(event.pos())
                return

            for drawItem in self.drawItems:
                if issubclass(type(drawItem), Selector) or issubclass(
                        type(drawItem), LineEdit):
                    if drawItem.collide(event.pos()):
                        break

            for point, i in self.inputPinPositions:
                # print(event.pos(), point, i)
                if abs(event.pos().x() - point.x()) < PINSIZE * self.scale and abs(
                            event.pos().y() - point.y()) < PINSIZE * self.scale:
                    self.clickedPin = i
                    if i[-8:] != 'in_array':
                        self.clickedPin = None
                        return
                    self.graph.removeConnection(i, from_self=False)
                    self.update()
                    return
            for point, i in self.outputPinPositions:
                # print(event.pos(), point, i)
                # w = node.__size__[0]*100
                if abs(event.pos().x() - point.x()) < PINSIZE * self.scale and abs(
                            event.pos().y() - point.y()) < PINSIZE * self.scale:
                    self.clickedPin = i
                    self.graph.removeConnection(i, from_self=True)
                    self.update()
                    return
            for nodePoints in self.nodePoints:
                x1 = nodePoints[0].x()
                x2 = nodePoints[1].x()  # + x1
                y1 = nodePoints[0].y()
                y2 = nodePoints[1].y()  # + y1
                xx = event.pos()
                yy = xx.y()
                xx = xx.x()
                if x1 < xx < x2 and y1 < yy < y2:
                    self.clickedNode = nodePoints[-1]
                    # print(self.clickedNode)
                    self.update()
                    self.downOverNode = event.pos()
                    return
            self.groupSelection = []
            self.selectFrame = event.pos() + (event.pos() - self.center) * (
                1 - self.scale) * 1 / self.scale
            self._selectFrame = event.pos()

    def getOutputPinAt(self, pos):
        for point, pin in self.outputPinPositions:
            if abs(pos.x() - point.x()) < 7 * self.scale and abs(
                            pos.y() - point.y()) < 7 * self.scale:
                return pin

    def getInputPinAt(self, pos):
        for point, pin in self.inputPinPositions:
            if abs(pos.x() - point.x()) < 7 * self.scale and abs(
                            pos.y() - point.y()) < 7 * self.scale:
                if pin[-8:] != 'in_array': return None
                return pin

    def mouseReleaseEvent(self, event):
        super(Painter2D, self).mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton and self.looseConnection and self.clickedPin:
            valid = True
            if ':I' in self.clickedPin:
                input_nodeID, _, input_name = self.clickedPin.partition(':I')
                try:
                    output_nodeID, _, output_name = self.getOutputPinAt(
                        event.pos()).partition(':O')
                except AttributeError:
                    valid = False
            else:
                output_nodeID, _, output_name = self.clickedPin.partition(':O')
                try:
                    input_nodeID, _, input_name = self.getInputPinAt(
                        event.pos()).partition(':I')
                except AttributeError:
                    valid = False
            if valid:
                try:
                    self.graph.connect(output_nodeID, output_name, input_nodeID,
                                       input_name)
                except TypeError:
                    util.disp_error('Cannot connect pins of different type')
            self.looseConnection = False
            self.clickedPin = None
        self.drag = False
        self.downOverNode = False

        if self.selectFrame and self.selectFrame_End:
            x1, x2 = self._selectFrame.x(), self._selectFrame_End.x()
            if x1 > x2:
                x2, x1 = x1, x2
            y1, y2 = self._selectFrame.y(), self._selectFrame_End.y()
            if y1 > y2:
                y2, y1 = y1, y2
            # x1 += self.globalOffset.x()
            # print(x1, '     ', self.globalOffset.x(), '    ', event.pos().x())
            # x2 += self.globalOffset.x()
            # y1 += self.globalOffset.y()
            # y2 += self.globalOffset.y()
            self.groupSelection = self.massNodeCollide(x1, y1,
                                                       x2, y2)
        self.selectFrame = None
        self.selectFrame_End = None
        self.repaint()
        self.update()

    def massNodeCollide(self, x, y, xx, yy):
        nodes = []
        for nodePoints in self.nodePoints:
            x1 = nodePoints[0].x()
            x2 = nodePoints[1].x()  # + x1
            y1 = nodePoints[0].y()
            y2 = nodePoints[1].y()  # + y1
            if x < x1 < xx and y < y1 < yy and x < x2 < xx and y < y2 < yy:
                nodes.append(nodePoints[-1])
                # print(self.clickedNode)
        return nodes

    def mouseMoveEvent(self, event):
        for drawItem in self.watchingItems:
            drawItem.watch(event.pos())
        super(Painter2D, self).mouseMoveEvent(event)

        if self.drag:
            self.globalOffset += event.pos() - self.drag
            self.drag = event.pos()
            # self.repaint()
            self.update()
        if self.downOverNode:
            if self.groupSelection:
                for node in self.groupSelection:
                    newPos = (event.pos() - self.downOverNode) / self.scale
                    oldPos = QtCore.QPoint(node.__pos__[0], node.__pos__[1])
                    newPos = oldPos + newPos
                    node.__pos__ = (newPos.x(), newPos.y())
                self.downOverNode = event.pos()
                self.update()
            else:
                node = self.clickedNode
                newPos = (event.pos() - self.downOverNode) / self.scale
                oldPos = QtCore.QPoint(node.__pos__[0], node.__pos__[1])
                newPos = oldPos + newPos
                node.__pos__ = (newPos.x(), newPos.y())
                self.downOverNode = event.pos()
                self.update()

        else:
            self.drawLooseConnection(event.pos())
            self.update()
        if self.selectFrame:
            self.selectFrame_End = event.pos() + (event.pos() - self.center) * (
                1 - self.scale) * 1 / self.scale
            self._selectFrame_End = event.pos()

    def getSelectedNode(self):
        return self.clickedNode

    def contextMenuEvent(self, event):
        node = self.rightClickedNode
        if not node:
            return None

        menu = QtWidgets.QMenu(self)
        delete_action = menu.addAction('Delete node')
        rename_action = menu.addAction('Rename node')
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == delete_action:
            self.delete_node(node)
        elif action == rename_action:
            self.rename_node(node)
        return None

    def delete_node(self, node):
        self.graph.deleteNode(node)
        self.unregisterNode(node)
        node.clear()
        self.repaint()

    def get_all_name(self):
        return [node.get_name() for node in self.nodes]

    def rename_node(self, node):
        text, ok = QtWidgets.QInputDialog.getText(self, 'Rename node',
                                                  'Enter new name:')
        if ok and text and text not in self.get_all_name():
            node.name = text
            self.repaint()

    def paintEvent(self, event):
        # before = time.time()
        self.inputPinPositions = []
        self.outputPinPositions = []
        self.nodePoints = []
        super(Painter2D, self).paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.HighQualityAntialiasing)
        self.drawGrid(painter)
        try:
            self.drawConnections(painter)
        except KeyError:
            pass

        painter.translate(self.width() / 2. + self.globalOffset.x(),
                          self.height() / 2. + self.globalOffset.y())
        self.center = QtCore.QPoint(self.width() / 2. + self.globalOffset.x(),
                             self.height() / 2. + self.globalOffset.y())
        painter.scale(self.scale, self.scale)
        # painter.translate(self.width()/2., self.height()/2.)
        painter.setRenderHint(QtGui.QPainter.HighQualityAntialiasing)
        # painter.drawEllipse(QtCore.QPoint(0,0),5,5)

        lastDraws = []
        halfPinSize = PINSIZE // 2

        for j, node in enumerate(self.nodes):
            if not self.selectedSubgraph[0] == node.subgraph:
                continue
            pen = QtGui.QPen()
            pen.setWidth(2)
            if node.runtime_error_happened:
                painter.setBrush(QtGui.QColor(125, 45, 45))
            elif hasattr(node, 'color'):
                painter.setBrush(node.color())
            else:
                painter.setBrush(QtGui.QColor(55, 55, 55))
            if self.clickedNode == node or node in self.groupSelection:
                painter.setBrush(QtGui.QColor(75, 75, 75))

            font = QtGui.QFont('Helvetica', 12)
            painter.setFont(font)
            path = QtGui.QPainterPath()
            x = node.__pos__[0]  # + self.globalOffset.x()
            y = node.__pos__[1]  # + self.globalOffset.y()
            w = node.__size__[0] * self.settings.value('NodeWidth')
            if len(node.__class__.__name__) > 10:
                w += len(node.__class__.__name__) * 4
            h = node.__size__[1] * (8 + PINSIZE) + 40

            path.addRoundedRect(x, y, w, h, 50, 5)
            self.nodePoints.append((QtCore.QPoint(x, y) * painter.transform(),
                                    QtCore.QPoint(x + w, y + h) * painter.transform(),
                                    node))
            painter.setPen(pen)

            painter.fillPath(path, QtGui.QColor(55, 55, 55))
            painter.drawPath(path)
            pen.setColor(QtGui.QColor(150, 150, 150))
            painter.setFont(
                QtGui.QFont('Helvetica', self.settings.value('NodeTitleFontSize')))
            painter.setPen(pen)
            painter.drawText(x, y + 3, w, h, Qt.AlignHCenter,
                             node.__class__.__name__)
            painter.drawText(x, y + 20, w, h, Qt.AlignHCenter,
                             node.get_name())
            painter.setBrush(QtGui.QColor(40, 40, 40))
            drawOffset = 33
            # for i, inputPin in enumerate(node.inputPins.values()):
            for i, drawItem in enumerate(self.drawItemsOfNode[node]['inp']):
                inputPin = drawItem.data
                try:
                    pen.setColor(Painter2D.PINCOLORS[inputPin.info.var_type[0]])
                except KeyError:
                    pen.setColor(QtGui.QColor(*inputPin.info.var_type[0].color))
                pen.setWidth(2)
                painter.setPen(pen)
                if inputPin.ID == self.clickedPin:
                    pen.setColor(Qt.red)
                    painter.setPen(pen)

                if inputPin.info.var_type[0] is chainer.Variable:
                    painter.drawEllipse(x - halfPinSize,
                                        y + drawOffset + PINSIZE, PINSIZE,
                                        PINSIZE)
                point = QtCore.QPoint(x, y + drawOffset + 4 + PINSIZE)
                point *= painter.transform()
                self.inputPinPositions.append((point, inputPin.ID))
                drawOffset += (8 + PINSIZE)
                drawItem.update(x, y + drawOffset + 8, w, h,
                                painter.transform())
                if self.graph.getConnectionOfInput(inputPin):
                    text = inputPin.name
                    drawItem.draw(painter, as_label=text)
                else:
                    item = drawItem.draw(painter)
                    if item:
                        lastDraws.append(item)

            for k, drawItem in enumerate(self.drawItemsOfNode[node]['out']):
                outputPin = drawItem.data
                # pen.setColor(QColor(0, 115, 130))
                try:
                    pen.setColor(Painter2D.PINCOLORS[outputPin.info.var_type[0]])
                except KeyError:
                    pen.setColor(QtGui.QColor(*outputPin.info.var_type[0].color))
                pen.setWidth(2)
                painter.setPen(pen)
                if outputPin.ID == self.clickedPin:
                    pen.setColor(Qt.red)
                    painter.setPen(pen)
                else:
                    painter.drawEllipse(x + w - halfPinSize,
                                        y + drawOffset + PINSIZE, PINSIZE,
                                        PINSIZE)
                    point = QtCore.QPoint(x + w - 4,
                                   y + drawOffset + 4 + PINSIZE) * painter.transform()
                drawOffset += (8 + PINSIZE)
                self.outputPinPositions.append((point, outputPin.ID))
                drawItem.update(x, y + drawOffset + 8, w, h,
                                painter.transform())
                drawItem.draw(painter)

        self.pinPositions = {value[1]: value[0] for value in
                             self.inputPinPositions + self.outputPinPositions}
        # self.drawConnections(painter)
        for item in lastDraws:
            item.draw(painter, last=True)

        self.draw_selection(painter)

    def draw_selection(self, painter):
        if self.selectFrame and self.selectFrame_End:
            painter.setBrush(QtGui.QColor(255, 255, 255, 25))
            painter.setPen(Qt.white)
            x = self.selectFrame.x()
            y = self.selectFrame.y()
            xx = self.selectFrame_End.x() - x
            yy = self.selectFrame_End.y() - y
            painter.translate(-self.width() / 2. - self.globalOffset.x(),
                              -self.height() / 2. - self.globalOffset.y())
            painter.drawRect(x, y, xx, yy)
            painter.translate(self.width() / 2. + self.globalOffset.x(),
                              self.height() / 2. + self.globalOffset.y())

    def drawConnections(self, painter):
        if not self.graph:
            print('No graph connected yet.')
            return
        if not self.pinPositions:
            return

        if self.looseConnection and self.clickedPin:
            start = self.pinPositions[self.clickedPin]
            if ':I' in self.clickedPin:
                start, end = self.looseConnection, start
            else:
                end = self.looseConnection
            self.drawBezier(start, end, Qt.white, painter)

        for output_node, connList in self.graph.connections.items():
            for info in connList:
                outputID = output_node.getOutputID(info.output_name)
                inputID = info.input_node.getInputID(info.input_name)
                var_type = output_node.getOutputInfo(info.output_name).var_type
                start = self.pinPositions[outputID]
                end = self.pinPositions[inputID]
                try:
                    color = Painter2D.PINCOLORS[var_type[0]]
                except KeyError:
                    color = QtGui.QColor(*var_type[0].color)
                rotate = None
                self.drawBezier(start, end, color, painter, rotate)

    def drawLooseConnection(self, position):
        self.looseConnection = position

    def drawBezier(self, start, end, color, painter, rotate=None):
        pen = QtGui.QPen()
        pen.setColor(color)
        pen.setWidth(self.settings.value('ConnectionLineWidth') * self.scale)
        painter.setPen(pen)
        path = QtGui.QPainterPath()
        path.moveTo(start)
        diffx = abs((start.x() - end.x()) / 2.)
        if diffx < 100 * self.scale:
            diffx = 100 * self.scale
        if rotate == 'input':
            p21 = start.x() + diffx
            p22 = start.y()
            p31 = end.x()
            p32 = end.y() - 100 * self.scale
        elif rotate == 'output':
            p21 = start.x()
            p22 = start.y() + 100 * self.scale
            p31 = end.x() - diffx
            p32 = end.y()
        elif rotate == 'both':
            p21 = start.x()
            p22 = start.y() + 100 * self.scale
            p31 = end.x()
            p32 = end.y() - 100 * self.scale
        else:
            p21 = start.x() + diffx
            p22 = start.y()
            p31 = end.x() - diffx
            p32 = end.y()
        path.cubicTo(p21, p22, p31, p32, end.x(), end.y())
        painter.drawPath(path)

    def registerNode(self, node, position, silent=False):
        if not silent:
            self.parent().parent().parent().parent().statusBar.showMessage(
                'Spawned node of class \'{}\'.'
                    .format(type(node).__name__), 2000)
        node.__painter__ = {'position': position}
        node.__pos__ = position
        node.__size__ = (1, len(node.inputs) + len(node.outputs))
        self.nodes.append(node)
        self.drawItemsOfNode[node] = {'inp': [], 'out': []}
        for out in node.outputPins.values():
            if out.info.select:
                s = Selector(node, out, self)
            else:
                s = OutputLabel(node, out, self)
            self.drawItems.append(s)
            self.drawItemsOfNode[node]['out'].append(s)
        for inp in node.inputPins.values():
            # print(inp.name)
            # if inp.name == 'TRIGGER':# and inp.connected:
            #      self.triggers.add(node)
            if inp.info.select:
                s = Selector(node, inp, self)
            else:
                s = LineEdit(node, inp, self)
            self.drawItems.append(s)
            self.drawItemsOfNode[node]['inp'].append(s)

    def unregisterNode(self, node):
        self.nodes.remove(node)
        del self.drawItemsOfNode[node]

    def drawGrid(self, painter):
        color = 105
        spacing = 100 * self.scale
        while spacing < 25:
            spacing *= 9
            color = 70 + (color - 70) / 2.5
        if color < 0:
            return

        pen = QtGui.QPen()
        pen.setColor(QtGui.QColor(color, color, color))
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        verticalN = int(self.width() / spacing / 2) + 1
        horizontalN = int(self.height() / spacing / 2) + 1
        for i in range(verticalN):
            painter.drawLine(self.width() / 2 + i * spacing, 0,
                             self.width() / 2 + i * spacing, self.height())
            painter.drawLine(QtCore.QPoint(self.width() / 2 - i * spacing, 0),
                             QtCore.QPoint(self.width() / 2 - i * spacing,
                                           self.height()))

        for i in range(horizontalN):
            painter.drawLine(0, self.height() / 2 + i * spacing, self.width(),
                             self.height() / 2 + i * spacing)
            painter.drawLine(0, self.height() / 2 - i * spacing, self.width(),
                             self.height() / 2 - i * spacing)

    def set_settings(self, settings):
        self.settings = settings


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None, painter=None):
        super(MainWindow, self).__init__(parent)

        self.iconRoot = os.path.join(os.path.dirname(__file__), '../resources')
        self.settings = QtCore.QSettings('ChainerWing', 'ChainerWing')

        self.select_data_button = QtWidgets.QPushButton('')
        self.select_data_button.clicked.connect(self.open_data_config)
        self.select_data_button.setToolTip('Select training data')

        self.setupUi(self)

        self.setWindowIcon(
            QtGui.QIcon(os.path.join(self.iconRoot, 'appIcon.png')))

        try:
            self.resize(self.settings.value("size", (900, 700)))
            self.move(self.settings.value("pos", QtCore.QPoint(50, 50)))
        except TypeError:
            pass
        self.setWindowTitle('ChainerWind')

        self.initActions()
        self.initMenus()

        painter.reportWidget = self.BottomWidget
        painter.set_settings(self.settings)

        painter.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(painter.backgroundRole(), QtGui.QColor(70, 70, 70))
        painter.setPalette(p)
        l = QtWidgets.QGridLayout()
        l.addWidget(painter)
        self.DrawArea.setLayout(l)
        self.drawer = painter

        # self.drawer.graph.spawnAndConnect()

        # to reflect initial configuration
        SettingsDialog(self, settings=self.settings).close()
        TrainDialog(self, settings=self.settings).close()
        ImageDataDialog(self, settings=self.settings).close()
        DataDialog(self, settings=self.settings).close()
        self.update_data_label()

        self.setupNodeLib()

    def setArgs(self, args):
        if args.test:
            logger.info('Performing test.')
            self.load_graph(override=args.test[0])
            self.compile_and_exe()

    def initActions(self):
        self.exit_action = QtWidgets.QAction(
            QtGui.QIcon(os.path.join(self.iconRoot, 'quit.png')), 'Quit', self)
        self.exit_action.setShortcut('Ctrl+Q')
        self.exit_action.setStatusTip('Exit application')
        self.exit_action.triggered.connect(self.close)

        self.data_action = QtWidgets.QAction(
            QtGui.QIcon(os.path.join(self.iconRoot, 'new.png')), 'Data', self)
        self.data_action.setShortcut('Ctrl+D')
        self.data_action.setStatusTip('Managing Data')
        self.data_action.triggered.connect(self.open_data_config)

        self.compile_and_exe_action = QtWidgets.QAction(
            QtGui.QIcon(os.path.join(self.iconRoot, 'run.png')),
            'Compile and Run', self)
        self.compile_and_exe_action.setShortcut('Ctrl+R')
        self.compile_and_exe_action.triggered.connect(self.compile_and_exe)
        self.compile_and_exe_action.setIconVisibleInMenu(True)
        self.addAction(self.compile_and_exe_action)

        self.load_action = QtWidgets.QAction(
            QtGui.QIcon(os.path.join(self.iconRoot, 'load.png')), 'load', self)
        self.load_action.setShortcut('Ctrl+O')
        self.load_action.triggered.connect(self.load_graph)
        self.load_action.setIconVisibleInMenu(True)
        self.addAction(self.load_action)

        self.save_action = QtWidgets.QAction(
            QtGui.QIcon(os.path.join(self.iconRoot, 'save.png')), 'save', self)
        self.save_action.setShortcut('Ctrl+S')
        self.save_action.triggered.connect(self.save_graph_and_train)
        self.save_action.setIconVisibleInMenu(True)
        self.addAction(self.save_action)

        self.clear_all_action = QtWidgets.QAction(
            QtGui.QIcon(os.path.join(self.iconRoot, 'kill.png')),
            'Clear All', self)
        # self.killRunnerAction.setShortcut('Ctrl+K')
        self.clear_all_action.triggered.connect(self.clear_all_nodes)
        self.clear_all_action.setIconVisibleInMenu(True)
        self.addAction(self.clear_all_action)

        self.compile_action = QtWidgets.QAction(
            QtGui.QIcon(os.path.join(self.iconRoot, 'unpause.png')),
            'Compile', self)
        self.compile_action.setShortcut('Ctrl+L')
        self.compile_action.triggered.connect(self.compile_runner)
        self.compile_action.setIconVisibleInMenu(True)
        self.addAction(self.compile_action)

        self.exe_action = QtWidgets.QAction(
            QtGui.QIcon(os.path.join(self.iconRoot, 'step.png')), 'Run', self)
        self.exe_action.setShortcut('Ctrl+K')
        self.exe_action.triggered.connect(self.exe_runner)
        self.exe_action.setIconVisibleInMenu(True)
        self.addAction(self.exe_action)

        self.deleteNodeAction = QtWidgets.QAction('Delete', self)
        self.deleteNodeAction.setShortcut('Delete')
        self.deleteNodeAction.triggered.connect(self.deleteNode)
        self.deleteNodeAction.setIconVisibleInMenu(True)
        self.addAction(self.deleteNodeAction)

        self.statusAction = QtWidgets.QAction('Status', self)
        # self.statusAction.setShortcut('Ctrl+R')
        self.statusAction.triggered.connect(self.updateStatus)
        self.statusAction.setIconVisibleInMenu(True)
        self.addAction(self.statusAction)

        self.train_configure_action = QtWidgets.QAction(
            QtGui.QIcon(os.path.join(self.iconRoot, 'drop.png')),
            'Train configuration', self)
        self.train_configure_action.setShortcut('Ctrl+I')
        self.train_configure_action.triggered.connect(self.open_train_config)
        self.train_configure_action.setIconVisibleInMenu(True)
        self.addAction(self.train_configure_action)

        self.prediction_action = QtWidgets.QAction(
            QtGui.QIcon(os.path.join(self.iconRoot, 'push.png')),
            'Predict by trained model', self)
        self.prediction_action.setShortcut('Ctrl+P')
        self.prediction_action.triggered.connect(self.open_prediction)
        self.prediction_action.setIconVisibleInMenu(True)
        self.addAction(self.prediction_action)

        self.settings_action = QtWidgets.QAction(
            QtGui.QIcon(os.path.join(self.iconRoot, 'settings.png')),
            'Settings', self)
        self.settings_action.setShortcut('Ctrl+T')
        self.settings_action.triggered.connect(self.openSettingsDialog)
        self.settings_action.setIconVisibleInMenu(False)
        self.addAction(self.settings_action)

        self.createSubgraphAction = QtWidgets.QAction(
            QtGui.QIcon(os.path.join(self.iconRoot, 'macro.png')),
            'Create Macro', self)
        self.createSubgraphAction.setShortcut('Ctrl+G')
        self.createSubgraphAction.triggered.connect(self.openMacroDialog)
        self.createSubgraphAction.setIconVisibleInMenu(False)
        self.addAction(self.createSubgraphAction)

    def initMenus(self):
        fileMenu = self.menuBar.addMenu('&File')
        fileMenu.addAction(self.data_action)
        fileMenu.addAction(self.save_action)
        fileMenu.addAction(self.load_action)
        fileMenu.addAction(self.exit_action)

        run_menu = self.menuBar.addMenu('&Run')
        run_menu.addAction(self.compile_and_exe_action)
        run_menu.addAction(self.compile_action)
        run_menu.addAction(self.exe_action)
        # run_menu.addAction(self.connectAction)
        # run_menu.addAction(self.createSubgraphAction)

        settingsMenu = self.menuBar.addMenu('&Settings')
        settingsMenu.addAction(self.train_configure_action)
        settingsMenu.addAction(self.settings_action)

        # self.mainToolBar.addAction(self.exitAction)
        self.mainToolBar.addWidget(self.select_data_button)
        # self.mainToolBar.addAction(self.data_action)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.save_action)
        self.mainToolBar.addAction(self.load_action)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.compile_and_exe_action)
        self.mainToolBar.addSeparator()
        # self.mainToolBar.addAction(self.pauseRunnerAction)
        self.mainToolBar.addAction(self.compile_action)
        self.mainToolBar.addAction(self.exe_action)
        # self.mainToolBar.addAction(self.gotoRunnerAction)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.prediction_action)
        # self.mainToolBar.addAction(self.updateRunnerAction)
        self.mainToolBar.addAction(self.clear_all_action)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.train_configure_action)
        self.mainToolBar.addAction(self.settings_action)

    def selectSubgraph(self):
        self.drawer.setSelectedSubgraph(self.macroSelector.currentText())
        self.drawer.update()

    def getSubgraphList(self):
        new = self.drawer.getAllSubgraphs()
        self.macroSelector.addItems(new.difference(self.knownSubgraphs))
        self.knownSubgraphs = self.knownSubgraphs.union(new)

    def open_data_config(self):
        if 'Image' in TrainParamServer()['Task']:
            try:
                import chainercv
                data_dialog = ImageDataDialog(self, settings=self.settings)
            except ImportError:
                util.disp_error('Failed to import chainercv.'
                                'See https://github.com/chainer/chainercv#installation')
                return
        else:
            data_dialog = DataDialog(self, settings=self.settings)
        data_dialog.show()
        self.update_data_label()

    def update_data_label(self):
        text = TrainParamServer().get_train_data_name()
        if text:
            self.select_data_button.setText('Selecting Data: ' + text)
        else:
            self.select_data_button.setText('Please Select Data File')

    def openMacroDialog(self):
        if not self.drawer.groupSelected():
            self.statusBar.showMessage(
                'You Must Select a Group to Create a Macro.', 2000)
            return
        name, state = QtWidgets.QInputDialog.getText(
            self, 'Create Macro', 'Macro Name:')
        if not state:
            return
        self.drawer.createSubgraph(name)
        self.getSubgraphList()

    def openSettingsDialog(self):
        SettingsDialog(self, settings=self.settings).show()

    def open_train_config(self):
        TrainDialog(self, settings=self.settings).show()

    def open_prediction(self):
        PredictionWindow(self, settings=self.settings).show()

    def connect(self):
        # TODO(fukatani): Implement.
        pass

    def close(self):
        try:
            self.drawer.graph.killRunner()
        except:
            util.disp_error('No runner to kill.')
        QtWidgets.qApp.quit()

    def updateStatus(self):
        try:
            self.drawer.graph.requestRemoteStatus()
        except AttributeError:
            self.statusBar.showMessage(
                'Cannot Update Graph. No Interpreter Available..', 2000)

    def killRunner(self):
        try:
            self.drawer.graph.killRunner()
        except ConnectionRefusedError:
            pass

    def deleteNode(self):
        node = self.drawer.getSelectedNode()
        if node:
            self.drawer.delete_node(node)

    def clear_all_nodes(self):
        while self.drawer.nodes:
            node = self.drawer.nodes[0]
            self.drawer.delete_node(node)

    def exe_runner(self):
        self.statusBar.showMessage('Run started.', 2000)
        self.drawer.graph.run()
        self.BottomWidget.update_report()

    def compile_runner(self):
        self.statusBar.showMessage('Compile started.', 2000)
        return self.drawer.graph.compile()

    def compile_and_exe(self):
        if self.compile_runner():
            self.exe_runner()
        else:
            util.disp_error('Compile is failured')

    def load_graph(self, override=False):
        if not override:
            init_path = TrainParamServer().get_work_dir()
            file_name = QtWidgets.QFileDialog.getOpenFileName(
                self, 'Open File', init_path,
                filter='Chainer Wing Files (*.json);; Any (*.*)')[0]
        else:
            file_name = override
        if not file_name: return
        logger.debug('Attempting to load graph: {}'.format(file_name))
        self.clear_all_nodes()
        with open(file_name, 'r') as fp:
            try:
                proj_dict = json.load(fp)
            except json.decoder.JSONDecodeError:
                util.disp_error(file_name + ' is corrupted.')
                return
            # proj_dict = json.load(fp, object_hook=util.nethook)
            if 'graph' in proj_dict:
                self.drawer.graph.load_from_dict(proj_dict['graph'])
                self.statusBar.showMessage(
                    'Graph loaded from {}.'.format(file_name), 2000)
                logger.info('Successfully loaded graph: {}'.format(file_name))
            if 'train' in proj_dict:
                TrainParamServer().load_from_dict(proj_dict['train'])

    def save_graph_and_train(self, *args):
        """
        Callback for the 'SaveAction'.
        :param args: throwaway arguments.
        :return: None
        """
        file_name = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save File', '~/',
            filter='Chainer Wing Files (*.json);; Any (*.*)')[0]
        if not file_name:
            return
        if not file_name.endswith('.json'):
            file_name += '.json'
        logger.debug('Attempting to save graph as {}'.format(file_name))
        with open(file_name, 'w') as fp:
            proj_dict = {'graph': self.drawer.graph.to_dict(),
                         'train': TrainParamServer().to_dict()}
            proj_dump = json.dumps(proj_dict, sort_keys=True, indent=4,
                                   cls=util.NetJSONEncoder)
            fp.write(proj_dump)
        self.statusBar.showMessage('Graph saved as {}.'.format(file_name), 2000)
        logger.info('Save graph as {}'.format(file_name))

    def resizeEvent(self, event):
        super(MainWindow, self).resizeEvent(event)
        self.drawer.repaint()
        self.drawer.update()

    def setupNodeLib(self):
        self.NodeListView.setup(self.FilterEdit, self.drawer.graph)

    def closeEvent(self, event):
        logger.debug('Attempting to kill interpreter.')
        self.killRunner()
        logger.debug('MainWindow is shutting down.')
        self.settings.setValue("size", self.size())
        self.settings.setValue("pos", self.pos())
        super(MainWindow, self).closeEvent(event)

    def keyPressEvent(self, event):
        super(MainWindow, self).keyPressEvent(event)
        if event.key() == 16777248:
            self.drawer.keyPressEvent(event)

    def keyReleaseEvent(self, event):
        super(MainWindow, self).keyReleaseEvent(event)
        if event.key() == 16777248:
            self.drawer.keyReleaseEvent(event)


class DrawItem(object):
    alignment = Qt.AlignRight

    def __init__(self, parent, data, painter):
        self.settings = painter.settings
        self.painter = painter
        self.state = False
        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0
        self.parent = parent
        self.data = data
        self.active = True

    def deactivate(self):
        self.active = False

    def activate(self):
        self.active = True

    def update(self, x, y, w, h, transform):
        self.transform = transform
        self.x = x
        self.y = y
        self.w = w - 10
        self.h = h
        point = QtCore.QPoint(x + 12, y - 16) * transform
        self._x = point.x()
        self._y = point.y()
        point = QtCore.QPoint(x + w - 24, y + h - 60) * transform
        self._xx = point.x()
        self._yy = point.y()

        self._yy = self._y + PINSIZE

    def draw(self, painter, as_label=''):
        alignment = self.__class__.alignment
        text = self.data.name
        pen = QtGui.QPen(Qt.darkGray)
        painter.setPen(pen)
        painter.setBrush(QtGui.QColor(40, 40, 40))
        xx, yy, ww, hh = self.x + self.w / 2. - (
            self.w - 25) / 2., self.y - 18, self.w - 18, 4 + PINSIZE
        self.set_font(painter)
        painter.setPen(pen)
        painter.drawText(xx + 5, yy - 3 + TEXTYOFFSET, ww - 10, hh + 5,
                         alignment, text)

    def set_font(self, painter):
        painter.setFont(
            QtGui.QFont('Helvetica', self.settings.value('FontSize')))

    def run(self):
        pass

    def setState(self, state):
        self.state = state

    def collide(self, pos):
        if not self.active:
            return False
        if self._x < pos.x() < self._xx and self._y < pos.y() < self._yy:
            return True

    def watch(self, pos):
        pass

    def watchDown(self, pos):
        pass

    def keyPressEvent(self, event):
        pass


class Selector(DrawItem):
    alignment = Qt.AlignLeft

    def __init__(self, *args, **kwargs):
        super(Selector, self).__init__(*args, **kwargs)
        self.highlight = 0
        self.select = None
        self.items = self.data.info.select
        if self.data.info.has_value_set():
            self.select = str(self.data.info.value)

    def update(self, x, y, w, h, transform):
        super(Selector, self).update(x, y, w, h, transform)
        if self.select is not None:
            self.items = self.data.info.select
            if self.data.info.has_value_set():
                self.select = str(self.data.info.value)

    def watch(self, pos):
        scale = self.painter.scale
        for i in range(1, len(self.items) + 1):
            if self._x < pos.x() < self._xx and self._y + 4 * scale + PINSIZE * i * scale < pos.y() < (
                            self._y + 4 * scale + (i + 1) * scale * PINSIZE):
                self.highlight = i
                return

    def watchDown(self, pos):
        self.select = str(self.items[self.highlight - 1])
        self.parent.inputs[self.data.name].set_value_from_text(self.select)
        # self.parent._Boolean.setDefault(self.select)
        # self.painter.removeWatchingItem(self)

    def collide(self, pos):
        if self._x < pos.x() < self._xx + 16 and self._y < pos.y() < self._yy:
            self.state = (self.state + 1) % 2
            try:
                self.painter.registerWatchingItem(self)
            except ValueError:
                pass
        else:
            if self.state:
                try:
                    self.painter.removeWatchingItem(self)
                except ValueError:
                    pass
            self.state = 0
        return super(Selector, self).collide(pos)

    def draw(self, painter, last=False, as_label=''):
        if as_label:
            text = as_label
            alignment = self.__class__.alignment
            pen = QtGui.QPen(Qt.darkGray)
            painter.setPen(pen)
            painter.setBrush(QtGui.QColor(40, 40, 40))
            xx, yy, ww, hh = self.x + self.w / 2. - (
                self.w - 25) / 2., self.y - 18, self.w - 18, 4 + PINSIZE
            self.set_font(painter)
            painter.setPen(pen)
            painter.drawText(xx + 5, yy - 3 + TEXTYOFFSET, ww - 10, hh + 5,
                             alignment, text)
            return
        if not self.state:
            alignment = self.alignment
            text = self.data.name
            if self.select:
                text = str(self.select)
            pen = QtGui.QPen(Qt.darkGray)
            painter.setPen(pen)
            painter.setBrush(QtGui.QColor(40, 40, 40))
            xx, yy, ww, hh = self.x + self.w / 2. - (
                self.w - 25) / 2., self.y - 18, self.w - 25, 4 + PINSIZE
            painter.drawRoundedRect(xx, yy, ww, hh, 2, 20)
            self.set_font(painter)
            painter.setPen(pen)
            painter.drawText(xx + 5, yy - 3 + TEXTYOFFSET, ww - 20, hh + 5,
                             alignment, text)
            pen.setColor(Qt.gray)
            # pen.setWidth(3)
            painter.setPen(pen)
            painter.setBrush(QtGui.QBrush(Qt.gray))
            points = QtCore.QPoint(xx + self.w - 40, yy - 2 + PINSIZE / 2), \
                     QtCore.QPoint(xx + 10 - 40 + self.w, yy - 2 + PINSIZE / 2), \
                     QtCore.QPoint(xx + 5 + self.w - 40, yy + 4 + PINSIZE / 2)
            painter.drawPolygon(*points)
            painter.setBrush(QtGui.QColor(40, 40, 40))
        else:
            if not last:
                return self
            alignment = self.alignment
            text = self.data.name
            pen = QtGui.QPen(Qt.darkGray)
            painter.setPen(pen)
            painter.setBrush(QtGui.QColor(40, 40, 40))
            xx, yy, ww, hh = self.x + self.w / 2. - (
                self.w - 25) / 2., self.y - 26 + 12, self.w - 25, (
                                 4 + PINSIZE) * len(self.items)
            painter.drawRoundedRect(xx, yy + PINSIZE, ww, hh, 2, 20 + PINSIZE)
            self.set_font(painter)
            painter.setPen(pen)

            for i, item in enumerate(self.items):
                item = str(item)
                if i + 1 == self.highlight:
                    pen.setColor(Qt.white)
                    painter.setPen(pen)
                else:
                    pen = QtGui.QPen(Qt.darkGray)
                    painter.setPen(pen)
                painter.drawText(xx + 5, yy + PINSIZE - 3 + i * (
                    4 + PINSIZE) + TEXTYOFFSET, ww - 20, hh + 5 + PINSIZE,
                                 alignment, item)
            # painter.drawText(xx-5, yy-3+0, ww-20, hh+5, alignment, 'True')
            # painter.drawText(xx-5, yy-3+12, ww-20, hh+5, alignment, 'False')

            pen = QtGui.QPen(Qt.darkGray)
            painter.setPen(pen)
            painter.setBrush(QtGui.QColor(60, 60, 60))
            xx, yy, ww, hh = self.x + self.w / 2. - (
                self.w - 25) / 2., self.y - 18, self.w - 25, 4 + PINSIZE
            painter.drawRoundedRect(xx, yy, ww, hh, 2, 20)
            painter.drawText(xx + 5, yy - 3 + TEXTYOFFSET, ww - 20, hh + 5,
                             alignment, text)


class LineEdit(DrawItem):
    alignment = Qt.AlignLeft

    def __init__(self, parent, data, painter):
        super(LineEdit, self).__init__(parent, data, painter)
        self.text = ''

    def collide(self, pos):
        collides = super(LineEdit, self).collide(pos)
        if collides:
            self.state = (self.state + 1) % 2
            self.painter.registerWatchingItem(self)
            self.painter.relayInputEventsTo(self)
        else:
            self.painter.stopInputRelayingTo(self)
            if self.state:
                self.painter.removeWatchingItem(self)
            self.state = 0
        return collides

    def draw(self, painter, as_label=''):
        if not self.text and not self.data.info.value:
            text = self.data.name
        else:
            text = self.data.info.value
        if as_label:
            text = as_label
            alignment = self.__class__.alignment
            pen = QtGui.QPen(Qt.darkGray)
            painter.setPen(pen)
            painter.setBrush(QtGui.QColor(40, 40, 40))
            xx, yy, ww, hh = self.x + self.w / 2. - (
                self.w - 25) / 2., self.y - 18, self.w - 18, 4 + PINSIZE
            self.set_font(painter)
            painter.setPen(pen)
            painter.drawText(xx + 5, yy - 3 + TEXTYOFFSET, ww - 10, hh + 5,
                             alignment, text)
            return
        text = str(text)
        if not self.state:
            alignment = self.__class__.alignment
            pen = QtGui.QPen(Qt.darkGray)
            painter.setPen(pen)
            painter.setBrush(QtGui.QColor(40, 40, 40))
            xx, yy, ww, hh = self.x + self.w / 2. - (
                self.w - 25) / 2., self.y - 18, self.w - 18, 4 + PINSIZE
            painter.drawRoundedRect(xx, yy, ww, hh, 2, 20)
            self.set_font(painter)
            painter.setPen(pen)
            painter.drawText(xx + 5, yy - 3 + TEXTYOFFSET, ww - 10, hh + 5,
                             alignment, text)
        else:
            alignment = self.__class__.alignment
            pen = QtGui.QPen(Qt.darkGray)
            painter.setPen(pen)
            painter.setBrush(QtGui.QColor(10, 10, 10))
            xx, yy, ww, hh = self.x + self.w / 2. - (
                self.w - 25) / 2., self.y - 18, self.w - 18, 4 + PINSIZE
            painter.drawRoundedRect(xx, yy, ww, hh, 2, 20)
            self.set_font(painter)
            painter.setPen(pen)
            painter.drawText(xx + 5, yy - 3 + TEXTYOFFSET, ww - 10, hh + 5,
                             alignment, text)

    def keyPressEvent(self, event):
        if event.key() == 16777219:  # Backspace
            self.text = self.text[:-1]
        else:
            self.text += self._sanitize_string(event.text())
        self.painter.update()
        self.parent.inputs[self.data.name].set_value_from_text(self.text)

    def _sanitize_string(self, string):
        string = string.strip('\r\n')
        try:
            if float in self.data.info.var_type and string == '.':
                return '0.'
            self.data.info.convert_var_type(string)
        except ValueError:
            return ''
        return string


class InputLabel(DrawItem):
    alignment = Qt.AlignLeft


class OutputLabel(DrawItem):
    pass
