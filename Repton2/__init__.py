"""
__init__.py - The main Repton2 Python package file.

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

from sprites import Reader

class NotFound(Exception):
    pass

class IncorrectSize(Exception):
    pass

class Repton2:

    tile_width = 12
    tile_height = 24
    
    colours = [(0,0,255), (255,0,0), (0,255,255), (0,0,255),
               (255,0,255), (0,0,255), (0,255,255), (0,0,255),
               (255,0,255), (0,0,255), (0,255,255), (0,0,255),
               (255,0,255), (0,0,255), (0,255,255), (0,255,255)]
    
    def __init__(self, uef_file):
    
        self.uef = UEFfile.UEFfile(uef_file)
        self.file_number = 0
        
        for details in self.uef.contents:

            if details["name"] == "REPTONB":
                break
            
            self.file_number += 1
        else:
            raise NotFound
        
        self.data = details["data"]
        
        if len(self.data) != 0x4c00:
            raise IncorrectSize
    
    def read_levels(self):
    
        levels = []
        
        for number in range(16):
        
            level = []
            
            offsets_address = 0x2000 + (number * 4)
            
            for offset in range(4):
            
                offset = ord(self.data[offsets_address + offset])
                
                if offset & 0x80:
                
                    for row in range(8):
                        level.append([offset & 0x1f]*32)
                
                else:
                    address = 0x2e00 + (offset * 160)
                    
                    for row in range(8):
                    
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
    
    def read_sprites(self):
    
        reader = Reader(self.data[0x2340:0x2e00])
        
        sprite_defs_address = 0x1b00
        puzzle_sprite_defs_address = 0x1c20
        
        sprites = self._read_sprites(reader, sprite_defs_address, 32)
        sprites += self._read_sprites(reader, puzzle_sprite_defs_address, 42)
        
        # Define the spirit sprite separately.
        sprites += [self._read_sprite(reader, [0x300, 0x300, 0x300,
                                              0x300, 0x000, 0x300,
                                              0x300, 0x300, 0x300])]
        
        return sprites
    
    def _read_sprites(self, reader, sprite_defs_address, number):
    
        sprites = []
        
        for n in range(number):
        
            addr = sprite_defs_address + (n * 9)
            offsets = map(lambda x: ord(x) * 0x08, self.data[addr:addr + 9])
            
            sprite = self._read_sprite(reader, offsets)
            sprites.append(sprite)
            
            n += 1
        
        return sprites
    
    def _read_sprite(self, reader, offsets):
    
        pieces = map(reader.read_sprite, offsets)
        
        sprite = []
        for i in range(0, 9, 3):
            for left, middle, right in zip(*pieces[i:i+3]):
                sprite.append(left + middle + right)
        
        return "".join(sprite)
    
    def read_transporter_defs(self):
    
        transporters_address = 0x1e50
        transporters = {}
        destinations = {}
        
        i = transporters_address
        while i < 0x1fd0:
        
            src_screen, src_x, src_y = map(ord, self.data[i:i+3])
            dest_screen, dest_x, dest_y = map(ord, self.data[i+3:i+6])
            
            transporters.setdefault(src_screen, {})[(src_x, src_y)] = \
                dest_screen, (dest_x, dest_y)
            destinations.setdefault(dest_screen, {})[(dest_x, dest_y)] = \
                src_screen, (src_x, src_y)
            
            i += 6
        
        return transporters, destinations
    
    def read_puzzle_defs(self):
    
        puzzle_address = 0x1da0
        pieces = {}
        
        # Define the puzzle pieces as tiles 32 to 73.
        number = 32
        
        i = puzzle_address
        while i < 0x1e48:
        
            screen, x, y, destination = map(ord, self.data[i:i+4])
            pieces.setdefault(screen, {})[(x, y)] = (number, destination)
            
            number += 1
            i += 4
        
        return pieces
    
    def palette(self, level):
    
        wall_colour = self.colours[level - 1]
        return [(0,0,0), wall_colour, (255,255,0), (0,255,0)]
    
    def write_levels(self, levels):
    
        data = self.uef.contents[self.file_number]["data"][:0x2e00]
        
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
