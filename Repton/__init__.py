__all__ = ["sprites"]

import UEFfile

from sprites import Reader, sprite_table

class NotFound(Exception):
    pass

class IncorrectSize(Exception):
    pass

class Repton:

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
