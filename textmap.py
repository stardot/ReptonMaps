#!/usr/bin/env python

import sys
import UEFfile

chars = {
    0: " ", 1: "+",         # space, diamond
    2: "O", 3: "0",         # boulder, egg
    4: "K",                 # key
    5: "x", 6: ".", 7: ",", # earth
    8: "S",                 # safe
    9: "#",                 # brick wall
    10: "%", 11: 'H',       # double (top/bottom) wall, double (left/right) wall
    12: "&", 13: "@",       # quadruple wall, fancy wall
    14: "X",                # smooth wall
    15: "_", 16: "^",   # lower and upper edged smooth walls
    17: "|", 18: "|",   # right and left edged smooth walls
    19: "/", 20: "\\",  # lower curved smooth walls
    21: "\\", 22: "/",  # upper curved smooth walls
    23: "M",            # map
    24: "_", 25: "^",   # lower and upper edged brick walls
    26: "|", 27: "|",   # right and left edged brick walls
    28: "/", 29: "\\",  # lower curved brick walls
    30: "\\", 31: "/"   # upper curved brick walls
    }


if __name__ == "__main__":

    if len(sys.argv) != 3:
    
        sys.stderr.write("Usage: %s <Repton UEF file> <level number>\n" % sys.argv[0])
        sys.exit(1)
    
    uef_file = sys.argv[1]
    
    try:
        level = int(sys.argv[2])
        if not 1 <= level <= 12:
            raise ValueError
    
    except ValueError:
        sys.stderr.write("The level number must be an integer from 1 to 12.\n")
        sys.exit(1)
    
    u = UEFfile.UEFfile(uef_file)
    
    for details in u.contents:
    
        if details["name"] == "REPTON2":
            break
    else:
        sys.stderr.write("Failed to find REPTON2 file in the specified file: %s\n" % uef_file)
        sys.exit(1)
    
    data = details["data"]
    
    if len(data) != 0x4a00:
        sys.stderr.write("The REPTON2 file was not the expected size.\n")
        sys.exit(1)
    
    address = 0x2c00 + ((level - 1) * 640)
    
    for row in range(32):
    
        current = 0
        offset = 0
        
        for column in range(32):

            if offset < 5:
                current = current | (ord(data[address]) << offset)
                address += 1
                offset += 8
            
            if offset >= 5:
                value = current & 0x1f
                current = current >> 5
                offset -= 5
                try:
                    char = chars[value]
                    sys.stdout.write(char)
                except KeyError:
                    if value < 10:
                        sys.stdout.write(chr(ord("0") + value))
                    else:
                        sys.stdout.write(chr(ord("a") + value - 10))
        
        print
    
    sys.exit()
