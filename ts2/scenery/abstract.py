#
#   Copyright (C) 2008-2013 by Nicolas Piganeau
#   npi@m4x.org
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the
        #if self.simulation.context == utils.Context.EDITOR_SCENERY:
            #x, y = eval(value.strip('()'))
            #self.origin = QtCore.QPointF(x, y)
#   Free Software Foundation, Inc.,
#   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt
from ts2 import utils
from ts2.scenery import helper

translate = QtCore.QCoreApplication.translate

class TrackItem(QtCore.QObject):
    """A TrackItem is a piece of scenery. Each item has defined coordinates in
    the scenery layout and is connected to other items so that the trains can
    travel from one to another. The coordinates are expressed in pixels.
    The origin is the top left most corner of the scene.
    The X-axis is from left to right and the Y-axis is from top to bottom.
    """
    def __init__(self, simulation, parameters):
        """ Constructor for the TrackItem class"""
        super().__init__()
        self.simulation = simulation
        self.tiId = parameters["tiid"]
        self._name = parameters["name"]
        if parameters["maxspeed"] == "" or parameters["maxspeed"] is None:
            parameters["maxspeed"] = "0.0"
        self._maxSpeed = float(parameters["maxspeed"])
        self.tiType = "0"
        self._nextItem = None
        self._previousItem = None
        self.activeRoute = None
        self.activeRoutePreviousItem = None
        self.selected = False
        x = parameters["x"]
        y = parameters["y"]
        self._origin = QtCore.QPointF(x, y)
        self._end = QtCore.QPointF(x + 10, y)
        self._realLength = 1.0
        self._trainHead = -1
        self._trainTail = -1
        self._place = None
        self._conflictTrackItem = None
        self._gi = helper.TrackGraphicsItem(self)
        self.trackItemClicked.connect(self.simulation.itemSelected)

    def __del__(self):
        """Destructor for the TrackItem class"""
        self.simulation.scene.removeItem(self._gi)
        super().__del__()

    properties = [helper.TIProperty("tiTypeStr",
                                    translate("TrackItem", "Type"), True),
                  helper.TIProperty("tiId",
                                    translate("TrackItem", "id"), True),
                  helper.TIProperty("name",
                                    translate("TrackItem", "Name")),
                  helper.TIProperty("originStr",
                                    translate("TrackItem", "Position")),
                  helper.TIProperty("maxSpeed",
                                    translate("TrackItem",
                                              "Maximum speed (m/s)")),
                  helper.TIProperty("conflictTiId",
                                    translate("TrackItem",
                                              "Conflict item ID"))]

    fieldTypes = {
                    "tiid":"INTEGER PRIMARY KEY",
                    "titype":"VARCHAR(5)",
                    "name":"VARCHAR(100)",
                    "conflicttiid":"INTEGER",
                    "x":"DOUBLE",
                    "y":"DOUBLE",
                    "xf":"DOUBLE",
                    "yf":"DOUBLE",
                    "xr":"DOUBLE",
                    "yr":"DOUBLE",
                    "xn":"DOUBLE",
                    "yn":"DOUBLE",
                    "reverse":"BOOLEAN",
                    "reallength":"DOUBLE",
                    "maxspeed":"DOUBLE",
                    "placecode":"VARCHAR(10)",
                    "trackcode":"VARCHAR(10)",
                    "timersw":"DOUBLE",
                    "timerwc":"DOUBLE",
                    "ptiid":"INTEGER",
                    "ntiid":"INTEGER",
                    "rtiid":"INTEGER",
                    "signaltype":"VARCHAR(50)",
                    "routesset":"VARCHAR(255)",
                    "trainpresent":"VARCHAR(255)"
                 }

    trackItemClicked = QtCore.pyqtSignal(int)

    def getSaveParameters(self):
        """Returns the parameters dictionary to save this TrackItem to the
        database"""
        if self.previousItem is not None:
            previousTiId = self.previousItem.tiId
        else:
            previousTiId = None
        if self.nextItem is not None:
            nextTiId = self.nextItem.tiId
        else:
            nextTiId = None
        return  {
                    "tiid":self.tiId,
                    "titype":self.tiType,
                    "name":self.name,
                    "conflicttiid":self.conflictTiId,
                    "x":self.origin.x(),
                    "y":self.origin.y(),
                    "maxspeed":self.maxSpeed,
                    "ptiid":previousTiId,
                    "ntiid":nextTiId
                }

    ### Function factories #################################################

    def qPointFStrizer(attr):
        """Returns a function giving the str representation of attr, the
        latter being a QPointF property."""
        def getter(self):
            return "(%i, %i)" % (getattr(self, attr).x(),
                                 getattr(self, attr).y())
        return getter

    def qPointFDestrizer(attr):
        """Returns a function which updates a QPointF property from a string
        representation of a QPointF."""
        def setter(self, value):
            if self.simulation.context == utils.Context.EDITOR_SCENERY:
                x, y = eval(value.strip('()'))
                setattr(self, attr, QtCore.QPointF(x, y))
        return setter

    ### Properties #########################################################

    def _getOrigin(self):
        """Returns the origin QPointF of the TrackItem. The origin is
        generally the left end of the track represented on the TrackItem"""
        return self._origin

    def _setOrigin(self, pos):
        """Setter function for the origin property"""
        if self.simulation.context == utils.Context.EDITOR_SCENERY:
            grid = self.simulation.grid
            x = round((pos.x()) / grid) * grid
            y = round((pos.y()) / grid) * grid
            self._origin = QtCore.QPointF(x, y)
            self._gi.setPos(self._origin)
            self.updateGraphics()

    origin = property(_getOrigin, _setOrigin)
    originStr = property(qPointFStrizer("origin"),
                         qPointFDestrizer("origin"))

    def _getEnd(self):
        """Returns the end QPointF of the TrackItem. The end is
        generally the right end of the track represented on the TrackItem"""
        return self._end

    end = property(_getEnd)

    def _getName(self):
        """Returns the unique name of the trackItem"""
        return self._name

    def _setName(self, value):
        """Setter function for the name property"""
        if self.simulation.context == utils.Context.EDITOR_SCENERY:
            self._name = value
            self._gi.setToolTip(self.toolTipText)

    name = property(_getName, _setName)

    @property
    def maxSpeed(self):
        """Returns the maximum speed allowed on this LineItem, in metres per
        second"""
        if self.simulation.context == utils.Context.GAME and \
           self._maxSpeed == 0:
            return float(self.simulation.option("defaultMaxSpeed"))
        else:
            return self._maxSpeed

    @maxSpeed.setter
    def maxSpeed(self, value):
        """Setter function for the maxSpeed property"""
        if self.simulation.context == utils.Context.EDITOR_SCENERY:
            if value == "": value = "0.0"
            self._maxSpeed = float(value)

    @property
    def toolTipText(self):
        """Returns the string to show on the tool tip."""
        return ""

    @property
    def tiTypeStr(self):
        """Returns the type of this TrackItem as a string to be displayed"""
        return str(self.__class__.__name__)

    @property
    def highlighted(self):
        if self.activeRoute is None:
            return False
        else:
            return True

    def _getRealLength(self):
        return self._realLength

    realLength = property(_getRealLength)

    @property
    def place(self):
        return self._place

    @property
    def nextItem(self):
        return self._nextItem

    @nextItem.setter
    def nextItem(self, ni):
        self._nextItem = ni

    @property
    def previousItem(self):
        return self._previousItem

    @previousItem.setter
    def previousItem(self, pi):
        self._previousItem = pi

    def _getGraphicsItem(self):
        """Returns the graphics item of this TrackItem"""
        return self._gi

    graphicsItem = property(_getGraphicsItem)

    @property
    def conflictTI(self):
        return self._conflictTrackItem

    @conflictTI.setter
    def conflictTI(self, ti):
        self._conflictTrackItem = ti

    @property
    def conflictTiId(self):
        """Returns the conflict trackitem ID."""
        if self._conflictTrackItem is not None:
            return str(self._conflictTrackItem.tiId)
        else:
            return None

    @conflictTiId.setter
    def conflictTiId(self, value):
        """Setter function for the conflictTiId property."""
        if self.simulation.context == utils.Context.EDITOR_SCENERY:
            if value is not None and value != "":
                self._conflictTrackItem = \
                                        self.simulation.trackItem(int(value))
            else:
                self._conflictTrackItem = None

    ### Methods #########################################################

    def getFollowingItem(self, precedingItem, direction = -1):
        """Returns the following TrackItem linked to this one, knowing we come
        from precedingItem
        @param precedingItem TrackItem where we come from (along a route)
        @return Either _nextItem or _previousItem,depending which way we come
        from."""
        if precedingItem == self._previousItem:
            return self._nextItem
        elif precedingItem == self._nextItem:
            return self._previousItem
        else:
            return None

    def setActiveRoute(self, r, previous):
        """Sets the activeRoute and activeRoutePreviousItem informations. It
        is called upon Route activation. These information are used when other
        routes are activated in order to check the potential conflicts.
        @param r The newly active Route on this TrackItem.
        @param previous The previous TrackItem on this route (to know the
        direction)."""
        self.activeRoute = r
        self.activeRoutePreviousItem = previous
        self.updateGraphics()

    def resetActiveRoute(self):
        """Resets the activeRoute and activeRoutePreviousItem informations. It
        is called upon route desactivation."""
        self.activeRoute = None
        self.activeRoutePreviousItem = None
        self.updateGraphics()

    def setTrainHead(self, pos, prevTI = None):
        """Sets the trainHead indication on this TrackItem. The trainHead
        indication enables the drawing of a Train on this TrackItem.
        @param pos is the position of the trainHead in metres. Set to -1 if no
        Train head on this TrackItem
        @param prevTI To define the direction of the train, prevTI is a
        pointer to the previous TrackItem where the Train comes from."""
        if pos == -1:
            self._trainHead = -1
        else:
            if prevTI == self._previousItem:
                self._trainHead = pos
            else:
                self._trainHead = self._realLength - pos
        self.updateTrain()

    def setTrainTail(self, pos, prevTI = None):
        """Same as setTrainHead() but with the trainTail information."""
        if pos == -1:
            self._trainTail = -1
        else:
            if prevTI == self._previousItem:
                self._trainTail = pos
            else:
                self._trainTail = self._realLength - pos
        self.updateTrain()

    def trainPresent(self):
        """Returns True if a train is present on this TrackItem"""
        if self._trainHead != -1 or self._trainTail != -1:
            return True
        else:
            return False

    def distanceToTrainEnd(self, previousTI):
        """Returns the distance to the closest end (either trainHead or
        trainTail) of the train from previousTI."""
        if previousTI == self.previousItem:
            return min(self._trainHead, self._trainTail)
        else:
            return min(self.realLength - self._trainHead,
                       self.realLength - self._trainTail)

    def isOnPosition(self, p):
        if p.trackItem() == self:
            return True
        else:
            return False

    def trainHeadActions(self, trainId):
        """Performs the actions to be done when a train head reaches this
        TrackItem"""
        pass

    def trainTailActions(self, trainId):
        """Performs the actions to be done when a train tail reaches this
        TrackItem"""
        if self.activeRoute is not None:
            if not self.activeRoute.persistent:
                beginSignalNextRoute = \
                            self.activeRoute.beginSignal.nextActiveRoute
                if beginSignalNextRoute is None or \
                   beginSignalNextRoute != self.activeRoute:
                    if (self.activeRoutePreviousItem.activeRoute is not None
                        and self.activeRoutePreviousItem.activeRoute
                                        == self.activeRoute):
                        self.activeRoutePreviousItem.resetActiveRoute()
                        self.updateGraphics()

    def __eq__(self, ti):
        if ti is not None and self.tiId == ti.tiId:
            return True
        else:
            return False

    def __ne__(self, ti):
        if ti is None or self.tiId != ti.tiId:
            return True
        else:
            return False

    def __updateGraphics(self):
        self._gi.update()

    @QtCore.pyqtSlot()
    def updateGraphics(self):
        self.__updateGraphics()

    def updateTrain(self):
        """Updates the graphics item for train only"""
        self.updateGraphics()

    ### Graphics Methods #################################################

    def getPen(self):
        """Returns the standard pen for drawing trackItems"""
        pen = QtGui.QPen()
        pen.setWidth(3)
        pen.setJoinStyle(Qt.RoundJoin)
        pen.setCapStyle(Qt.RoundCap)
        if self.highlighted:
            pen.setColor(Qt.white)
        else:
            pen.setColor(Qt.darkGray)
        return pen

    def drawConnectionRect(self, painter, point):
        """Draws a connection rectangle on the given painter at the given
        point."""
        painter.setPen(Qt.cyan)
        painter.setBrush(Qt.NoBrush)
        topLeft = point + QtCore.QPointF(-5, -5)
        painter.drawRect(QtCore.QRectF(topLeft, QtCore.QSizeF(10, 10)))

    def graphicsBoundingRect(self):
        """This function is called by the owned TrackGraphicsItem to return
        its bounding rectangle"""
        return QtCore.QRectF(0, 0, 1, 1)

    def graphicsShape(self, shape):
        """This function is called by the owned TrackGraphicsItem to return
        its shape. The given argument is the shape given by the parent class.
        """
        return shape

    def graphicsPaint(self, painter, options, widget = 0):
        """This function is called by the owned TrackGraphicsItem to paint its
        painter. The implementation in the base class TrackItem does nothing.
        """
        pass

    def graphicsMousePressEvent(self, event):
        """This function is called by the owned TrackGraphicsItem to handle
        its mousePressEvent. In the base TrackItem class, this function only
        emits the trackItemClicked signal."""
        if event.button() == Qt.LeftButton and self.tiId > 0:
            self.trackItemClicked.emit(self.tiId)

    def graphicsMouseMoveEvent(self, event):
        """This function is called by the owned TrackGraphicsItem to handle
        its mouseMoveEvent. The implementation in the base class TrackItem
        begins a drag operation."""
        if event.buttons() == Qt.LeftButton and \
           self.simulation.context == utils.Context.EDITOR_SCENERY:
            if QtCore.QLineF(event.scenePos(), \
                     event.buttonDownScenePos(Qt.LeftButton)).length() < 3.0:
                return
            drag = QtGui.QDrag(event.widget())
            mime = QtCore.QMimeData()
            pos = event.buttonDownPos(Qt.LeftButton)
            mime.setText(self.tiType + "#" +
                         str(self.tiId)+ "#" +
                         str(pos.x()) + "#" +
                         str(pos.y()) + "#" +
                         "origin")
            drag.setMimeData(mime)
            drag.exec_()

    def graphicsDragEnterEvent(self, event):
        """This function is called by the owned TrackGraphicsItem to handle
        its dragEnterEvent. The implementation in the base class TrackItem
        does nothing."""
        pass

    def graphicsDragLeaveEvent(self, event):
        """This function is called by the owned TrackGraphicsItem to handle
        its dragLeaveEvent. The implementation in the base class TrackItem
        does nothing."""
        pass

    def graphicsDropEvent(self, event):
        """This function is called by the owned TrackGraphicsItem to handle
        its dropEvent. The implementation in the base class TrackItem
        does nothing."""
        pass


