import os
import time
from floppy.graph import Graph
from floppy.node import InputNotAvailable, ControlNode
from floppy.mainwindow import Ui_MainWindow
from floppy.floppySettings import SettingsDialog
from floppy.nodeLib import ContextNodeFilter, ContextNodeList
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QPoint, QSettings
from PyQt5.QtGui import *
from PyQt5.Qt import QTimer
import platform
import logging

logger = logging.getLogger('Floppy')


LOCALPORT = 8080
PINSIZE = 8
NODETITLEFONTSIZE = 12
CONNECTIONLINEWIDTH = 2
NODEWIDTHSCALE = 100
TEXTYOFFSET = 0
LINEEDITFONTSIZE = 8
if platform.system() is 'Windows':
    TEXTYOFFSET = 4
    LINEEDITFONTSIZE = 7


class Painter(QWidget):
    def decorateNode(self, node, position):
        return node


class Painter2D(Painter):
    PINCOLORS = {str: QColor(255, 190, 0),
                 int: QColor(0, 115, 130),
                 float: QColor(0, 200, 0),
                 object: QColor(190, 190, 190),
                 bool: QColor(190, 0, 0),}
    nodes = []
    scale = 1.
    globalOffset = QPoint(0, 0)
    drag = False
    inputPinPositions = []
    clickedPin = None
    clickedNode = None
    nodePoints = []
    downOverNode = False
    
    def __init__(self, parent=None):
        super(Painter2D, self).__init__(parent)
        self.setMouseTracking(True)
        self.timer = QTimer()
        self.timer.timeout.connect(self.checkGraph)
        self.timer.start(500)
        self.setFocusPolicy(Qt.ClickFocus)
        self.graph = None
        self.shiftDown = False
        self.looseConnection = None
        self.reportWidget = None
        self.pinPositions = {}
        self.drawItems = []
        self.drawItemsOfNode = {}
        self.watchingItems = []
        self.triggers = set()
        self.contextSensitive = False
        self.rightClickedNode = None
        self.lastReport = None

        self.mouseDownPos = None
        self.dialog = None
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
        self.triggers = set()
        self.graph = None
        self.shiftDown = False
        self.looseConnection = None
        self.reportWidget = None
        self.pinPositions = {}
        self.drawItems = []
        self.drawItemsOfNode = {}
        self.watchingItems = []
        self.rightClickedNode = None
        self.lastReport = None
        self.contextSensitive = True

        self.contextSensitive = False

        self.mouseDownPos = None
        self.dialog = None
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
            if inp.name == 'TRIGGER':
                continue
            con = self.graph.getConnectionOfInput(inp)
            if con:
                outNode = con.outputNode
                if not outNode in subgraph:
                    relayInputs.add((inp, outNode, con.outputName))
            else:
                relayInputs.add((inp, None, None))

        relayOutputs = set()
        allOutputs = self.getAllOutputsOfSubgraph(name)
        for out in allOutputs:
            cons = self.graph.getConnectionsOfOutput(out)
            if cons:
                for con in cons:
                    inpNode = con.inputNode
                    if not inpNode in subgraph:
                        relayOutputs.add((out, inpNode, con.inputName))
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
        newNode = self.graph.createSubGraphNode(name, self.graph.toJson(subgraph=name), relayInputs,
                                                relayOutputs, spawnAt=(pos.x(), pos.y()))
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
        inputs = {node.inputs.values() for node in self.nodes if node.subgraph == subgraph}
        return [j for i in inputs for j in i]

    def getAllOutputsOfSubgraph(self, subgraph=None):
        if not subgraph:
            subgraph = self.selectedSubgraph[0]
        outputs = {node.outputs.values() for node in self.nodes if node.subgraph == subgraph}
        return [j for i in outputs for j in i]

    def checkGraph(self):
        if self.graph.needsUpdate():
            self.update()

    def relayInputEventsTo(self, drawItem):
        self.relayTo = drawItem

    def stopInputRelayingTo(self, drawItem):
        if self.relayTo == drawItem:
            self.relayTo = None

    def registerWatchingItem(self, item):
        self.watchingItems.append(item)

    def removeWatchingItem(self, item):
        self.watchingItems.remove(item)

    def registerGraph(self, graph):
        self.graph = graph

    def keyPressEvent(self, event):
        super(Painter2D, self).keyPressEvent(event)
        if self.relayTo:
            self.relayTo.keyPressEvent(event)
        if event.key() == 16777248:
            self.shiftDown = True

    def keyReleaseEvent(self, event):
        super(Painter2D, self).keyReleaseEvent(event)
        if event.key() == 16777248:
            self.shiftDown = False

    def wheelEvent(self, event):
        # self.scale += event.deltaX()
        up = event.angleDelta().y()>0
        if up:
            x = 1.1
        else:
            x = .9
        self.scale *= x
        self.repaint()  # Dirty trick to make sure the connection beziers are drawn at the same zoom level as the nodes.
        self.update()

    def mousePressEvent(self, event):
        if self.dialog:
            self.dialog.close()
            self.dialog = None
        self.mouseDownPos = event.pos()
        if event.button() == Qt.RightButton:
            self.rightClickedNode = None
            for nodePoints in self.nodePoints:
                x1 = nodePoints[0].x()
                x2 = nodePoints[1].x() #+ x1
                y1 = nodePoints[0].y()
                y2 = nodePoints[1].y() #+ y1
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
                if issubclass(type(drawItem), Selector) or issubclass(type(drawItem), LineEdit):
                    if drawItem.collide(event.pos()):
                        break

            for point, i in self.inputPinPositions:
                # print(event.pos(), point, i)
                if abs(event.pos().x() - point.x()) < PINSIZE * self.scale and abs(event.pos().y() - point.y()) < PINSIZE * self.scale:
                    self.clickedPin = i
                    if self.shiftDown:
                        self.graph.removeConnection(i)
                    self.update()
                    return
            for point, i in self.outputPinPositions:
                # print(event.pos(), point, i)
                # w = node.__size__[0]*100
                if abs(event.pos().x() - point.x()) < PINSIZE * self.scale and abs(event.pos().y() - point.y()) < PINSIZE * self.scale:
                    self.clickedPin = i
                    if self.shiftDown:
                        self.graph.removeConnection(i)
                    self.update()
                    return
            for nodePoints in self.nodePoints:
                x1 = nodePoints[0].x()
                x2 = nodePoints[1].x() #+ x1
                y1 = nodePoints[0].y()
                y2 = nodePoints[1].y() #+ y1
                xx = event.pos()
                yy = xx.y()
                xx = xx.x()
                if x1 < xx < x2 and y1 < yy < y2:
                    self.clickedNode = nodePoints[-1]
                    self.graph.requestReport(self.clickedNode.ID)
                    # print(self.clickedNode)
                    self.update()
                    self.downOverNode = event.pos()
                    return
            self.groupSelection = []
            self.selectFrame = event.pos() + (event.pos() - self.center) * (1-self.scale) * 1/self.scale
            self._selectFrame = event.pos()


    def getOutputPinAt(self, pos):
        for point, pin in self.outputPinPositions:
            if abs(pos.x() - point.x()) < 7 * self.scale and abs(pos.y() - point.y()) < 7 * self.scale:
                return pin

    def getInputPinAt(self, pos):
        for point, pin in self.inputPinPositions:
            if abs(pos.x() - point.x()) < 7 * self.scale and abs(pos.y() - point.y()) < 7 * self.scale:
                return pin

    def mouseReleaseEvent(self, event):
        super(Painter2D, self).mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton and self.looseConnection and self.clickedPin:
            valid = True
            if ':I' in self.clickedPin:
                inputNodeID, _, inputName = self.clickedPin.partition(':I')
                try:
                    outputNodeID, _, outputName = self.getOutputPinAt(event.pos()).partition(':O')
                except AttributeError:
                    valid = False
            else:
                outputNodeID, _, outputName = self.clickedPin.partition(':O')
                try:
                    inputNodeID, _, inputName = self.getInputPinAt(event.pos()).partition(':I')
                except AttributeError:
                    valid = False
            if valid:
                try:
                    self.graph.connect(outputNodeID, outputName, inputNodeID, inputName)
                except TypeError:
                    print('Cannot connect pins of different type')
            else:
                if not self.shiftDown and (abs((event.pos()-self.mouseDownPos).x()) > 10 or
                                                   abs((event.pos()-self.mouseDownPos).y()) > 10):
                    # print('Do something. NOW!!!')
                    self.openDialog(event)
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
            x2 = nodePoints[1].x() #+ x1
            y1 = nodePoints[0].y()
            y2 = nodePoints[1].y() #+ y1
            if x < x1 < xx and y < y1 < yy and x < x2 < xx and y < y2 < yy:
                nodes.append(nodePoints[-1])
                # print(self.clickedNode)
        return nodes


    def openDialog(self, event):
        dialog = NodeDialog(self, event, self.clickedPin, self.graph)
        self.dialog = dialog
        dialog.show()

    def mouseMoveEvent(self, event):
        for drawItem in self.watchingItems:
            drawItem.watch(event.pos())
        super(Painter2D, self).mouseMoveEvent(event)

        if self.drag:
            self.globalOffset += event.pos()-self.drag
            self.drag = event.pos()
            # self.repaint()
            self.update()
        if self.downOverNode:
            if self.groupSelection:
                for node in self.groupSelection:
                    newPos = (event.pos() - self.downOverNode)*self.scale**-1
                    oldPos = QPoint(node.__pos__[0], node.__pos__[1])
                    newPos = oldPos + newPos
                    node.__pos__ = (newPos.x(), newPos.y())
                self.downOverNode = event.pos()
                self.update()
            else:
                node = self.clickedNode
                newPos = (event.pos() - self.downOverNode)*self.scale**-1
                oldPos = QPoint(node.__pos__[0], node.__pos__[1])
                newPos = oldPos + newPos
                node.__pos__ = (newPos.x(), newPos.y())
                self.downOverNode = event.pos()
                self.update()

        else:
            self.drawLooseConnection(event.pos())
            self.update()
        if self.selectFrame:
            self.selectFrame_End = event.pos() + (event.pos() - self.center) * (1-self.scale) * 1/self.scale
            self._selectFrame_End = event.pos()

    def getSelectedNode(self):
        return self.clickedNode

    def contextMenuEvent(self, event):
        node = self.rightClickedNode
        if not node:
            return None
        menu = QMenu(self)
        if not node in self.triggers:
            triggerAction = menu.addAction('Add Trigger')
            action = menu.exec_(self.mapToGlobal(event.pos()))
            if action == triggerAction:
                self.triggers.add(node)
        else:
            triggerAction = menu.addAction('Remove Trigger')
            action = menu.exec_(self.mapToGlobal(event.pos()))
            if action == triggerAction:
                self.triggers.discard(node)
        return None

    def paintEvent(self, event):
        # before = time.time()
        self.inputPinPositions = []
        self.outputPinPositions = []
        self.nodePoints = []
        super(Painter2D, self).paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        self.drawGrid(painter)
        try:
            self.drawConnections(painter)
        except KeyError:
            pass

        painter.translate(self.width()/2. + self.globalOffset.x(), self.height()/2. + self.globalOffset.y())
        self.center = QPoint(self.width()/2. + self.globalOffset.x(), self.height()/2. + self.globalOffset.y())
        painter.scale(self.scale, self.scale)
        #painter.translate(self.width()/2., self.height()/2.)
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        # painter.drawEllipse(QPoint(0,0),5,5)
        history, last = self.graph.getExecutionHistory()
        running = self.graph.getRunningNodes()
        report = self.graph.getReport()
        if report and not report == self.lastReport:
            self.reportWidget.updateReport(report)
            self.lastReport = report

        lastDraws = []
        halfPinSize = PINSIZE//2

        for j, node in enumerate(self.nodes):
            if not self.selectedSubgraph[0] == node.subgraph:
                continue
            j *= 3
            j += 1
            pen = QPen()
            pen.setWidth(2)
            painter.setBrush(QColor(55, 55, 55))
            if self.clickedNode == node or node in self.groupSelection:
                # pen.setColor(Qt.green)
                painter.setBrush(QColor(75, 75, 75))
            if node.ID in history:
                # if node.ID in history:
                #     pen.setColor(QColor(175,175,175))
                # else:
                #     pen.setColor(QColor(125, 125, 125))
                if node.ID == last[0]:
                    pen.setColor(Qt.white)
                else:
                    dT = history[node.ID]
                    c = int(17*(15-dT))
                    pen.setColor(QColor(0, c, c))
            elif node.ID in running:
                pen.setColor(Qt.red)
            else:
                pen.setColor(Qt.black)

            font = QFont('Helvetica', 12)
            painter.setFont(font)
            path = QPainterPath()
            x = node.__pos__[0]# + self.globalOffset.x()
            y = node.__pos__[1]# + self.globalOffset.y()
            w = node.__size__[0]*NODEWIDTHSCALE
            h = node.__size__[1]*(8+PINSIZE)+40

            path.addRoundedRect(x, y, w, h, 50, 5)
            self.nodePoints.append((QPoint(x, y)*painter.transform(), QPoint(x+w, y+h)*painter.transform(), node))
            painter.setPen(pen)

            painter.fillPath(path, QColor(55,55,55))
            # painter.drawRoundedRect(node.pos[0], node.pos[1], node.size[0], node.size[1], 50, 5)
            painter.drawPath(path)
            pen.setColor(QColor(150, 150, 150))
            painter.setFont(QFont('Helvetica', NODETITLEFONTSIZE))
            painter.setPen(pen)
            painter.drawText(x, y+3, w, h, Qt.AlignHCenter, node.__class__.__name__)
            painter.setBrush(QColor(40, 40, 40))
            drawOffset = 25
            # for i, inputPin in enumerate(node.inputPins.values()):
            for i, drawItem in enumerate(self.drawItemsOfNode[node]['inp']):
                inputPin = drawItem.data
                if inputPin.name == 'TRIGGER':
                    if not node in self.triggers and not inputPin.info.connected:
                        drawItem.update(x, y+drawOffset+8, w, h, painter.transform())
                        drawItem.deactivate()
                        drawOffset += (8 + PINSIZE)
                        continue
                    else:
                        self.triggers.add(node)
                        drawItem.activeate()
                # pen.setColor(QColor(255, 190, 0))
                try:
                    pen.setColor(Painter2D.PINCOLORS[inputPin.info.varType])
                except KeyError:
                    pen.setColor(QColor(*inputPin.info.varType.color))
                pen.setWidth(2)
                painter.setPen(pen)
                if inputPin.ID == self.clickedPin:
                    pen.setColor(Qt.red)
                    painter.setPen(pen)
                if inputPin.name == 'Control':
                    painter.drawEllipse(x-halfPinSize+w/2., y-halfPinSize, PINSIZE, PINSIZE)
                    point = QPoint(x+w/2., y) * painter.transform()
                    self.inputPinPositions.append((point, inputPin.ID))
                    continue
                else:
                    if inputPin.info.list:
                        painter.drawRect(x-halfPinSize, y+drawOffset+PINSIZE, PINSIZE, PINSIZE)
                    else:
                        painter.drawEllipse(x-halfPinSize, y+drawOffset+PINSIZE, PINSIZE, PINSIZE)
                    point = QPoint(x, y+drawOffset+4+PINSIZE) * painter.transform()
                # self.pinPositions.append((point, i+j))
                self.inputPinPositions.append((point, inputPin.ID))
                # drawOffset += 16
                drawOffset += (8 + PINSIZE)
                drawItem.update(x, y+drawOffset+8, w, h, painter.transform())
                if self.graph.getConnectionOfInput(inputPin):
                    text = inputPin.name
                    drawItem.draw(painter, asLabel=text)
                    # self.drawLabel(x, y+drawOffset+8, w, h, text, painter, Qt.AlignLeft)
                else:
                    item = drawItem.draw(painter)
                    if item:
                        lastDraws.append(item)

            # for k, outputPin in enumerate(node.outputPins.values()):
            finalBuffer = None
            for k, drawItem in enumerate(self.drawItemsOfNode[node]['out']):
                outputPin = drawItem.data
                # pen.setColor(QColor(0, 115, 130))
                try:
                    pen.setColor(Painter2D.PINCOLORS[outputPin.info.varType])
                except KeyError:
                    pen.setColor(QColor(*outputPin.info.varType.color))
                pen.setWidth(2)
                painter.setPen(pen)
                if outputPin.ID == self.clickedPin:
                    pen.setColor(Qt.red)
                    painter.setPen(pen)
                if outputPin.name == 'Final':
                    finalBuffer = (k, drawItem)
                    continue
                    # painter.drawEllipse(x-4+w/2., y+10+drawOffset, 8, 8)
                    # point = QPoint(x+w/2., y+drawOffset+14) * painter.transform()
                    # self.outputPinPositions.append((point, outputPin.ID))
                    # continue
                else:
                    if outputPin.info.list:
                        painter.drawRect(x + w-halfPinSize, y+drawOffset+PINSIZE, PINSIZE, PINSIZE)
                    else:
                        painter.drawEllipse(x + w-halfPinSize, y+drawOffset+PINSIZE, PINSIZE, PINSIZE)
                    point = QPoint(x + w-4, y+drawOffset+4+PINSIZE) * painter.transform()
                # drawOffset += 16
                drawOffset += (8 + PINSIZE)
                self.outputPinPositions.append((point, outputPin.ID))
                if not outputPin.info.select:
                    text = outputPin.name
                    # self.drawLabel(x, y+drawOffset+8, w, h, text, painter, Qt.AlignRight)
                else:
                    text = outputPin.name
                    # self.drawSelector(x, y+drawOffset+8, w, h, text, painter, Qt.AlignRight)
                drawItem.update(x, y+drawOffset+8, w, h, painter.transform())
                drawItem.draw(painter)
            if finalBuffer:
                k, drawItem = finalBuffer
                outputPin = drawItem.data
                pen.setColor(Painter2D.PINCOLORS[outputPin.info.varType])
                pen.setWidth(2)
                painter.setPen(pen)
                if outputPin.ID == self.clickedPin:
                    pen.setColor(Qt.red)
                    painter.setPen(pen)
                painter.drawEllipse(x-halfPinSize+w/2., y+10-int(PINSIZE/10)+drawOffset, PINSIZE, PINSIZE)
                point = QPoint(x+w/2., y+drawOffset+14) * painter.transform()
                self.outputPinPositions.append((point, outputPin.ID))

            # trans = painter.transform()
        self.pinPositions = {value[1]: value[0] for value in self.inputPinPositions+self.outputPinPositions}
        # self.drawConnections(painter)
        self.transform = painter.transform()
        self.transform = painter.transform()
        for item in lastDraws:
            item.draw(painter, last=True)

        if self.selectFrame and self.selectFrame_End:
            painter.setBrush(QColor(255,255,255,25))
            painter.setPen(Qt.white)
            x = self.selectFrame.x()
            y = self.selectFrame.y()
            xx = self.selectFrame_End.x() - x
            yy = self.selectFrame_End.y() - y
            painter.translate(-self.width()/2. - self.globalOffset.x(), -self.height()/2. - self.globalOffset.y())
            painter.drawRect(x, y, xx, yy)
            painter.translate(self.width()/2. + self.globalOffset.x(), self.height()/2. + self.globalOffset.y())


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

        for outputNode, connList in self.graph.connections.items():
            for info in connList:
                # print(info)
                outputID = outputNode.getOutputID(info['outputName'])
                inputID = info['inputNode'].getInputID(info['inputName'])
                varType = outputNode.getOutputInfo(info['outputName']).varType
                start = self.pinPositions[outputID]
                end = self.pinPositions[inputID]
                try:
                    color = Painter2D.PINCOLORS[varType]
                except KeyError:
                    color = QColor(*varType.color)
                rotate = None
                if issubclass(type(info['inputNode']), ControlNode) and info['inputName'] == 'Control':
                    rotate = 'input'
                    if issubclass(type(info['outputNode']), ControlNode) and info['outputName'] == 'Final':
                        rotate = 'both'
                elif issubclass(type(info['outputNode']), ControlNode) and info['outputName'] == 'Final':
                    rotate = 'output'
                self.drawBezier(start, end, color, painter, rotate)

    def drawLooseConnection(self, position):
        self.looseConnection = position

    def drawBezier(self, start, end, color, painter, rotate=None):
                pen = QPen()
                pen.setColor(color)
                pen.setWidth(CONNECTIONLINEWIDTH*self.scale)
                painter.setPen(pen)
                path = QPainterPath()
                path.moveTo(start)
                diffx = abs((start.x()-end.x())/2.)
                if diffx < 100 * self.scale:
                    diffx = 100 * self.scale
                if rotate == 'input':
                    p21 = start.x()+diffx
                    p22 = start.y()
                    p31 = end.x()
                    p32 = end.y() - 100*self.scale
                elif rotate == 'output':
                    p21 = start.x()
                    p22 = start.y() + 100 * self.scale
                    p31 = end.x()-diffx
                    p32 = end.y()
                elif rotate == 'both':
                    p21 = start.x()
                    p22 = start.y() + 100 * self.scale
                    p31 = end.x()
                    p32 = end.y() - 100*self.scale
                else:
                    p21 = start.x()+diffx
                    p22 = start.y()
                    p31 = end.x()-diffx
                    p32 = end.y()
                path.cubicTo(p21, p22, p31, p32, end.x(), end.y())
                painter.drawPath(path)


    def registerNode(self, node, position, silent=False):
        if not silent:
            self.parent().parent().parent().parent().statusBar.showMessage('Spawned node of class \'{}\'.'
                                                                           .format(type(node).__name__), 2000)
        node.__painter__ = {'position': position}
        node.__pos__ = position
        node.__size__ = (1, len(node.inputs) + len(node.outputs))
        node.__size__ = (1, node.__size__[1] if not issubclass(type(node), ControlNode) else node.__size__[1]-2)
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
            elif inp.info.name == 'Control':
                s = InputLabel(node, inp, self)
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
            color = 70 + (color-70) / 2.5
        if color < 0:
            return


        pen = QPen()
        pen.setColor(QColor(color, color, color))
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        verticalN = int(self.width() / spacing / 2) + 1
        horizontalN = int(self.height() / spacing / 2) + 1
        for i in range(verticalN):
            # painter.drawLine(self.width()/2 + self.globalOffset.x()+i*spacing, 0, self.width()/2+ self.globalOffset.x() + i*spacing, self.height())
            painter.drawLine(self.width()/2 +i*spacing, 0, self.width()/2 + i*spacing, self.height())
            # painter.drawLine(QPoint(self.width()/2 + self.globalOffset.x()-i*spacing, 0), QPoint(self.width()/2+ self.globalOffset.x() - i*spacing, self.height()))
            painter.drawLine(QPoint(self.width()/2 -i*spacing, 0), QPoint(self.width()/2 - i*spacing, self.height()))

        for i in range(horizontalN):
            # painter.drawLine(0, self.height()/2+self.globalOffset.y()+i*spacing, self.width(), self.height()/2+self.globalOffset.y()+i*spacing)
            painter.drawLine(0, self.height()/2+i*spacing, self.width(), self.height()/2+i*spacing)
            # painter.drawLine(0, self.height()/2+self.globalOffset.y()-i*spacing, self.width(), self.height()/2+self.globalOffset.y()-i*spacing)
            painter.drawLine(0, self.height()/2-i*spacing, self.width(), self.height()/2-i*spacing)


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None, painter=None):
        super(MainWindow, self).__init__(parent)

        iconRoot = os.path.realpath(__file__)
        iconRoot = os.path.join(os.path.dirname(os.path.dirname(iconRoot)), 'floppy')
        self.iconRoot = os.path.join(iconRoot, 'ressources')
        self.settings = QSettings('Floppy', 'Floppy')

        self.setupUi(self)

        self.setWindowIcon(QIcon(os.path.join(self.iconRoot, 'appIcon.png')))

        self.resize(900, 700)
        self.setWindowTitle('Floppy')

        self.initActions()
        self.initMenus()

        drawWidget = painter
        painter.reportWidget = self.BottomWidget
        drawWidget.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(drawWidget.backgroundRole(), QColor(70, 70, 70))
        drawWidget.setPalette(p)
        l = QGridLayout()
        l.addWidget(drawWidget)
        self.DrawArea.setLayout(l)
        self.drawer = drawWidget
        self.painter = drawWidget

        self.setupNodeLib()
        # self.drawer.graph.spawnAndConnect()
        self.connectHint = self.settings.value('DefaultConnection', type=str)
        settingsDialog = SettingsDialog(self, settings=self.settings, globals=globals())
        settingsDialog.close()

    def setArgs(self, args):
        if args.test:
            logger.info('Performing test.')
            self.loadGraph(override=args.test[0])
            self.runCode()

    def initActions(self):
        self.exitAction = QAction(QIcon(os.path.join(self.iconRoot, 'quit.png')), 'Quit', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect(self.close)

        self.newAction = QAction(QIcon(os.path.join(self.iconRoot, 'new.png')), 'New', self)
        self.newAction.setShortcut('Ctrl+N')
        self.newAction.setStatusTip('New Graph')
        self.newAction.triggered.connect(self.new)

        self.runAction = QAction(QIcon(os.path.join(self.iconRoot, 'run.png')), 'Run', self)
        self.runAction.setShortcut('Ctrl+R')
        self.runAction.triggered.connect(self.runCode)
        self.runAction.setIconVisibleInMenu(True)
        self.addAction(self.runAction)
        
        self.loadAction = QAction(QIcon(os.path.join(self.iconRoot, 'load.png')), 'load', self)
        self.loadAction.setShortcut('Ctrl+O')
        self.loadAction.triggered.connect(self.loadGraph)
        self.loadAction.setIconVisibleInMenu(True)
        self.addAction(self.loadAction)
        
        self.saveAction = QAction(QIcon(os.path.join(self.iconRoot, 'save.png')), 'save', self)
        self.saveAction.setShortcut('Ctrl+S')
        self.saveAction.triggered.connect(self.saveGraph)
        self.saveAction.setIconVisibleInMenu(True)
        self.addAction(self.saveAction)

        self.killRunnerAction = QAction(QIcon(os.path.join(self.iconRoot, 'kill.png')), 'Kill Interpreter', self)
        self.killRunnerAction.setShortcut('Ctrl+K')
        self.killRunnerAction.triggered.connect(self.killRunner)
        self.killRunnerAction.setIconVisibleInMenu(True)
        self.addAction(self.killRunnerAction)

        self.pauseRunnerAction = QAction(QIcon(os.path.join(self.iconRoot, 'pause.png')), 'Pause', self)
        self.pauseRunnerAction.setShortcut('Ctrl+P')
        self.pauseRunnerAction.triggered.connect(self.pauseRunner)
        self.pauseRunnerAction.setIconVisibleInMenu(True)
        self.addAction(self.pauseRunnerAction)
        
        self.unpauseRunnerAction = QAction(QIcon(os.path.join(self.iconRoot, 'unpause.png')), 'Unpause', self)
        self.unpauseRunnerAction.setShortcut('Ctrl+L')
        self.unpauseRunnerAction.triggered.connect(self.unpauseRunner)
        self.unpauseRunnerAction.setIconVisibleInMenu(True)
        self.addAction(self.unpauseRunnerAction)
        
        self.stepRunnerAction = QAction(QIcon(os.path.join(self.iconRoot, 'step.png')), 'Step', self)
        self.stepRunnerAction.setShortcut('Ctrl+K')
        self.stepRunnerAction.triggered.connect(self.stepRunner)
        self.stepRunnerAction.setIconVisibleInMenu(True)
        self.addAction(self.stepRunnerAction)
        
        self.gotoRunnerAction = QAction(QIcon(os.path.join(self.iconRoot, 'goto.png')), 'GoTo', self)
        self.gotoRunnerAction.setShortcut('Ctrl+F')
        self.gotoRunnerAction.triggered.connect(self.gotoRunner)
        self.gotoRunnerAction.setIconVisibleInMenu(True)
        self.addAction(self.gotoRunnerAction)
        
        self.updateRunnerAction = QAction(QIcon(os.path.join(self.iconRoot, 'update.png')), 'Update', self)
        self.updateRunnerAction.setShortcut('Ctrl+U')
        self.updateRunnerAction.triggered.connect(self.updateRunner)
        self.updateRunnerAction.setIconVisibleInMenu(True)
        self.addAction(self.updateRunnerAction)
        
        self.spawnRunnerAction = QAction(QIcon(os.path.join(self.iconRoot, 'spawn.png')), 'Spawn', self)
        self.spawnRunnerAction.setShortcut('Ctrl+H')
        self.spawnRunnerAction.triggered.connect(self.spawnRunner)
        self.spawnRunnerAction.setIconVisibleInMenu(True)
        self.addAction(self.spawnRunnerAction)
        
        self.deleteNodeAction = QAction('Delete', self)
        self.deleteNodeAction.setShortcut('Ctrl+D')
        self.deleteNodeAction.triggered.connect(self.deleteNode)
        self.deleteNodeAction.setIconVisibleInMenu(True)
        self.addAction(self.deleteNodeAction)
        
        self.connectAction = QAction(QIcon(os.path.join(self.iconRoot, 'connect.png')), 'Connect', self)
        self.connectAction.setShortcut('Ctrl+C')
        self.connectAction.triggered.connect(self.connect)
        self.connectAction.setIconVisibleInMenu(True)
        self.addAction(self.connectAction)
        
        self.statusAction = QAction('Status', self)
        # self.statusAction.setShortcut('Ctrl+R')
        self.statusAction.triggered.connect(self.updateStatus)
        self.statusAction.setIconVisibleInMenu(True)
        self.addAction(self.statusAction)

        self.dropAction = QAction(QIcon(os.path.join(self.iconRoot, 'drop.png')), 'Drop', self)
        self.dropAction.setShortcut('Ctrl+I')
        self.dropAction.triggered.connect(self.dropGraph)
        self.dropAction.setIconVisibleInMenu(True)
        self.addAction(self.dropAction)

        self.pushAction = QAction(QIcon(os.path.join(self.iconRoot, 'push.png')), 'Push', self)
        self.pushAction.setShortcut('Ctrl+X')
        self.pushAction.triggered.connect(self.pushGraph)
        self.pushAction.setIconVisibleInMenu(True)
        self.addAction(self.pushAction)
        
        self.settingsAction = QAction(QIcon(os.path.join(self.iconRoot, 'settings.png')), 'Settings', self)
        self.settingsAction.setShortcut('Ctrl+T')
        self.settingsAction.triggered.connect(self.openSettingsDialog)
        self.settingsAction.setIconVisibleInMenu(False)
        self.addAction(self.settingsAction)
        
        self.createSubgraphAction = QAction(QIcon(os.path.join(self.iconRoot, 'macro.png')), 'Create Macro', self)
        self.createSubgraphAction.setShortcut('Ctrl+G')
        self.createSubgraphAction.triggered.connect(self.openMacroDialog)
        self.createSubgraphAction.setIconVisibleInMenu(False)
        self.addAction(self.createSubgraphAction)
        
        self.configureAction = QAction(QIcon(os.path.join(self.iconRoot, 'configure.png')), 'configure', self)
        self.configureAction.setShortcut('Ctrl+Y')
        self.configureAction.triggered.connect(self.configureInterpreter)
        self.configureAction.setIconVisibleInMenu(False)
        self.addAction(self.configureAction)

    def initMenus(self):
        fileMenu = self.menuBar.addMenu('&File')
        fileMenu.addAction(self.exitAction)
        fileMenu.addAction(self.newAction)
        fileMenu.addAction(self.runAction)

        advancedMenu = self.menuBar.addMenu('&Advanced')
        advancedMenu.addAction(self.connectAction)
        advancedMenu.addAction(self.createSubgraphAction)

        settingsMenu = self.menuBar.addMenu('&Settings')
        settingsMenu.addAction(self.settingsAction)
        
        self.mainToolBar.addAction(self.exitAction)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.newAction)
        self.mainToolBar.addAction(self.saveAction)
        self.mainToolBar.addAction(self.loadAction)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.runAction)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.pauseRunnerAction)
        self.mainToolBar.addAction(self.unpauseRunnerAction)
        self.mainToolBar.addAction(self.stepRunnerAction)
        self.mainToolBar.addAction(self.gotoRunnerAction)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.spawnRunnerAction)
        self.mainToolBar.addAction(self.pushAction)
        self.mainToolBar.addAction(self.updateRunnerAction)
        self.mainToolBar.addAction(self.killRunnerAction)
        self.mainToolBar.addSeparator()
        # self.mainToolBar.addAction(self.deleteNodeAction)
        self.mainToolBar.addAction(self.connectAction)
        # self.mainToolBar.addAction(self.statusAction)
        self.mainToolBar.addAction(self.dropAction)



        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.settingsAction)
        self.mainToolBar.addSeparator()

        self.mainToolBar.addWidget(QLabel('Display Macro:'))
        macroSelector = QComboBox(self.mainToolBar)
        self.macroSelector = macroSelector
        macroSelector.addItem('main')
        self.knownSubgraphs = {'main'}
        macroSelector.currentTextChanged.connect(self.selectSubgraph)
        macroSelector.activated.connect(self.getSubgraphList)
        self.mainToolBar.addWidget(macroSelector)

    def selectSubgraph(self):
        self.drawer.setSelectedSubgraph(self.macroSelector.currentText())
        self.drawer.update()

    def configureInterpreter(self):
        self.drawer.graph.configureInterpreter({'framerate': 0.01, 'foo': 'bar'})

    def getSubgraphList(self):
        new = self.drawer.getAllSubgraphs()
        self.macroSelector.addItems(new.difference(self.knownSubgraphs))
        self.knownSubgraphs = self.knownSubgraphs.union(new)

    def new(self):
        self.drawer.reset()
        self.drawer.registerGraph(Graph(self.drawer))
        self.drawer.reportWidget = self.BottomWidget
        self.drawer.repaint()

    def openMacroDialog(self):
        if not self.drawer.groupSelected():
            self.statusBar.showMessage('You Must Select a Group to Create a Macro.', 2000)
            return
        name, state = QInputDialog.getText(self, 'Create Macro', 'Macro Name:')
        if not state:
            return
        self.drawer.createSubgraph(name)
        self.getSubgraphList()


    def openSettingsDialog(self):
        settingsDialog = SettingsDialog(self, settings=self.settings, globals=globals())
        settingsDialog.show()

    def connect(self):
        self.connectHint = self.settings.value('DefaultConnection', type=str)
        text = ''
        while not text:
            text, ok = QInputDialog.getItem(self, 'Connect to remote Interpreter',
                                            'IP Address/Port: (xxx.xxx.xxx:Port)',
                                            [self.connectHint])
            if not ok:
                return
        if not ':' in text:
            ip = text
            port = ''
            while not port:
                port, ok = QInputDialog.getText(self, 'Port number is missing',
                                                'Port:')
                if not ok:
                    return
        else:
            ip, port = text.split(':')
        self.connectHint = text
        import socket
        try:
            self.drawer.graph.connect2RemoteRunner(ip, port)
        except ConnectionRefusedError:
            err = QErrorMessage(self)
            err.showMessage('Connection to {} on port {} refused.'.format(ip, port))
        except socket.timeout:
            err = QErrorMessage(self)
            err.showMessage('Connection to {} on port {} timed out.'.format(ip, port))
        else:
            self.statusBar.showMessage('Connection to {} on port {} established.'.format(ip, port), 2000)

    def close(self):
        try:
            self.drawer.graph.killRunner()
        except:
            print('No runner to kill.')
        workDir = self.settings.value('WorkDir', type=str)
        for file in os.listdir(workDir):
            if file.startswith('_'):
                try:
                    os.remove(workDir+'/'+file)
                except:
                    pass
        qApp.quit()

    def updateStatus(self):
        try:
            self.drawer.graph.requestRemoteStatus()
        except AttributeError:
            self.statusBar.showMessage('Cannot Update Graph. No Interpreter Available..', 2000)

    def dropGraph(self):
        try:
            self.drawer.graph.dropGraph()
        except AttributeError:
            self.statusBar.showMessage('Cannot Drop Graph. No Interpreter Available..', 2000)

    def pushGraph(self):
        try:
            self.drawer.graph.push2Runner()
        except AttributeError:
            self.statusBar.showMessage('Cannot Push Graph. No Interpreter Available.', 2000)

    def killRunner(self):
        try:
            self.drawer.graph.killRunner()
        except ConnectionRefusedError:
            pass

    def deleteNode(self):
        node = self.drawer.getSelectedNode()
        if node:
            self.drawer.graph.deleteNode(self.drawer.getSelectedNode())
            self.drawer.unregisterNode(node)
            self.drawer.repaint()

    def stepRunner(self):
        try:
            self.drawer.graph.stepRunner()
        except AttributeError:
            self.statusBar.showMessage('Cannot Execute Graph Step. No Interpreter Available.', 2000)

    def gotoRunner(self):
        try:
            self.drawer.graph.gotoRunner(1)
        except AttributeError:
            self.statusBar.showMessage('Cannot Go To Node. No Interpreter Available.', 2000)

    def updateRunner(self):
        try:
            self.drawer.graph.updateRunner()
        except AttributeError:
            self.statusBar.showMessage('Cannot Update Interpreter. No Interpreter Available.', 2000)

    def pauseRunner(self):
        try:
            self.drawer.graph.pauseRunner()
        except AttributeError:
            self.statusBar.showMessage('Cannot Pause Interpreter. No Interpreter Available.', 2000)

    def unpauseRunner(self):
        try:
            self.drawer.graph.unpauseRunner()
        except AttributeError:
            self.statusBar.showMessage('Cannot Unpause Interpreter. No Interpreter Available.', 2000)

    def spawnRunner(self):
        logger.debug('Spawning new Runner.')
        self.statusBar.showMessage('New Remote Interpreter spawned.', 2000)
        self.drawer.graph.spawnAndConnect(LOCALPORT)
        logger.debug('Connected to Runner.')

    def runCode(self, *args):
        self.drawer.graph.execute()
        self.statusBar.showMessage('Code execution started.', 2000)

    def loadGraph(self, *args, override=False):
        if not override:
            fileName = QFileDialog.getOpenFileName(self, 'Open File', '~/',
                                                   filter='Floppy Files (*.ppy);; Any (*.*)')[0]
        else:
            fileName = override
        if fileName:
            logger.debug('Attempting to load graph: {}'.format(fileName))
            self.drawer.graph.load(fileName, callback=self.raiseErrorMessage)
            self.statusBar.showMessage('Graph loaded from {}.'.format(fileName), 2000)
            logger.info('Successfully loaded graph: {}'.format(fileName))

    def raiseErrorMessage(self, message):
        err = QErrorMessage(self)
        err.showMessage(message)
        logger.error(message)

    def saveGraph(self, *args):
        """
        Callback for the 'SaveAction'.
        :param args: throwaway arguments.
        :return: None
        """
        fileName = QFileDialog.getSaveFileName(self, 'Save File', '~/')[0]
        if not fileName:
            return
        if not fileName.endswith('.ppy'):
             fileName += '.ppy'
        logger.debug('Attempting to save graph as {}'.format(fileName))
        self.drawer.graph.save(fileName)
        self.statusBar.showMessage('Graph saved as {}.'.format(fileName), 2000)
        logger.info('Save graph as {}'.format(fileName))

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

    def activeate(self):
        self.active = True

    def update(self, x, y, w, h, transform):
        self.transform = transform
        self.x = x
        self.y = y
        self.w = w - 10
        self.h = h
        point = QPoint(x+12, y-16)*transform
        self._x = point.x()
        self._y = point.y()
        point = QPoint(x+w-24, y+h-60)*transform
        self._xx = point.x()
        self._yy = point.y()

        self._yy = self._y + PINSIZE

    def draw(self, painter, asLabel=False):
        alignment = self.__class__.alignment
        text = self.data.name
        pen = QPen(Qt.darkGray)
        painter.setPen(pen)
        painter.setBrush(QColor(40, 40, 40))
        xx, yy, ww, hh = self.x+(self.w)/2.-(self.w-25)/2., self.y-18, self.w-18, 4+PINSIZE
        painter.setFont(QFont('Helvetica', LINEEDITFONTSIZE))
        painter.setPen(pen)
        painter.drawText(xx+5, yy-3 + TEXTYOFFSET, ww-10, hh+5, alignment, text)

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
        if self.data.info.default is not None:
            self.select = str(self.data.info.default)

    def update(self, x, y, w, h, transform):
        super(Selector, self).update(x, y, w, h, transform)
        if self.select is not None:
            self.items = self.data.info.select
            if self.data.info.default is not None:
                self.select = str(self.data.info.default)

    def watch(self, pos):
        scale = self.painter.scale
        for i in range(1, len(self.items)+1):
            if self._x < pos.x() < self._xx and self._y+4*scale + PINSIZE*i*scale < pos.y() < (self._y+4*scale + (i+1)*scale*PINSIZE):
                self.highlight = i
                return

    def watchDown(self, pos):
        self.select = str(self.items[self.highlight-1])
        self.parent.inputs[self.data.name].setDefault(self.select)
        # self.parent._Boolean.setDefault(self.select)
        # self.painter.removeWatchingItem(self)

    def collide(self, pos):
        if self._x < pos.x() < self._xx+16 and self._y < pos.y() < self._yy:
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

    def draw(self, painter, last=False, asLabel=False):
        if asLabel:
            text = asLabel
            alignment = self.__class__.alignment
            pen = QPen(Qt.darkGray)
            painter.setPen(pen)
            painter.setBrush(QColor(40, 40, 40))
            xx, yy, ww, hh = self.x+(self.w)/2.-(self.w-25)/2., self.y-18, self.w-18, 4+PINSIZE
            painter.setFont(QFont('Helvetica', LINEEDITFONTSIZE))
            painter.setPen(pen)
            painter.drawText(xx+5, yy-3 + TEXTYOFFSET, ww-10, hh+5, alignment, text)
            return
        if not self.state:
            alignment = self.alignment
            text = self.data.name
            if self.select:
                text = str(self.select)
            pen = QPen(Qt.darkGray)
            painter.setPen(pen)
            painter.setBrush(QColor(40, 40, 40))
            xx, yy, ww, hh = self.x+(self.w)/2.-(self.w-25)/2., self.y-18, self.w-25, 4+PINSIZE
            painter.drawRoundedRect(xx, yy, ww, hh, 2, 20)
            painter.setFont(QFont('Helvetica', LINEEDITFONTSIZE))
            painter.setPen(pen)
            painter.drawText(xx+5, yy-3+TEXTYOFFSET, ww-20, hh+5, alignment, text)
            pen.setColor(Qt.gray)
            # pen.setWidth(3)
            painter.setPen(pen)
            painter.setBrush(QBrush(Qt.gray))
            points = QPoint(xx+self.w-40, yy-2+PINSIZE/2), QPoint(xx+10-40 + self.w, yy-2+PINSIZE/2), QPoint(xx+5+self.w-40, yy+4+PINSIZE/2)
            painter.drawPolygon(*points)
            painter.setBrush(QColor(40, 40, 40))
        else:
            if not last:
                return self
            alignment = self.alignment
            text = self.data.name
            pen = QPen(Qt.darkGray)
            painter.setPen(pen)
            painter.setBrush(QColor(40, 40, 40))
            xx, yy, ww, hh = self.x+(self.w)/2.-(self.w-25)/2., self.y-26 + 12, self.w-25, (4+PINSIZE) * len(self.items)
            painter.drawRoundedRect(xx, yy+PINSIZE, ww, hh, 2, 20+PINSIZE)
            painter.setFont(QFont('Helvetica', LINEEDITFONTSIZE))
            painter.setPen(pen)

            for i, item in enumerate(self.items):
                item = str(item)
                if i+1 == self.highlight:
                    pen.setColor(Qt.white)
                    painter.setPen(pen)
                else:
                    pen = QPen(Qt.darkGray)
                    painter.setPen(pen)
                painter.drawText(xx+5, yy+PINSIZE-3+i*(4+PINSIZE)+TEXTYOFFSET, ww-20, hh+5+PINSIZE, alignment, item)
            # painter.drawText(xx-5, yy-3+0, ww-20, hh+5, alignment, 'True')
            # painter.drawText(xx-5, yy-3+12, ww-20, hh+5, alignment, 'False')

            pen = QPen(Qt.darkGray)
            painter.setPen(pen)
            painter.setBrush(QColor(60, 60, 60))
            xx, yy, ww, hh = self.x+(self.w)/2.-(self.w-25)/2., self.y-18, self.w-25, 4+PINSIZE
            painter.drawRoundedRect(xx, yy, ww, hh, 2, 20)
            painter.drawText(xx+5, yy-3+TEXTYOFFSET, ww-20, hh+5, alignment, text)


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

    def draw(self, painter, asLabel=False):

        if not self.text and not self.data.info.default:
            text = self.data.name
        else:
            text = self.data.info.default
        if asLabel:
            text = asLabel
            alignment = self.__class__.alignment
            pen = QPen(Qt.darkGray)
            painter.setPen(pen)
            painter.setBrush(QColor(40, 40, 40))
            xx, yy, ww, hh = self.x+(self.w)/2.-(self.w-25)/2., self.y-18, self.w-18, 4+PINSIZE
            painter.setFont(QFont('Helvetica', LINEEDITFONTSIZE))
            painter.setPen(pen)
            painter.drawText(xx+5, yy-3 + TEXTYOFFSET, ww-10, hh+5, alignment, text)
            return
        text = str(text)
        if not self.state:
            alignment = self.__class__.alignment
            pen = QPen(Qt.darkGray)
            painter.setPen(pen)
            painter.setBrush(QColor(40, 40, 40))
            xx, yy, ww, hh = self.x+(self.w)/2.-(self.w-25)/2., self.y-18, self.w-18, 4+PINSIZE
            painter.drawRoundedRect(xx, yy, ww, hh, 2, 20)
            painter.setFont(QFont('Helvetica', LINEEDITFONTSIZE))
            painter.setPen(pen)
            painter.drawText(xx+5, yy-3+TEXTYOFFSET, ww-10, hh+5, alignment, text)
        else:
            alignment = self.__class__.alignment
            pen = QPen(Qt.darkGray)
            painter.setPen(pen)
            painter.setBrush(QColor(10, 10, 10))
            xx, yy, ww, hh = self.x+(self.w)/2.-(self.w-25)/2., self.y-18, self.w-18, 4+PINSIZE
            painter.drawRoundedRect(xx, yy, ww, hh, 2, 20)
            painter.setFont(QFont('Helvetica', LINEEDITFONTSIZE))
            painter.setPen(pen)
            painter.drawText(xx+5, yy-3+TEXTYOFFSET, ww-10, hh+5, alignment, text)

    def keyPressEvent(self, event):
        if event.key() == 16777219:
            self.text = self.text[:-1]
        else:
            self.text += self.sanitizeInputString(event.text())
        self.painter.update()
        self.parent.inputs[self.data.name].setDefault(self.text)
        # print(event.key())

    def sanitizeInputString(self, string):
        string = string.strip('\r\n')
        try:
            self.data.info.varType(string)
        except ValueError:
            return ''
        return string


