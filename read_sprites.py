#!/usr/bin/env python

import os, sys

import Image
import repton

sprite_table = [
    (0x5a0, 0x5a0, 0x5a0, 0x5a0),   # blank
    (0x110, 0x118, 0x120, 0x128),   # diamond
    (0x130, 0x138, 0x140, 0x148),   # boulder
    (0x150, 0x158, 0x160, 0x168),   # egg
    (0x170, 0x178, 0x180, 0x188),   # key
    (0x0f0, 0x0f8, 0x0f0, 0x0f8),   # earth
    (0x0f8, 0x100, 0x0f8, 0x100),   # earth
    (0x108, 0x108, 0x108, 0x108),   # earth
    (0x0d0, 0x0d8, 0x0e0, 0x0e8),   # safe
    (0x050, 0x050, 0x050, 0x050),   # brick wall
    (0x0b0, 0x0b8, 0x0b0, 0x0b8),   # double (top/bottom) wall
    (0x0a0, 0x0a8, 0x0a8, 0x0a8),   # double (left/right) wall
    (0x000, 0x008, 0x000, 0x008),   # quadruple wall
    (0x0c0, 0x0c8, 0x0c0, 0x0c8),   # fancy wall
    (0x098, 0x098, 0x098, 0x098),   # smooth wall
    (0x098, 0x098, 0x078, 0x078),   # lower edged smooth wall
    (0x060, 0x060, 0x098, 0x098),   # upper edged smooth wall
    (0x098, 0x090, 0x098, 0x090),   # right edged smooth wall
    (0x088, 0x098, 0x088, 0x098),   # left edged smooth wall
    (0x098, 0x090, 0x078, 0x080),   # lower right curved smooth wall
    (0x088, 0x098, 0x070, 0x078),   # lower left curved smooth wall
    (0x060, 0x068, 0x098, 0x090),   # upper right curved smooth wall
    (0x058, 0x060, 0x088, 0x098),   # upper left curved smooth wall
    (0x190, 0x198, 0x1a0, 0x1a8),   # map
    (0x050, 0x050, 0x030, 0x030),   # lower edged brick wall
    (0x018, 0x018, 0x050, 0x050),   # upper edged brick wall
    (0x050, 0x048, 0x050, 0x048),   # right edged brick wall
    (0x040, 0x050, 0x040, 0x050),   # left edged brick wall
    (0x050, 0x048, 0x030, 0x038),   # lower right curved brick wall
    (0x040, 0x050, 0x028, 0x030),   # lower left curved brick wall
    (0x018, 0x020, 0x050, 0x048),   # upper right curved brick wall
    (0x010, 0x018, 0x040, 0x050),   # upper left curved brick wall
    ]

class Reader:

    def __init__(self, data):
    
        self.data = data
    
    def read_sprite(self, offset):
    
        rows = []
        
        for i in range(8):
        
            byte = self.data[offset + i]
            rows.append(self.read_columns(byte))
        
        return rows
    
    def read_columns(self, byte):
    
        columns = []
        byte = ord(byte)
        for i in range(4):
        
            v = (byte & 0x01) | ((byte & 0x10) >> 3)
            byte = byte >> 1
            columns.append(v)
        
        columns.reverse()
        return "".join(map(chr, columns))


if __name__ == "__main__":

    if len(sys.argv) != 3:
    
        sys.stderr.write("Usage: %s <Repton UEF file> <output directory>\n" % sys.argv[0])
        sys.exit(1)
    
    uef_file = sys.argv[1]
    output_dir = sys.argv[2]
    
    try:
        r = repton.Repton(uef_file)
    except NotFound:
        sys.stderr.write("Failed to find REPTON2 file in the specified file: %s\n" % uef_file)
        sys.exit(1)
    except IncorrectSize:
        sys.stderr.write("The REPTON2 file was not the expected size.\n")
        sys.exit(1)
    
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    
    data = r.read_sprite_data()
    
    n = 0
    reader = Reader(data)
    
    for offsets in sprite_table:
    
        top_left, top_right, bottom_left, bottom_right = \
            map(reader.read_sprite, offsets)
        
        sprite = []
        for left, right in zip(top_left + bottom_left, top_right + bottom_right):
            sprite.append(left + right)
        
        sprite = "".join(sprite)
        
        im = Image.fromstring("P", (8, 16), sprite)
        im.putpalette((0,255,0, 255,255,0, 255,0,0, 0,0,0))
        im.save(os.path.join(output_dir, "%02i.png" % n))
        
        n += 1
    
    sys.exit()
