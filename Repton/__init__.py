__all__ = ["sprites"]

import UEFfile

from sprites import Reader, sprite_table

class NotFound(Exception):
    pass

class IncorrectSize(Exception):
    pass

class Repton:

    def __init__(self, uef_file):
    
        self.u = UEFfile.UEFfile(uef_file)
        
        for details in self.u.contents:

            if details["name"] == "REPTON2":
                break
        else:
            raise NotFound
        
        self.data = details["data"]
        
        if len(self.data) != 0x4a00:
            raise IncorrectSize
    
    def read_level(self, number):
    
        address = 0x2c00 + ((number - 1) * 640)
        
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
        
        return level
    
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
