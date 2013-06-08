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

class TooManyAreas(Exception):
    pass

class Repton2:

    tile_width = 12
    tile_height = 24
    
    wall_colours = [(0,0,255), (255,0,0), (0,255,255), (0,0,255),
                    (255,0,255), (0,0,255), (0,255,255), (0,0,255),
                    (255,0,255), (0,0,255), (0,255,255), (255,0,0),
                    (255,0,255), (0,0,255), (0,255,255), (255,0,0)]
    
    repton_colours = [(0,255,0), (0,255,0), (0,255,0), (0,255,0),
                      (0,255,0), (0,255,0), (0,255,0), (0,255,0),
                      (0,255,0), (0,255,0), (0,255,0), (0,255,255),
                      (0,255,0), (0,255,0), (0,255,0), (0,255,255)]
    
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
        
        # Initialise dictionaries for each screen.
        for screen in range(16):
            transporters[screen] = {}
            destinations[screen] = {}
        
        i = transporters_address
        while i < 0x1fd0:
        
            src_screen, src_x, src_y = map(ord, self.data[i:i+3])
            dest_screen, dest_x, dest_y = map(ord, self.data[i+3:i+6])
            
            transporters[src_screen][(src_x, src_y)] = \
                dest_screen, (dest_x, dest_y)
            destinations[dest_screen].setdefault((dest_x, dest_y), set()).add((src_screen, (src_x, src_y)))
            
            i += 6
        
        return transporters, destinations
    
    def read_puzzle_defs(self):
    
        puzzle_address = 0x1da0
        pieces = {}
        piece_numbers = {}
        self.piece_destinations = {}
        
        # Initialise dictionaries for each screen.
        for screen in range(16):
            pieces[screen] = {}
        
        # Give the puzzle pieces numbers from 0 to 41.
        number = 0
        
        i = puzzle_address
        while i < 0x1e48:
        
            screen, x, y, destination = map(ord, self.data[i:i+4])
            pieces[screen][(x, y)] = (number, destination)
            piece_numbers[number] = (screen, (x, y))
            self.piece_destinations[number] = destination
            
            number += 1
            i += 4
        
        return pieces, piece_numbers
    
    def palette(self, level):
    
        wall_colour = self.wall_colours[level - 1]
        repton_colour = self.repton_colours[level - 1]
        return [(0,0,0), wall_colour, (255,255,0), repton_colour]
    
    def write_levels(self, levels, transporters, puzzle_pieces):
    
        data = self.uef.contents[self.file_number]["data"][:0x1da0]
        
        pieces = {}
        
        for screen, defs in puzzle_pieces.items():
        
            for (x, y), (number, destination) in defs.items():
            
                # Remember that we gave these pieces tile numbers from 32.
                pieces[number] = (screen, x, y, self.piece_destinations[number])
        
        for i in range(42):
            try:
                data += "".join(map(chr, pieces[i]))
            except KeyError:
                # Use a placeholder piece.
                data += "\x00\x00\x00\x00"
        
        data += "\x6b\x00\x00\x00\x00\x00\x00\x00"
        
        for screen, defs in transporters.items():
        
            for (x, y), (dest_screen, (dest_x, dest_y)) in defs.items():
            
                data += "".join(map(chr, (screen, x, y, dest_screen, dest_x, dest_y)))
        
        data += (0x2000 - len(data))*"\x00"
        
        # Level area definitions
        
        # Find filled areas.
        area_dict = {}
        areas = []
        
        a = 0
        for level in levels:
        
            for row in range(0, 32, 8):
                area = tuple(reduce(list.__add__, level[row:row+8]))
                
                # Reference existing areas if possible.
                try:
                    areas.append(area_dict[area])
                    continue
                except KeyError:
                    pass
                
                # Determine if the area is completely filled with one tile type.
                first_tile = area[0]
                for tile in area:
                    if tile != first_tile:
                        area_dict[area] = a
                        areas.append(a)
                        a += 1
                        break
                else:
                    # Reference special tile-filled areas.
                    areas.append(0x80 | first_tile)
        
        if a > 0x30:
            print map(hex, areas)
            raise TooManyAreas
        
        data += "".join(map(chr, areas))
        
        # Text character definitions
        data += self.uef.contents[self.file_number]["data"][0x2040:0x2340]
        
        # Sprite definitions
        data += self.uef.contents[self.file_number]["data"][0x2340:0x2e00]
        
        # Level definitions
        next = 0
        
        for a in range(len(areas)):
        
            if a % 4 == 0:
                level = levels[a/4]
            
            area = areas[a]
            
            # If the area is a special area or refers to one that has already
            # occurred then do not write its data to the file.
            if area & 0x80 != 0 or area < next:
                continue
            
            next = area + 1
            start_row = (a % 4) * 8
            
            for row in range(start_row, start_row + 8):
            
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