class InputLabel(DrawItem):
    alignment = Qt.AlignLeft


class OutputLabel(DrawItem):
    pass


class NodeDialog(QDockWidget):
    """
    Container Widget handling the set up of a ContextNodeFilter widget and a ContextNodeList when connections are
    dragged into open space.
    """
    def __init__(self, painter, event, pin, graph, parent=None):
        self.graph = graph
        self.painter = painter
        self.pin = pin
        super(NodeDialog, self).__init__(parent)
        self.setTitleBarWidget(QWidget(self))
        self.setStyleSheet("NodeDialog {background-color:rgb(45,45,45) ;border:1px solid rgb(0, 0, 0); "
                           "border-color:black}")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint |Qt.X11BypassWindowManagerHint | Qt.FramelessWindowHint)
        self.setFeatures(QDockWidget.DockWidgetMovable)
        self.setFloating(True)
        pos = event.globalPos()
        self.setGeometry(pos.x(), pos.y(), 150, 250)
        dL = QVBoxLayout()
        cB = QCheckBox('Context sensitive')
        cB.setChecked(painter.contextSensitive)
        self.cB = cB

        nFilter = ContextNodeFilter()
        self.back = True if ':I' in pin else False
        nFilter.registerDialog(self, back=self.back)
        nFilter.setFocus()
        # nodeList = ContextNodeList(nFilter, painter, self)
        nodeList = ContextNodeList(self)
        nodeList.registerDialog(self)
        nodeList.registerGraph(graph)
        nodeList.registerPainter(painter)
        nodeList.setup(nFilter, graph)
        cB.stateChanged.connect(nFilter.check)
        nFilter.registerListView(nodeList)
        dL.addWidget(nFilter)
        dL.addWidget(cB)
        dL.addWidget(nodeList)
        # self.cl
        self.dialogWidget = QWidget()
        self.dialogWidget.setLayout(dL)
        self.setWidget(self.dialogWidget)

    def close(self, spawned=False):
        """
        Close the dialog and connect a newly connected node if necessary.
        :param spawned: Boolean defining whether a node was spawned and needs connecting.
        :return: None
        """
        if spawned:
            self.painter.contextSensitive = self.cB.checkState()
            newNode = self.graph.getNewestNode()
            pin = self.graph.getPinWithID(self.pin)
            if not self.back:
                endPin = newNode.getInputofType(pin.info.varType)
                if endPin:
                    self.graph.connect(self.graph.getNodeFromPinID(self.pin), self.pin.split(':')[1][1:], newNode, endPin.name)
            else:
                endPin = newNode.getOutputofType(pin.info.varType)
                if endPin:
                    # self.graph.connect(self.graph.getNodeFromPinID(self.pin), self.pin.split(':')[1][1:], newNode, endPin.name)
                    self.graph.connect(newNode, endPin.name, self.graph.getNodeFromPinID(self.pin), self.pin.split(':')[1][1:])

                # self.painter.app.connectionManager.registerStart(pin, pin.node)
                # self.painter.app.connectionManager.registerEnd(endPin, newNode)

        # painter.contextSensitive = self.cB.checkState()
        self.painter.update()
        super(NodeDialog, self).close()

    def getTypeHint(self):
        """
        Returns the name of the type of the pin the new node will be connected to.
        This is used to filter the node list for appropriate nodes.
        :return: String representing a Hint. In this case a type Hint.
        """
        pin = self.graph.getPinWithID(self.pin)
        return pin.info.varType.__name__


