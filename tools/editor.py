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

    def __init__(self, tw, th, parent = None):
    
        QWidget.__init__(self, parent)
        
        self.xs = 2
        self.ys = 1
        self.tw = tw
        self.th = th
        
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
                
                painter.drawImage(c * self.tw * self.xs, r * self.th * self.ys,
                                  tile_image)
        
        if r1 <= 4 <= r2 and c1 <= 4 <= c2:
            x1, y1 = 4 * self.tw * self.xs, 4 * self.th * self.ys
            x2, y2 = 5 * self.tw * self.xs - 1, 5 * self.th * self.ys - 1
            painter.drawLine(x1, y1, x2, y2)
            painter.drawLine(x1, y2, x2, y1)
        
        painter.end()
    
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
    
    def writeTile(self, event, tile):
    
        r = self._row_from_y(event.y())
        c = self._column_from_x(event.x())
        
        if 0 <= r < 32 and 0 <= c < 32:
        
            self.level[r][c] = tile
            tw = self.tw * self.xs
            
            self.update(QRect(self._x_from_column(c), self._y_from_row(r),
                              tw, self.th * self.ys))

class EditorWindow(QMainWindow):

    def __init__(self, repton):
    
        QMainWindow.__init__(self)
        
        self.xs = 2
        self.ys = 1
        self.tw = repton.tile_width
        self.th = repton.tile_height
        
        self.repton = repton
        self.path = ""
        
        self.level = 1
        
        self.loadImages()
        self.loadLevels()
        
        self.levelWidget = LevelWidget(self.tw, self.th)
        self.levelWidget.setTileImages(self.tile_images)
        
        self.createMenus()
        self.createToolBars()
        
        # Select the first tile in the tiles toolbar and the first level in the
        # levels menu.
        self.tileGroup.actions()[0].trigger()
        self.levelsGroup.actions()[0].trigger()
        
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
        self.levelsGroup = QActionGroup(self)
        
        for i in range(1, 17):
            levelAction = levelsMenu.addAction(chr(64 + i))
            levelAction.setData(QVariant(i))
            levelAction.setCheckable(True)
            self.levelsGroup.addAction(levelAction)
        
        levelsMenu.triggered.connect(self.selectLevel)
    
    def createToolBars(self):
    
        self.tilesToolBar = self.addToolBar(self.tr("Tiles"))
        self.tileGroup = QActionGroup(self)
        
        for symbol in range(32):
        
            icon = QIcon(QPixmap.fromImage(self.tile_images[symbol]))
            action = self.tilesToolBar.addAction(icon, str(symbol))
            action.setData(QVariant(symbol))
            action.setCheckable(True)
            self.tileGroup.addAction(action)
            action.triggered.connect(self.setCurrentTile)
    
    def setCurrentTile(self):
    
        self.levelWidget.currentTile = self.sender().data().toInt()[0]
    
    def selectLevel(self, action):
    
        number = action.data().toInt()[0]
        data = self.levels[number - 1]
        
        self.level = number
        self.loadImages()
        self.levelWidget.setTileImages(self.tile_images)
        self.levelWidget.setLevel(data)
        
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
