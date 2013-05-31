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
import UEFfile

__version__ = "0.1"

class LevelWidget(QWidget):

    def __init__(self, parent = None):
    
        QWidget.__init__(self, parent)
        
        self.xs = 4
        self.ys = 2
        
        self.currentTile = 0
        
        self.setAutoFillBackground(True)
        p = QPalette()
        p.setColor(QPalette.Window, Qt.black)
        self.setPalette(p)
    
    def setTileImages(self, tile_images):
    
        self.tile_images = tile_images
    
    def clearLevel(self):
    
        for row in range(32):
            for column in range(32):
                self.level[row][column] = self.currentTile
        
        self.update()
                
    def setLevel(self, level):
    
        self.level = level
        self.update()
    
    def mousePressEvent(self, event):
    
        if event.button() == Qt.LeftButton:
            self.writeTile(event, self.currentTile)
        elif event.button() == Qt.RightButton:
            self.writeTile(event, 0)
        else:
            event.ignore()
    
    def mouseMoveEvent(self, event):
    
        if event.buttons() & Qt.LeftButton:
            self.writeTile(event, self.currentTile)
        elif event.buttons() & Qt.RightButton:
            self.writeTile(event, 0)
        else:
            event.ignore()
    
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
                tile_image = self.tile_images[tile]
                
                painter.drawImage(c * 8 * self.xs, r * 16 * self.ys,
                                  tile_image)
        
        if r1 <= 4 <= r2 and c1 <= 4 <= c2:
            x1, y1 = 4 * 8 * self.xs, 4 * 16 * self.ys
            x2, y2 = 5 * 8 * self.xs - 1, 5 * 16 * self.ys - 1
            painter.drawLine(x1, y1, x2, y2)
            painter.drawLine(x1, y2, x2, y1)
        
        painter.end()
    
    def sizeHint(self):
    
        return QSize(32 * 8 * self.xs, 32 * 16 * self.ys)
    
    def _row_from_y(self, y):
    
        return y/(16 * self.ys)
    
    def _column_from_x(self, x):
    
        return x/(8 * self.xs)
    
    def _y_from_row(self, r):
    
        return r * 16 * self.ys
    
    def _x_from_column(self, c):
    
        return c * 8 * self.xs
    
    def writeTile(self, event, tile):
    
        r = self._row_from_y(event.y())
        c = self._column_from_x(event.x())
        
        if 0 <= r < 32 and 0 <= c < 32:
        
            self.level[r][c] = tile
            tw = 8 * self.xs
            
            self.update(QRect(self._x_from_column(c), self._y_from_row(r),
                              tw, 16 * self.ys))

class EditorWindow(QMainWindow):

    def __init__(self, repton):
    
        QMainWindow.__init__(self)
        
        self.xs = 4
        self.ys = 2
        self.repton = repton
        self.path = ""
        
        self.level = 1
        self.colours = [(255,0,0), (0,0,255), (255,0,255), (255,0,0),
                        (255,0,0), (0,0,255), (0,255,255), (255,0,0),
                        (0,0,255), (255,0,0), (255,0,255), (0,255,255)]
        
        self.loadImages()
        self.loadLevels()
        
        self.levelWidget = LevelWidget()
        self.levelWidget.setTileImages(self.tile_images)
        
        self.createMenus()
        self.createToolBars()
        
        area = QScrollArea()
        area.setWidget(self.levelWidget)
        self.setCentralWidget(area)
    
    def loadImages(self):
    
        self.tile_images = []
        colour = self.colours[self.level - 1]
        
        palette = map(lambda x: qRgb(*x), [(0,255,0), (255,255,0), colour, (0,0,0)])
        
        for sprite in self.repton.read_sprites():
        
            image = QImage(sprite, 8, 16, QImage.Format_Indexed8).scaled(self.xs * 8, self.ys * 16)
            image.setColorTable(palette)
            self.tile_images.append(image)
    
    def loadLevels(self):
    
        self.levels = self.repton.read_levels()
    
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
        self.repton.write_levels(self.levels)
        
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
        levelsGroup = QActionGroup(self)
        
        for i in range(1, 13):
            levelAction = levelsMenu.addAction(chr(64 + i))
            levelAction.setData(QVariant(i))
            levelAction.setCheckable(True)
            levelsGroup.addAction(levelAction)
        
        levelsMenu.triggered.connect(self.selectLevel)
        levelsGroup.actions()[0].trigger()
    
    def createToolBars(self):
    
        self.tilesToolBar = self.addToolBar(self.tr("Tiles"))
        self.tileGroup = QActionGroup(self)
        
        for symbol in range(32):
        
            icon = QIcon(QPixmap.fromImage(self.tile_images[symbol]))
            action = self.tilesToolBar.addAction(icon, str(symbol))
            action.setCheckable(True)
            self.tileGroup.addAction(action)
            action.triggered.connect(self.setCurrentTile)
        
        # Select the first tile in the tiles toolbar.
        self.tileGroup.actions()[0].trigger()
    
    def setCurrentTile(self):
    
        self.levelWidget.currentTile = int(self.sender().text())
    
    def selectLevel(self, action):
    
        number = action.data().toInt()[0]
        data = self.levels[number - 1]
        
        self.level = number
        self.loadImages()
        self.levelWidget.setTileImages(self.tile_images)
        self.levelWidget.setLevel(data)
    
    def clearLevel(self):
    
        answer = QMessageBox.question(self, self.tr("Clear Level"),
            self.tr("Clear the current level?"), QMessageBox.Yes | QMessageBox.No)
        
        if answer == QMessageBox.Yes:
            self.levelWidget.clearLevel()
    
    def sizeHint(self):
    
        levelSize = self.levelWidget.sizeHint()
        menuSize = self.menuBar().sizeHint()
        scrollBarSize = self.centralWidget().verticalScrollBar().size()
        toolBarSize = self.tilesToolBar.size()
        
        return QSize(max(levelSize.width(), menuSize.width(), toolBarSize.width()),
                     levelSize.height() + menuSize.height() + \
                     scrollBarSize.height() + toolBarSize.height())


if __name__ == "__main__":

    app = QApplication(sys.argv)
    
    if len(app.arguments()) < 2:
    
        sys.stderr.write("Usage: %s <UEF file>\n" % app.arguments()[0])
        app.quit()
        sys.exit(1)
    
    repton = Repton(app.arguments()[1])
    
    window = EditorWindow(repton)
    window.show()
    sys.exit(app.exec_())