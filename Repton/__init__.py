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

from sprites import Reader, BBCReader

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
            
                if details["name"] == "REPTON2":
                    break
                
                self.file_number += 1
            else:
                raise NotFound
            
            self.data = details["data"]
            
            if len(self.data) != 0x4a00:
                raise IncorrectSize
            
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
            
                if details.name == "D.REPTON2":
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
                        data += chr(current & 0xff)
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
    
        # Write the new UEF file.
        u = UEFfile.UEFfile(creator = 'Repton Editor ' + version)
        u.minor = 6
        u.target_machine = "Electron"
        
        # Update the level data.
        self.uef.contents[self.file_number]["data"] = self.data
        
        files = map(lambda x: (x["name"], x["load"], x["exec"], x["data"]),
                    self.uef.contents)
        
        u.import_files(0, files, gap = True)
        
        try:
            u.write(path, write_emulator_info = False)
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
            open(path, "w").write(disk.file.read())
            return True
        except IOError:
            return False
