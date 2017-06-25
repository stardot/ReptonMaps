#!/usr/bin/env python

"""
editor.py - A Repton level editor.

Copyright (C) 2013 David Boddie <david@boddie.org.uk>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os, shelve, sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from Repton import Repton
from Repton2 import Repton2
import UEFfile

__version__ = "0.2"

serialized_types = {
    "bool": bool,
    "int": int,
    "float": float,
    "str": str
    }

def deserialize(f):

    line = f.readline().strip()
    
    if not line:
        return None
    
    if line == "{":
    
        d = {}
        while True:
            key = deserialize(f)
            if key == None:
                return d
            
            value = deserialize(f)
            d[key] = value
    
    elif line == "[":
    
        l = []
        while True:
            item = deserialize(f)
            if item == None:
                return l
            
            l.append(item)
    
    elif line == "set{":
    
        s = set()
        while True:
            item = deserialize(f)
            if item == None:
                return s
            
            s.add(item)
    
    elif line == "(":
    
        l = []
        while True:
            item = deserialize(f)
            if item == None:
                return tuple(l)
            
            l.append(item)
    
    elif line in ("}", "]", ")"):
        return None
    
    else:
        at = line.find(":")
        if at == -1:
            return None
        
        t = line[:at]
        return serialized_types.get(t, str)(line[at + 1:])

def serialize(d, f):

    if type(d) == dict:
    
        f.write("{\n")
        for key, value in d.items():
            serialize(key, f)
            serialize(value, f)
        f.write("}\n")
    
    elif type(d) == list:
    
        f.write("[\n")
        for item in d:
            serialize(item, f)
        f.write("]\n")
    
    elif type(d) == set:
    
        f.write("set{\n")
        for item in d:
            serialize(item, f)
        f.write("}\n")
    
    elif type(d) == tuple:
    
        f.write("(\n")
        for item in d:
            serialize(item, f)
        f.write(")\n")
    
    else:
        f.write(type(d).__name__ + ":" + str(d) + "\n")


class DataDict(QObject):

    updated = pyqtSignal()
    
    def __init__(self, container, parent = None):
    
        QObject.__init__(self, parent)
        
        self.setContainer(container)
    
    def setContainer(self, container):
    
        # Since the dictionary may contain dictionaries as values, and we want
        # to know when they are updated, wrap them in DataDict objects and
        # connect their updated signals to the one in this object.
        
        for key, value in container.items():
            if type(value) == dict:
                wrapper = DataDict(value)
                wrapper.updated.connect(self.updated.emit)
                container[key] = wrapper
        
        self.container = container
    
    def __getitem__(self, key):
    
        return self.container[key]
    
    def __setitem__(self, key, value):
    
        self.container[key] = value
        self.updated.emit()
    
    def __delitem__(self, key):
    
        del self.container[key]
        self.updated.emit()
    
    def __contains__(self, key):
    
        return key in self.container
    
    def has_key(self, key):
    
        return self.container.has_key(key)
    
    def keys(self):
    
        return self.container.keys()
    
    def values(self):
    
        return self.container.values()
    
    def items(self):
    
        return self.container.items()
    
    def setdefault(self, key, default):
    
        return self.container.setdefault(key, default)
    
    def __len__(self):
    
        return len(self.container)
    
    def export(self):
    
        d = {}
        for key, value in self.container.items():
        
            if isinstance(value, DataDict):
                value = value.export()
            d[key] = value
        return d


class LevelWidget(QWidget):

    destinationRequested = pyqtSignal(int, int, int)
    puzzlePieceMoved = pyqtSignal(int)
    
    def __init__(self, repton, parent = None):
    
        QWidget.__init__(self, parent)
        
        self.repton = repton
        
        self.tw = repton.tile_width
        self.th = repton.tile_height
        
        if isinstance(repton, Repton):
            if self.repton.version == "Electron":
                self.xs = 4
                self.ys = 2
            else:
                self.xs = 2
                self.ys = 1
        
        elif isinstance(repton, Repton2):
            self.xs = 2
            self.ys = 1
        
        self.levels = []
        self.level_number = 1
        self.currentTile = 0
        self.highlight = None
        
        self.setAutoFillBackground(True)
        p = QPalette()
        p.setColor(QPalette.Window, Qt.black)
        self.setPalette(p)
        
        self.pen = QPen(Qt.white)
        self.pen.setWidth(2)
        self.pen.setJoinStyle(Qt.RoundJoin)
        self.pen.setCapStyle(Qt.RoundCap)
        
        self.setMouseTracking(True)
        
        self.loadImages()
        self.loadLevels()
    
    def loadImages(self):
    
        self.tile_images = []
        
        palette = map(lambda x: qRgb(*x), self.repton.palette(self.level_number))
        
        for sprite in self.repton.read_sprites():
        
            image = QImage(sprite, self.tw, self.th, QImage.Format_Indexed8).scaled(self.xs * self.tw, self.ys * self.th)
            image.setColorTable(palette)
            self.tile_images.append(image)
    
    def loadLevels(self):
    
        self.levels = self.repton.read_levels()
        
        if isinstance(self.repton, Repton2):
        
            transporters, destinations = self.repton.read_transporter_defs()
            self.transporters = DataDict(transporters)
            self.destinations = DataDict(destinations)
            self.puzzle, self.piece_numbers = self.repton.read_puzzle_defs()
    
    def setTileImages(self, tile_images):
    
        self.tile_images = tile_images
    
    def clearLevel(self):
    
        for row in range(32):
            for column in range(32):
                self.writeTile(column, row, self.currentTile)
    
    def setLevel(self, number):
    
        self.level_number = number
        self.loadImages()
        
        if isinstance(self.repton, Repton):
            self.highlight = (4, 4)
        else:
            # Some transporters are not stored on the map. Adjust the level
            # data to make them visible.
            for row in range(32):
                for column in range(32):
                    if (column, row) in self.transporters[self.level_number - 1] \
                      and self.levels[self.level_number - 1][row][column] != 2:
                        self.levels[self.level_number - 1][row][column] = 2
        
        self.update()
    
    def mousePressEvent(self, event):
    
        r = self._row_from_y(event.y())
        c = self._column_from_x(event.x())
        
        if event.button() == Qt.LeftButton:
            self.writeTile(c, r, self.currentTile)
        elif event.button() == Qt.MiddleButton:
            self.writeTile(c, r, 0)
        else:
            event.ignore()
    
    def mouseMoveEvent(self, event):
    
        r = self._row_from_y(event.y())
        c = self._column_from_x(event.x())
        
        if event.buttons() & Qt.LeftButton:
            self.writeTile(c, r, self.currentTile)
        elif event.buttons() & Qt.MiddleButton:
            self.writeTile(c, r, 0)
        else:
            self.updateCursor(event)
            event.ignore()
    
    def mouseReleaseEvent(self, event):
    
        self.updateCursor(event)
    
    def paintEvent(self, event):
    
        painter = QPainter()
        painter.begin(self)
        painter.fillRect(event.rect(), QBrush(Qt.black))
        
        painter.setPen(self.pen)
        
        y1 = event.rect().top()
        y2 = event.rect().bottom()
        x1 = event.rect().left()
        x2 = event.rect().right()
        
        r1 = max(0, self._row_from_y(y1))
        r2 = max(0, self._row_from_y(y2))
        c1 = self._column_from_x(x1)
        c2 = self._column_from_x(x2)
        
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
            
                tile = self.levels[self.level_number - 1][r][c]
                
                if isinstance(self.repton, Repton2):
                    if tile == 2:
                        tile = self.getTransporterOrPuzzleTile(r, c)
                    elif tile == 9:
                        tile = self.getFinishOrSpiritTile(r, c)
                
                tile_image = self.tile_images[tile]
                
                painter.drawImage(c * self.tw * self.xs, r * self.th * self.ys,
                                  tile_image)
        
        if self.highlight:
            x1 = (self.highlight[0] * self.tw * self.xs) + 2
            y1 = (self.highlight[1] * self.th * self.ys) + 2
            w = (self.tw * self.xs) - 3
            h = (self.th * self.ys) - 3
            painter.drawRect(x1, y1, w, h)
            painter.drawLine(x1, y1, x1 + w, y1 + h)
            painter.drawLine(x1, y1 + h, x1 + w, y1)
        
        painter.end()
    
    def contextMenuEvent(self, event):
    
        if isinstance(self.repton, Repton):
            event.ignore()
            return
        
        r, c = self._row_from_y(event.y()), self._column_from_x(event.x())
        if (c, r) in self.transporters[self.level_number - 1]:
        
            screen, (x, y) = self.transporters[self.level_number - 1][(c, r)]
            
            menu = QMenu(self.tr("Transporter"))
            goAction = menu.addAction(self.tr("Go to destination"))
            goAction.details = (screen, (x, y))
        
        elif (c, r) in self.destinations[self.level_number - 1]:
        
            menu = QMenu(self.tr("Destination"))
            
            for screen, (x, y) in self.destinations[self.level_number - 1][(c, r)]:
            
                goAction = menu.addAction(self.tr("Go to transporter: %1 (%2,%3)").arg(chr(65+screen)).arg(x).arg(y))
                goAction.details = (screen, (x, y))
        
        elif (c, r) in self.puzzle[self.level_number - 1]:
            number, destination = self.puzzle[self.level_number - 1][(c, r)]
            
            menu = QMenu(self.tr("Puzzle"))
            goAction = menu.addAction(self.tr("Go to destination"))
            screen = 0
            x = 8 + (destination % 16)
            y = 24 + (destination / 16)
            goAction.details = (screen, (x, y))
        
        else:
            event.ignore()
            return
        
        action = menu.exec_(event.globalPos())
        if action:
            screen, (x, y) = action.details
            self.destinationRequested.emit(screen + 1, x, y)
            self.highlight = (x, y)
    
    def updateCursor(self, event):
    
        if isinstance(self.repton, Repton):
            return
        
        r, c = self._row_from_y(event.y()), self._column_from_x(event.x())
        if (c, r) in self.transporters[self.level_number - 1]:
            self.setCursor(Qt.PointingHandCursor)
        elif (c, r) in self.destinations[self.level_number - 1]:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.unsetCursor()
    
    def sizeHint(self):
    
        return QSize(32 * self.tw * self.xs, 32 * self.th * self.ys)
    
    def _row_from_y(self, y):
    
        return y/(self.th * self.ys)
    
    def _column_from_x(self, x):
    
        return x/(self.tw * self.xs)
    
    def _y_from_row(self, r):
    
        return r * self.th * self.ys
    
    def _x_from_column(self, c):
    
        return c * self.tw * self.xs
    
    def getTransporterOrPuzzleTile(self, r, c):
    
        try:
            if (c, r) in self.transporters[self.level_number - 1]:
                # Transporters actually use tile 11.
                return 11
            elif (c, r) in self.puzzle[self.level_number - 1]:
                # Our puzzle piece numbers are recorded in the first tuple
                # element. We translate this to a tile number.
                return self.puzzle[self.level_number - 1][(c, r)][0] + 32
        except KeyError:
            pass
        
        # We should never reach here with self-consistent data.
        return 0
    
    def getFinishOrSpiritTile(self, r, c):
    
        # Replace the finishing piece with spirits on all levels except for
        # the first.
        if self.level_number == 1:
            return 9
        else:
            return 74
    
    def updateCell(self, c, r):
    
        self.update(QRect(self._x_from_column(c), self._y_from_row(r),
              self.tw * self.xs, self.th * self.ys))
    
    def writeTile(self, c, r, tile):
    
        if not (0 <= r < 32 and 0 <= c < 32):
            return
        
        if isinstance(self.repton, Repton2):
            # Do not allow spirits to be used on Screen A or the finishing piece
            # to be used on other screens.
            if tile == 74 and self.level_number == 1:
                return
            elif tile == 9 and self.level_number != 1:
                return
        
        previous = self.levels[self.level_number - 1][r][c]
        
        old_highlight = self.highlight
        self.highlight = (c, r)
        
        if old_highlight:
            self.updateCell(old_highlight[0], old_highlight[1])
        
        if isinstance(self.repton, Repton2):
        
            if previous == 2:
            
                # Find out what the previous tile refer to.
                actual_previous = self.getTransporterOrPuzzleTile(r, c)
                
                # If there is no change, just return.
                if actual_previous == tile:
                    return
                
                if actual_previous == 11:
                
                    # Remove the transporter entry at this location.
                    dest_screen, (x, y) = self.transporters[self.level_number - 1][(c, r)]
                    del self.transporters[self.level_number - 1][(c, r)]
                    self.destinations[dest_screen][(x, y)].remove((self.level_number - 1, (c, r)))
                    
                    # Remove the set for this entry if it is empty.
                    if not self.destinations[dest_screen][(x, y)]:
                        del self.destinations[dest_screen][(x, y)]
                
                elif 32 <= actual_previous < 74:
                
                    # The puzzle piece at this location is removed.
                    number, destination = self.puzzle[self.level_number - 1][(c, r)]
                    del self.puzzle[self.level_number - 1][(c, r)]
                    del self.piece_numbers[number]
                    
                    self.puzzlePieceMoved.emit(number)
            
            if tile == 11:
            
                # Create a new transporter entry. The new transporter's
                # destination is its own location.
                self.transporters[self.level_number - 1][(c, r)] = (self.level_number - 1, (c, r))
                s = self.destinations[self.level_number - 1].setdefault((c, r), set())
                s.add((self.level_number - 1, (c, r)))
                
                # Insert tile 2 instead.
                tile = 2
            
            elif tile < 3:
            
                # Write a blank space, even though tile 2 is technically a
                # transporter tile when stored in map data and tile 1 is a
                # transporter destination.
                tile = 0
            
            elif tile == 74:
            
                # Spirit (only available on Screen A)
                tile = 9
            
            elif 32 <= tile <= 73:
            
                # Puzzle pieces are handled like transporters, except that each one
                # is unique.
                number = tile - 32
                try:
                    old_screen, (old_x, old_y) = self.piece_numbers[number]
                    if old_screen == self.level_number - 1:
                        self.writeTile(old_x, old_y, 0)
                    
                    # Remove the entry from the puzzle dictionary. The piece's
                    # entry in the number dictionary will be redefined. Place a
                    # blank tile where the piece used to be.
                    del self.puzzle[old_screen][(old_x, old_y)]
                    self.levels[old_screen][old_y][old_x] = 0
                except KeyError:
                    pass
                
                self.puzzle[self.level_number - 1][(c, r)] = (number, 0)
                self.piece_numbers[number] = (self.level_number - 1, (c, r))
                
                self.puzzlePieceMoved.emit(number)
                
                # Insert tile 2 instead.
                tile = 2
        
        self.levels[self.level_number - 1][r][c] = tile
        self.updateCell(c, r)
    
    def setDestination(self, details):
    
        if not self.highlight:
            return
        
        screen, (x, y) = details
        self.transporters[screen][(x, y)] = (self.level_number - 1, self.highlight)
        s = self.destinations[self.level_number - 1].setdefault(self.highlight, set())
        s.add((screen, (x, y)))


class TransportersWidget(QListWidget):

    transporterSelected = pyqtSignal(tuple)
    
    def __init__(self, transporters, destinations, parent = None):
    
        QListWidget.__init__(self, parent)
        self.transporters = transporters
        self.destinations = destinations
        
        metrics = QFontMetrics(self.font())
        self.width = metrics.width("X (XX,XX) X (XX,XX)")
        self.height = 256
        
        self.updateDelayTimer = QTimer()
        self.updateDelayTimer.setInterval(200)
        
        self.transporters.updated.connect(self.updateDelayTimer.start)
        self.updateDelayTimer.timeout.connect(self.updateData)
        self.itemDoubleClicked.connect(self.setDestination)
        
        self.setLayout(QVBoxLayout())
        self.setToolTip(self.tr("Double click an item to set the transporter's destination."))
        self.updateData()
    
    def updateData(self):
    
        self.updateDelayTimer.stop()
        
        transporters = self.transporters.items()
        transporters.sort()
        
        self.clear()
        
        for screen, defs in transporters:
        
            for (x, y), (dest_screen, (dest_x, dest_y)) in defs.items():
            
                item = QListWidgetItem(self.tr(u"%1 (%2,%3) %4 (%5,%6)").arg(
                    chr(65+screen)).arg(x).arg(y).arg(chr(65+dest_screen)).arg(
                    dest_x).arg(dest_y))
                item.details = (screen, (x, y))
                self.addItem(item)
    
    def setDestination(self, item):
    
        self.transporterSelected.emit(item.details)
    
    def sizeHint(self):
    
        return QSize(self.width, self.height)


class TotalsWidget(QWidget):

    def __init__(self, levelWidget, parent = None):
    
        QWidget.__init__(self, parent)
        
        self.levelWidget = levelWidget
        self.calculated = False
        
        self.diamondsEdit = QSpinBox()
        self.diamondsEdit.setMaximum(9999)
        self.earthEdit = QSpinBox()
        self.earthEdit.setMaximum(9999)
        self.monstersEdit = QSpinBox()
        self.monstersEdit.setMaximum(99)
        self.transportersEdit = QSpinBox()
        self.transportersEdit.setMaximum(99)
        self.puzzleEdit = QSpinBox()
        self.puzzleEdit.setMaximum(42)
        
        recalcButton = QPushButton(self.tr("&Recalculate"))
        recalcButton.clicked.connect(self.recalculateTotals)
        
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        form.addRow(self.tr("&Diamonds:"), self.diamondsEdit)
        form.addRow(self.tr("&Earth:"), self.earthEdit)
        form.addRow(self.tr("&Monsters:"), self.monstersEdit)
        form.addRow(self.tr("&Transporters:"), self.transportersEdit)
        layout.addLayout(form)
        
        layout.addWidget(recalcButton)
        layout.addStretch(1)
    
    def recalculateTotals(self):
    
        totals = self.levelWidget.repton.recalculateTotals(
            self.levelWidget.levels, self.levelWidget.transporters,
            self.levelWidget.piece_numbers)
        
        self.setTotals(totals)
        self.calculated = True
    
    def totals(self):
    
        if not self.calculated:
            self.recalculateTotals()
        
        return (self.diamondsEdit.value(), self.earthEdit.value(),
                self.monstersEdit.value(), self.transportersEdit.value(),
                self.puzzleEdit.value())
    
    def setTotals(self, totals):
    
        diamonds, earth, monsters, transporters, pieces = totals
        
        self.diamondsEdit.setValue(diamonds)
        self.earthEdit.setValue(earth)
        self.monstersEdit.setValue(monsters)
        self.transportersEdit.setValue(transporters)
        self.puzzleEdit.setValue(pieces)


class EditorWindow(QMainWindow):

    def __init__(self, repton):
    
        QMainWindow.__init__(self)
        
        if isinstance(repton, Repton):
            self.xs = 4
            self.ys = 2
        elif isinstance(repton, Repton2):
            self.xs = 2
            self.ys = 1
        
        self.tw = repton.tile_width
        self.th = repton.tile_height
        
        self.repton = repton
        
        self.path = ""
        
        self.levelWidget = LevelWidget(repton)
        self.levelWidget.destinationRequested.connect(self.goToDestination)
        self.levelWidget.puzzlePieceMoved.connect(self.updatePuzzleTiles)
        
        self.createDocks()
        self.createToolBars()
        self.createMenus()
        
        # Select the first tile in the tiles toolbar and the first level in the
        # levels menu.
        self.tileGroup.actions()[0].trigger()
        self.levelsGroup.actions()[0].trigger()
        
        if isinstance(self.repton, Repton2):
            self.levelWidget.highlight = (16, 7)
        
        area = QScrollArea()
        area.setWidget(self.levelWidget)
        self.setCentralWidget(area)
    
    def saveAs(self):
    
        if self.repton.version == "Electron":
            file_type = self.tr("UEF files (*.uef)")
        else:
            file_type = self.tr("SSD files (*.ssd)")
        
        path = QFileDialog.getSaveFileName(self, self.tr("Save As"),
                                           self.path, file_type)
        if not path.isEmpty():
        
            if self.saveLevels(unicode(path)):
                self.path = path
                self.setWindowTitle(self.tr(path))
            else:
                QMessageBox.warning(self, self.tr("Save Levels"),
                    self.tr("Couldn't write the new executable to %1.\n").arg(path))
    
    def saveLevels(self, path):
    
        # Write the levels back to the UEF file.
        if isinstance(self.repton, Repton):
            self.repton.write_levels(self.levelWidget.levels)
        
        elif isinstance(self.repton, Repton2):
        
            totals = self.totalsDock.widget().totals()
            
            self.repton.write_levels(self.levelWidget.levels,
                                     self.levelWidget.transporters,
                                     self.levelWidget.puzzle,
                                     totals)
        else:
            return
        
        if self.repton.version == "Electron":
            return self.repton.saveUEF(path, __version__)
        else:
            return self.repton.saveSSD(path)
    
    def importAs(self):
    
        path = QFileDialog.getOpenFileName(self, self.tr("Import File"),
                                           self.path, self.tr("Level files (*.rdat);;Old level files (*.lev)"))
        if path.isEmpty():
            return
        
        path = unicode(path)
        
        try:
            if path.endswith(".lev"):
                d = shelve.open(path)
            else:
                d = deserialize(open(path))
            
            self.levelWidget.levels = d["levels"]
            
            if isinstance(self.repton, Repton2):
            
                self.levelWidget.transporters.setContainer(d["transporters"])
                self.levelWidget.destinations.setContainer(d["destinations"])
                self.levelWidget.puzzle = d["puzzle"]
                self.levelWidget.piece_numbers = d["piece numbers"]
                self.totalsDock.widget().setTotals(d["totals"])
            
            if path.endswith(".lev"):
                d.close()
            
            self.setLevel(1)
        
        except IOError:
            QMessageBox.warning(self, self.tr("Import Levels"),
                self.tr("Couldn't read the level data from %1.\n").arg(path))
    
    def exportAs(self):
    
        path = QFileDialog.getSaveFileName(self, self.tr("Export As"),
                                           self.path, self.tr("Level files (*.rdat)"))
        if path.isEmpty():
            return
        
        path = unicode(path)
        
        try:
            d = {}
            d["levels"] = self.levelWidget.levels
            
            if isinstance(self.repton, Repton2):
            
                d["transporters"] = self.levelWidget.transporters.export()
                d["destinations"] = self.levelWidget.destinations.export()
                d["puzzle"] = self.levelWidget.puzzle
                d["piece numbers"] = self.levelWidget.piece_numbers
                d["totals"] = self.totalsDock.widget().totals()
            
            serialize(d, open(path, "w"))
        
        except IOError:
            QMessageBox.warning(self, self.tr("Export Levels"),
                self.tr("Couldn't write the level data to %1.\n").arg(path))
    
    def createDocks(self):
    
        if isinstance(self.repton, Repton):
            return
        
        self.transportersDock = QDockWidget(self.tr("Transporters"))
        
        transportersWidget = TransportersWidget(self.levelWidget.transporters,
                                                self.levelWidget.destinations)
        transportersWidget.transporterSelected.connect(self.levelWidget.setDestination)
        
        self.transportersDock.setWidget(transportersWidget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.transportersDock)
        self.transportersDock.hide()
        
        self.totalsDock = QDockWidget(self.tr("Totals"))
        totalsWidget = TotalsWidget(self.levelWidget)
        
        self.totalsDock.setWidget(totalsWidget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.totalsDock)
        self.totalsDock.hide()
    
    def createToolBars(self):
    
        self.tileGroup = QActionGroup(self)
        
        if isinstance(self.repton, Repton):
            collection = [range(0, 32)]
            toolbar_areas = [Qt.TopToolBarArea]
            titles = [self.tr("Tiles")]
        else:
            # 32 tiles + 42 puzzle pieces + 1 spirit = 75
            collection = [range(0, 32) + [74], range(32, 74)]
            toolbar_areas = [Qt.TopToolBarArea, Qt.BottomToolBarArea]
            titles = [self.tr("Tiles"), self.tr("Puzzle Pieces")]
        
        for symbols, area, title in zip(collection, toolbar_areas, titles):
        
            tilesToolBar = QToolBar(title)
            self.addToolBar(area, tilesToolBar)
            
            for symbol in symbols:
            
                if 32 <= symbol < 74:
                    icon = self.puzzleIcon(symbol)
                else:
                    icon = QIcon(QPixmap.fromImage(self.levelWidget.tile_images[symbol]))
                action = tilesToolBar.addAction(icon, str(symbol))
                action.setData(QVariant(symbol))
                action.setCheckable(True)
                self.tileGroup.addAction(action)
                action.triggered.connect(self.setCurrentTile)
    
    def createMenus(self):
    
        fileMenu = self.menuBar().addMenu(self.tr("&File"))
        
        newAction = fileMenu.addAction(self.tr("&New"))
        newAction.setShortcut(QKeySequence.New)
        
        saveAsAction = fileMenu.addAction(self.tr("Save &As..."))
        saveAsAction.setShortcut(QKeySequence.SaveAs)
        saveAsAction.triggered.connect(self.saveAs)
        
        importAsAction = fileMenu.addAction(self.tr("Import Levels..."))
        importAsAction.triggered.connect(self.importAs)
        
        exportAsAction = fileMenu.addAction(self.tr("Export As..."))
        exportAsAction.triggered.connect(self.exportAs)
        
        quitAction = fileMenu.addAction(self.tr("E&xit"))
        quitAction.setShortcut(self.tr("Ctrl+Q"))
        quitAction.triggered.connect(self.close)
        
        editMenu = self.menuBar().addMenu(self.tr("&Edit"))
        clearAction = editMenu.addAction(self.tr("&Clear"))
        clearAction.triggered.connect(self.clearLevel)
        
        levelsMenu = self.menuBar().addMenu(self.tr("&Levels"))
        self.levelsGroup = QActionGroup(self)
        
        for i in range(len(self.levelWidget.levels)):
            levelAction = levelsMenu.addAction(chr(64 + i + 1))
            levelAction.setData(QVariant(i + 1))
            levelAction.setCheckable(True)
            self.levelsGroup.addAction(levelAction)
        
        levelsMenu.triggered.connect(self.selectLevel)
    
        if isinstance(self.repton, Repton2):
        
            dockMenu = self.menuBar().addMenu(self.tr("&Palettes"))
            transportersDockAction = dockMenu.addAction(self.tr("&Transporters"))
            transportersDockAction.setCheckable(True)
            transportersDockAction.setChecked(self.transportersDock.isVisible())
            transportersDockAction.toggled.connect(self.transportersDock.setVisible)
            self.transportersDock.visibilityChanged.connect(transportersDockAction.setChecked)
            
            totalsDockAction = dockMenu.addAction(self.tr("&Totals"))
            totalsDockAction.setCheckable(True)
            totalsDockAction.setChecked(self.totalsDock.isVisible())
            totalsDockAction.toggled.connect(self.totalsDock.setVisible)
            self.totalsDock.visibilityChanged.connect(totalsDockAction.setChecked)
    
    def setCurrentTile(self):
    
        self.levelWidget.currentTile = self.sender().data().toInt()[0]
    
    def selectLevel(self, action):
    
        number = action.data().toInt()[0]
        self.levelWidget.highlight = None
        self.setLevel(number)
    
    def setLevel(self, number):
    
        if isinstance(self.repton, Repton2):
            self.levelWidget.setLevel(number)
        else:
            self.levelWidget.setLevel(number)
        
        # Also change the sprites in the toolbar.
        for action in self.tileGroup.actions():
        
            symbol = action.data().toInt()[0]
            if 32 <= symbol < 74:
                icon = self.puzzleIcon(symbol)
            else:
                icon = QIcon(QPixmap.fromImage(self.levelWidget.tile_images[symbol]))
            action.setIcon(icon)
    
    def clearLevel(self):
    
        answer = QMessageBox.question(self, self.tr("Clear Level"),
            self.tr("Clear the current level?"), QMessageBox.Yes | QMessageBox.No)
        
        if answer == QMessageBox.Yes:
            self.levelWidget.clearLevel()
    
    def goToDestination(self, number, x, y):
    
        self.levelsGroup.actions()[number - 1].trigger()
    
    def updatePuzzleTiles(self, number):
    
        action = self.tileGroup.actions()[number + 33]
        symbol = action.data().toInt()[0]
        action.setIcon(self.puzzleIcon(symbol))
    
    def puzzleIcon(self, symbol):
    
        image = self.levelWidget.tile_images[symbol].convertToFormat(QImage.Format_ARGB32_Premultiplied)
        used = self.levelWidget.piece_numbers.has_key(symbol - 32)
        
        if used:
            painter = QPainter()
            painter.begin(image)
            painter.fillRect(0, 0, image.width(), image.height(), QColor(0,0,0,64))
            painter.end()
        
        return QIcon(QPixmap.fromImage(image))
    
    def sizeHint(self):
    
        levelSize = self.levelWidget.sizeHint()
        menuSize = self.menuBar().sizeHint()
        scrollBarSize = self.centralWidget().verticalScrollBar().size()
        
        return QSize(max(levelSize.width(), menuSize.width(), levelSize.width()),
                     levelSize.height() + menuSize.height() + scrollBarSize.height())


if __name__ == "__main__":

    app = QApplication(sys.argv)
    
    if len(app.arguments()) < 2:
    
        sys.stderr.write("Usage: %s <UEF or SSD file>\n" % app.arguments()[0])
        app.quit()
        sys.exit(1)
    
    file_name = unicode(app.arguments()[1])
    
    try:
        repton = Repton(file_name)
        try_repton2 = False
    except:
        try_repton2 = True
    
    if try_repton2:
        try:
            repton = Repton2(file_name)
        except:
            raise
    
    window = EditorWindow(repton)
    window.show()
    sys.exit(app.exec_())