class ResizableItem(TrackItem):
    """ResizableItem is the base class for all TrackItems which can be
    resized by the user in the editor, such as line items or platform items.
    """
    def __init__(self, simulation, parameters):
        """Constructor for the ResizableItem class."""
        super().__init__(simulation, parameters)
        xf = float(parameters["xf"])
        yf = float(parameters["yf"])
        self._end = QtCore.QPointF(xf, yf)

    properties = [helper.TIProperty("tiTypeStr",
                                    translate("LineItem", "Type"), True),
                  helper.TIProperty("tiId",
                                    translate("LineItem", "id"), True),
                  helper.TIProperty("name",
                                    translate("LineItem", "Name")),
                  helper.TIProperty("originStr",
                                    translate("LineItem", "Point 1")),
                  helper.TIProperty("endStr",
                                    translate("LineItem", "Point 2")),
                  helper.TIProperty("maxSpeed",
                                    translate("LineItem",
                                              "Maximum speed (m/s)")),
                  helper.TIProperty("conflictTiId",
                                    translate("LineItem",
                                              "Conflict item ID"))]

    ### Properties #################################################

    def _setOrigin(self, pos):
        """Setter function for the origin property"""
        self._gi.prepareGeometryChange()
        super()._setOrigin(pos)

    origin = property(TrackItem._getOrigin, _setOrigin)

    def _setEnd(self, pos):
        """Setter function for the origin property"""
        if self.simulation.context == utils.Context.EDITOR_SCENERY:
            grid = self.simulation.grid
            x = round((pos.x()) / grid) * grid
            y = round((pos.y()) / grid) * grid
            self._gi.prepareGeometryChange()
            self._end = QtCore.QPointF(x, y)
            self.updateGraphics()

    end = property(TrackItem._getEnd, _setEnd)
    endStr = property(TrackItem.qPointFStrizer("end"),
                      TrackItem.qPointFDestrizer("end"))

    def _getRealOrigin(self):
        """Returns the realOrigin QPointF of the TrackItem. The realOrigin is
        a point that is in the same place than origin, but does not resize
        the item when moved."""
        return self.origin

    def _setRealOrigin(self, pos):
        """Setter function for the realOrigin property."""
        if self.simulation.context == utils.Context.EDITOR_SCENERY:
            grid = self.simulation.grid
            x = round((pos.x() + 5.0) / grid) * grid
            y = round((pos.y() + 5.0) / grid) * grid
            vector = QtCore.QPointF(x, y) - self._origin
            self._gi.prepareGeometryChange()
            self._origin += vector
            self._end += vector
            self._gi.setPos(self.realOrigin)
            self.updateGraphics()

    realOrigin = property(_getRealOrigin, _setRealOrigin)

    ### Graphics Methods #################################################

    def graphicsBoundingRect(self):
        """Returns the bounding rectangle of this ResizableItem."""
        x1 = self.origin.x()
        y1 = self.origin.y()
        x2 = self.end.x()
        y2 = self.end.y()
        if self.simulation.context == utils.Context.EDITOR_SCENERY:
            return QtCore.QRectF(-5, -5, x2 - x1 + 10, y2 - y1 + 10)
        else:
            return QtCore.QRectF(0, 0, x2 - x1, y2 - y1)

    def graphicsMouseMoveEvent(self, event):
        """This function is called by the owned TrackGraphicsItem to handle
        its mouseMoveEvent. Reimplemented in the ResizableItem class to begin
        a drag operation on corners."""
        if event.buttons() == Qt.LeftButton and \
           self.simulation.context == utils.Context.EDITOR_SCENERY:
            if QtCore.QLineF(event.scenePos(),
                         event.buttonDownScenePos(Qt.LeftButton)).length() \
                        < 3.0:
                return
            drag = QtGui.QDrag(event.widget())
            mime = QtCore.QMimeData()
            pos = event.buttonDownPos(Qt.LeftButton)
            if QtCore.QRectF(-5,-5,9,9).contains(pos):
                movedEnd = "origin"
            elif QtCore.QRectF(self.end.x() - self.origin.x() - 5,
                               self.end.y() - self.origin.y() - 5,
                               9, 9).contains(pos):
                movedEnd = "end"
                pos -= self.end - self.origin
            elif self._gi.shape().contains(pos):
                movedEnd = "realOrigin"
            if movedEnd is not None:
                mime.setText(self.tiType + "#" +
                            str(self.tiId)+ "#" +
                            str(pos.x()) + "#" +
                            str(pos.y()) + "#" +
                            movedEnd)
                drag.setMimeData(mime)
                drag.exec_()

