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
import makedfs

from Repton.sprites import Reader, BBCReader

class NotFound(Exception):
    pass

class IncorrectSize(Exception):
    pass

class Repton:

    colours = [(255,0,0), (0,0,255), (255,0,255), (255,0,0),
               (255,0,0), (0,0,255), (0,255,255), (255,0,0),
               (0,0,255), (255,0,0), (255,0,255), (0,255,255)]
    
    def __init__(self, uef_or_ssd_file):
    
        if uef_or_ssd_file.endswith("uef"):
        
            # Acorn Electron version
            
            self.uef = UEFfile.UEFfile(uef_or_ssd_file)
            self.file_number = 0
            
            for details in self.uef.contents:
            
                if details["name"] == b"REPTON2":
                    break
                
                self.file_number += 1
            else:
                raise NotFound
            
            self.data = details["data"]
            
            if len(self.data) != 0x4a00:
                raise IncorrectSize
            
            # Certain releases of Repton contain scrambled data. Unscramble it
            # using a reversible scrambling routine.
            if len(self.uef.contents) == 4:
                self.data = self.scramble(self.data)
            
            self.levels_start = 0x2c00
            self.sprites_start = 0x2500
            self.sprites_finish = 0x2c00
            
            self.version = "Electron"
            self.Reader = Reader
            
            self.tile_width = 8
            self.tile_height = 16
        
        elif uef_or_ssd_file.endswith("ssd"):
        
            # BBC Micro DFS disk version
            
            self.ssd = makedfs.Disk()
            self.ssd.open(open(uef_or_ssd_file))
            self.file_number = 0
            
            cat = self.ssd.catalogue()
            title, files = cat.read()
            
            for details in files:
            
                if details.name == b"D.REPTON2":
                    break
                
                self.file_number += 1
            else:
                raise NotFound
            
            self.data = details.data
            
            if len(self.data) != 0x5600:
                raise IncorrectSize
            
            self.levels_start = 0x3800
            self.sprites_start = 0x25c0
            self.sprites_finish = 0x3600
            
            self.version = "BBC"
            self.Reader = BBCReader
            
            self.tile_width = 16
            self.tile_height = 32
        
        else:
            raise NotFound
    
    def scramble(self, data):
    
        # Keep the first byte.
        s = data[:1]
        
        d = []
        v = 0xe0
        o = [0x05, 0x04, 0x07, 0x06, 0x01, 0x00, 0x03, 0x02,
             0x0d, 0x0c, 0x0f, 0x0e, 0x09, 0x08, 0x0b, 0x0a,
             0x15, 0x14, 0x17, 0x16, 0x11, 0x10, 0x13, 0x12,
             0x1d, 0x1c, 0x1f, 0x1e, 0x19, 0x18, 0x1b, 0x1a]
        i = 0
        while i < len(data):
        
            b = data[i:i+32]
            j = 0
            while j < 32:
                d.append(b[j] ^ (v + o[j]))
                j += 1
            
            if v == 0:
                v = 0xe0
            else:
                v -= 32
            
            i += 32
        
        return s + bytes(d[1:])
    
    def read_levels(self):
    
        levels = []
        
        for number in range(12):
        
            address = self.levels_start + (number * 640)
            level = []
    
            for row in range(32):
    
                current = 0
                offset = 0
                level.append([])
    
                for column in range(32):
    
                    if offset < 5:
                        ch = self.data[address]
                        current = current | (ch << offset)
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
    
        data = self.data[:self.levels_start]
        
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
                        data += bytes([current & 0xff])
                        current = current >> 8
                        offset -= 8
        
        self.data = data
    
    def read_sprites(self):
    
        reader = self.Reader(self.data[self.sprites_start:self.sprites_finish])
        
        sprites = []
        
        for offsets in reader.sprite_table:
            sprites.append(reader.read_sprite(offsets))
        
        return sprites
    
    def palette(self, level):
    
        colour = self.colours[level - 1]
        return [(0,255,0), (255,255,0), colour, (0,0,0)]
    
    def saveUEF(self, path, version):
    
        # Update the UEF file and save it to the specified location.
        
        # Scramble the data if necessary.
        if len(self.uef.contents) == 4:
            self.data = self.scramble(self.data)
        
        last_file = self.uef.contents[-1]
        last_index = len(self.uef.contents) - 1
        
        self.uef.remove_files([last_index])
        
        # Add the last file again with the updated level data.
        info = (last_file["name"], last_file["load"], last_file["exec"], self.data)
        self.uef.import_files(last_index, info)
        
        try:
            self.uef.write(path, write_emulator_info = False)
            return True
        except UEFfile.UEFfile_error:
            return False
    
    def saveSSD(self, path):
    
        # Write the new SSD file.
        disk = makedfs.Disk()
        disk.new()
        catalogue = disk.catalogue()
        catalogue.boot_option = 3
        
        title, files = self.ssd.catalogue().read()
        
        # Update the level data.
        files[self.file_number].data = self.data
        
        # Fix copy protection length problem.
        for file in files:
            file.length = len(file.data)
        
        catalogue.write(title, files)
        disk.file.seek(0, 0)
        
        try:
            open(path, "wb").write(disk.file.read())
            return True
        except IOError:
            return False
