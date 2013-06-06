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

import os, sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from Repton import Repton
from Repton2 import Repton2
import UEFfile

__version__ = "0.1"

class LevelWidget(QWidget):

    destinationRequested = pyqtSignal(int, int, int)
    
    def __init__(self, repton, parent = None):
    
        QWidget.__init__(self, parent)
        
        self.repton = repton
        
        self.tw = repton.tile_width
        self.th = repton.tile_height
        
        if isinstance(repton, Repton):
            self.xs = 4
            self.ys = 2
        
        elif isinstance(repton, Repton2):
            self.xs = 2
            self.ys = 1
        
        self.highlight = None
        
        self.level_number = 1
        self.currentTile = 0
        
        self.setAutoFillBackground(True)
        p = QPalette()
        p.setColor(QPalette.Window, Qt.black)
        self.setPalette(p)
        
        self.setMouseTracking(True)
    
    def setTileImages(self, tile_images):
    
        self.tile_images = tile_images
    
    def clearLevel(self):
    
        for row in range(32):
            for column in range(32):
                self.level[row][column] = self.currentTile
        
        self.update()
                
    def setLevel(self, number, level, transporters = {}, destinations = {},
                       puzzle = {}, piece_numbers = {}):
    
        self.level_number = number
        self.level = level
        self.transporters = transporters
        self.destinations = destinations
        self.puzzle = puzzle
        self.piece_numbers = piece_numbers
        
        if isinstance(self.repton, Repton):
            self.highlight = (4, 4)
        
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
        
        painter.setPen(Qt.white)
        
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
            
                tile = self.level[r][c]
                
                if isinstance(self.repton, Repton2):
                    if tile == 2:
                        tile = self.getTransporterOrPuzzleTile(r, c)
                    elif tile == 9:
                        tile = self.getFinishOrSpiritTile(r, c)
                
                tile_image = self.tile_images[tile]
                
                painter.drawImage(c * self.tw * self.xs, r * self.th * self.ys,
                                  tile_image)
        
        if self.highlight:
            x1 = self.highlight[0] * self.tw * self.xs
            y1 = self.highlight[1] * self.th * self.ys
            w = (self.tw * self.xs) - 1
            h = (self.th * self.ys) - 1
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
        
        elif (c, r) in self.destinations[self.level_number - 1]:
            screen, (x, y) = self.destinations[self.level_number - 1][(c, r)]

            menu = QMenu(self.tr("Destination"))
            goAction = menu.addAction(self.tr("Go to transporter"))
        
        else:
            event.ignore()
            return
        
        if menu.exec_(event.globalPos()) == goAction:
            self.destinationRequested.emit(screen + 1, x, y)
            self.highlight = (x, y)
    
    def updateCursor(self, event):
    
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
    
    def writeTile(self, c, r, tile):
    
        if not (0 <= r < 32 and 0 <= c < 32):
            return
        
        # Do not allow spirits to be used on Screen A.
        if tile == 75 and self.level_number == 1:
            return
        
        previous = self.level[r][c]
        
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
                del self.destinations[dest_screen][(x, y)]
            
            elif 32 <= actual_previous < 74:
            
                # The puzzle piece at this location is removed.
                number, destination = self.puzzle[self.level_number - 1][(c, r)]
                del self.puzzle[self.level_number - 1][(c, r)]
                del self.piece_numbers[number]
        
        if tile == 11:
        
            # Create a new transporter entry. The new transporter's
            # destination is its own location.
            self.transporters[self.level_number - 1][(c, r)] = (self.level_number - 1, (c, r))
            self.destinations[self.level_number - 1][(c, r)] = (self.level_number - 1, (c, r))
            
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
                
                del self.puzzle[old_screen][(old_x, old_y)]
            except KeyError:
                pass
            
            self.puzzle[self.level_number - 1][(c, r)] = (number, 0)
            self.piece_numbers[number] = (self.level_number - 1, (c, r))
            
            # Insert tile 2 instead.
            tile = 2
        
        self.level[r][c] = tile
        tw = self.tw * self.xs
        
        self.update(QRect(self._x_from_column(c), self._y_from_row(r),
                          tw, self.th * self.ys))

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
        self.transporters, self.destinations = repton.read_transporter_defs()
        self.puzzle, self.piece_numbers = repton.read_puzzle_defs()
        
        self.path = ""
        self.level = 1
        
        self.levelWidget = LevelWidget(repton)
        self.levelWidget.destinationRequested.connect(self.goToDestination)
        
        self.loadImages()
        self.loadLevels()
        
        self.createMenus()
        self.createToolBars()
        
        # Select the first tile in the tiles toolbar and the first level in the
        # levels menu.
        self.tileGroup.actions()[0].trigger()
        self.levelsGroup.actions()[0].trigger()
        self.levelWidget.highlight = (16, 7)
        
        area = QScrollArea()
        area.setWidget(self.levelWidget)
        self.setCentralWidget(area)
    
    def loadImages(self):
    
        self.tile_images = []
        
        palette = map(lambda x: qRgb(*x), self.repton.palette(self.level))
        
        for sprite in self.repton.read_sprites():
        
            image = QImage(sprite, self.tw, self.th, QImage.Format_Indexed8).scaled(self.xs * self.tw, self.ys * self.th)
            image.setColorTable(palette)
            self.tile_images.append(image)
    
    def loadLevels(self):
    
        self.levels = self.repton.read_levels()
        
        if isinstance(self.repton, Repton2):
        
            self.transporters, self.destinations = repton.read_transporter_defs()
            self.puzzle, self.piece_numbers = repton.read_puzzle_defs()
    
    def saveAs(self):
    
        path = QFileDialog.getSaveFileName(self, self.tr("Save As"),
                                           self.path, self.tr("UEF files (*.uef)"))
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
            self.repton.write_levels(self.levels)
        elif isinstance(self.repton, Repton2):
            self.repton.write_levels(self.levels, self.transporters, self.puzzle)
        else:
            return
        
        # Write the new UEF file.
        u = UEFfile.UEFfile(creator = 'Repton Editor ' + __version__)
        u.minor = 6
        u.target_machine = "Electron"
        
        files = map(lambda x: (x["name"], x["load"], x["exec"], x["data"]),
                    self.repton.uef.contents)
        
        u.import_files(0, files, gap = True)
        
        try:
            u.write(path, write_emulator_info = False)
            return True
        except UEFfile.UEFfile_error:
            return False
    
    def createMenus(self):
    
        fileMenu = self.menuBar().addMenu(self.tr("&File"))
        
        newAction = fileMenu.addAction(self.tr("&New"))
        newAction.setShortcut(QKeySequence.New)
        
        saveAsAction = fileMenu.addAction(self.tr("Save &As..."))
        saveAsAction.setShortcut(QKeySequence.SaveAs)
        saveAsAction.triggered.connect(self.saveAs)
        
        quitAction = fileMenu.addAction(self.tr("E&xit"))
        quitAction.setShortcut(self.tr("Ctrl+Q"))
        quitAction.triggered.connect(self.close)
        
        editMenu = self.menuBar().addMenu(self.tr("&Edit"))
        clearAction = editMenu.addAction(self.tr("&Clear"))
        clearAction.triggered.connect(self.clearLevel)
        
        levelsMenu = self.menuBar().addMenu(self.tr("&Levels"))
        self.levelsGroup = QActionGroup(self)
        
        for i in range(len(self.levels)):
            levelAction = levelsMenu.addAction(chr(64 + i + 1))
            levelAction.setData(QVariant(i + 1))
            levelAction.setCheckable(True)
            self.levelsGroup.addAction(levelAction)
        
        levelsMenu.triggered.connect(self.selectLevel)
    
    def createToolBars(self):
    
        self.tileGroup = QActionGroup(self)
        
        # 32 tiles + 42 puzzle pieces + 1 spirit = 75
        
        for symbols in [range(0, 32) + [74], range(32, 74)]:
        
            tilesToolBar = self.addToolBar(self.tr("Tiles"))
            
            for symbol in symbols:
            
                icon = QIcon(QPixmap.fromImage(self.tile_images[symbol]))
                action = tilesToolBar.addAction(icon, str(symbol))
                action.setData(QVariant(symbol))
                action.setCheckable(True)
                self.tileGroup.addAction(action)
                action.triggered.connect(self.setCurrentTile)
    
    def setCurrentTile(self):
    
        self.levelWidget.currentTile = self.sender().data().toInt()[0]
    
    def selectLevel(self, action):
    
        number = action.data().toInt()[0]
        self.levelWidget.highlight = None
        self.setLevel(number)
    
    def setLevel(self, number):
    
        data = self.levels[number - 1]
        self.level = number
        self.loadImages()
        self.levelWidget.setTileImages(self.tile_images)
        
        if isinstance(self.repton, Repton2):
            self.levelWidget.setLevel(number, data, self.transporters,
                                      self.destinations, self.puzzle,
                                      self.piece_numbers)
        else:
            self.levelWidget.setLevel(number, data)
        
        # Also change the sprites in the toolbar.
        for action in self.tileGroup.actions():
        
            symbol = action.data().toInt()[0]
            icon = QIcon(QPixmap.fromImage(self.tile_images[symbol]))
            action.setIcon(icon)
    
    def clearLevel(self):
    
        answer = QMessageBox.question(self, self.tr("Clear Level"),
            self.tr("Clear the current level?"), QMessageBox.Yes | QMessageBox.No)
        
        if answer == QMessageBox.Yes:
            self.levelWidget.clearLevel()
    
    def goToDestination(self, number, x, y):
    
        self.levelsGroup.actions()[number - 1].trigger()
    
    def sizeHint(self):
    
        levelSize = self.levelWidget.sizeHint()
        menuSize = self.menuBar().sizeHint()
        scrollBarSize = self.centralWidget().verticalScrollBar().size()
        
        return QSize(max(levelSize.width(), menuSize.width(), levelSize.width()),
                     levelSize.height() + menuSize.height() + scrollBarSize.height())


if __name__ == "__main__":

    app = QApplication(sys.argv)
    
    if len(app.arguments()) < 2:
    
        sys.stderr.write("Usage: %s <UEF file>\n" % app.arguments()[0])
        app.quit()
        sys.exit(1)
    
    try:
        repton = Repton(app.arguments()[1])
        try_repton2 = False
    except:
        try_repton2 = True
    
    if try_repton2:
        try:
            repton = Repton2(app.arguments()[1])
        except:
            raise
    
    window = EditorWindow(repton)
    window.show()
    sys.exit(app.exec_())
