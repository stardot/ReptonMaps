"""
__init__.py - The main Repton Python package file.

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

__all__ = ["sprites"]

import UEFfile

from sprites import Reader, sprite_table

class NotFound(Exception):
    pass

class IncorrectSize(Exception):
    pass

class Repton:

    tile_width = 8
    tile_height = 16
    
    colours = [(255,0,0), (0,0,255), (255,0,255), (255,0,0),
               (255,0,0), (0,0,255), (0,255,255), (255,0,0),
               (0,0,255), (255,0,0), (255,0,255), (0,255,255)]
    
    def __init__(self, uef_file):
    
        self.uef = UEFfile.UEFfile(uef_file)
        self.file_number = 0
        
        for details in self.uef.contents:

            if details["name"] == "REPTON2":
                break
            
            self.file_number += 1
        else:
            raise NotFound
        
        self.data = details["data"]
        
        if len(self.data) != 0x4a00:
            raise IncorrectSize
    
    def read_levels(self):
    
        levels = []
        
        for number in range(12):
        
            address = 0x2c00 + (number * 640)
            level = []
    
            for row in range(32):
    
                current = 0
                offset = 0
                level.append([])
    
                for column in range(32):
    
                    if offset < 5:
                        ch = self.data[address]
                        current = current | (ord(ch) << offset)
                        address += 1
                        offset += 8
    
                    if offset >= 5:
                        value = current & 0x1f
                        current = current >> 5
                        offset -= 5
                        level[-1].append(value)
            
            levels.append(level)
        
        return levels
    
    def write_levels(self, levels):
    
        data = self.uef.contents[self.file_number]["data"][:0x2c00]
        
        for number in range(len(levels)):
        
            level = levels[number]
            
            for row in range(32):
            
                current = 0
                offset = 0
                
                for column in range(32):
                
                    if offset < 8:
                        current = current | (level[row][column] << offset)
                        offset += 5
                    
                    if offset >= 8:
                        data += chr(current & 0xff)
                        current = current >> 8
                        offset -= 8
        
        self.uef.contents[self.file_number]["data"] = data
    
    def read_sprites(self):
    
        reader = Reader(self.data[0x2500:0x2c00])
        
        sprites = []
        n = 0
        
        for offsets in sprite_table:
        
            top_left, top_right, bottom_left, bottom_right = \
                map(reader.read_sprite, offsets)
            
            sprite = []
            for left, right in zip(top_left + bottom_left, top_right + bottom_right):
                sprite.append(left + right)
            
            sprite = "".join(sprite)
            sprites.append(sprite)
            
            n += 1
        
        return sprites
    
    def palette(self, level):
    
        colour = self.colours[level - 1]
        return [(0,255,0), (255,255,0), colour, (0,0,0)]
