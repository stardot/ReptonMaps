#!/usr/bin/env python

"""
Copyright (C) 2012 David Boddie <david@boddie.org.uk>

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

class LevelWidget(QWidget):

    def __init__(self, tile_images, parent = None):
    
        QWidget.__init__(self, parent)
        
        self.xs = 4
        self.ys = 2
        
        self.clearLevel()
        
        self.tile_images = tile_images
        self.currentTile = 0
        
        self.setAutoFillBackground(True)
        p = QPalette()
        p.setColor(QPalette.Window, Qt.black)
        self.setPalette(p)
    
    def clearLevel(self):
    
        self.level = []
        
        for row in range(32):
            self.level.append([])
            for column in range(32):
                self.level[-1].append(0)
                
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
        self.loadImages()
        
        self.levelWidget = LevelWidget(self.tile_images)
        
        self.createMenus()
        self.createToolBars()
        
        area = QScrollArea()
        area.setWidget(self.levelWidget)
        self.setCentralWidget(area)
    
    def loadImages(self):
    
        # Find the images.
        self.tile_images = []
        palette = map(lambda x: qRgb(*x), [(0,255,0), (255,255,0), (255,0,0), (0,0,0)])
        
        for sprite in self.repton.read_sprites():
        
            image = QImage(sprite, 8, 16, QImage.Format_Indexed8).scaled(self.xs * 8, self.ys * 16)
            image.setColorTable(palette)
            self.tile_images.append(image)
    
    def createMenus(self):
    
        fileMenu = self.menuBar().addMenu(self.tr("&File"))
        
        newAction = fileMenu.addAction(self.tr("&New"))
        newAction.setShortcut(QKeySequence.New)
        
        quitAction = fileMenu.addAction(self.tr("E&xit"))
        quitAction.setShortcut(self.tr("Ctrl+Q"))
        quitAction.triggered.connect(self.close)
        
        levelsMenu = self.menuBar().addMenu(self.tr("&Levels"))
        levelsGroup = QActionGroup(self)
        
        for i in range(1, 13):
            levelAction = levelsMenu.addAction(self.tr("%1").arg(i))
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
        data = self.repton.read_level(number)
        self.levelWidget.setLevel(data)
    
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
