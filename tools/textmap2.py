#!/usr/bin/env python

"""
textmap2.py - A tool for exporting the levels from Repton 2 as text.

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

import sys
from Repton2 import IncorrectSize, NotFound, Repton2

chars = {
    0: " ",                 # space
    1: ".",                 # space (transporter destination)
    2: "T",                 # transporter/puzzle piece
    3: "'",                 # earth (cross)
    4: ",",                 # earth (top-right, bottom-left)
    5: ".",                 # earth (bottom-left, top-right)
    6: "+",                 # diamond
    7: "K",                 # key
    8: "S",                 # skull
    9: "F",                 # finishing piece/spirit
    10: "s",                # status piece
    11: '?',                # transporter (sprite, but not used in level data)
    12: "C",                # cage
    13: "$",                # safe
    14: "O",                # boulder
    15: "0",                # egg
    16: "\\",               # upper right curved brick wall
    17: "/",                # upper left curved brick wall
    18: "\\",               # lower left curved brick wall
    19: "/",                # lower right curved brick wall
    20: "<",                # left brick wall
    21: ">",                # right brick wall
    22: "^",                # upper brick wall
    23: "v",                # lower brick wall
    24: "#",                # brick wall
    25: "%",                # quadruple decorative wall
    26: "/",                # upper left curved smooth wall
    27: "\\",               # upper right curved smooth wall
    28: "\\",               # lower left curved smooth wall
    29: "/",                # lower right curved smooth wall
    30: "X",                # smooth wall
    31: "&"                 # planet surface
    }


if __name__ == "__main__":

    if len(sys.argv) != 3:
    
        sys.stderr.write("Usage: %s <Repton 2 UEF file> <level number>\n" % sys.argv[0])
        sys.exit(1)
    
    uef_file = sys.argv[1]
    
    try:
        level_number = int(sys.argv[2])
        if not 1 <= level_number <= 16:
            raise ValueError
    
    except ValueError:
        sys.stderr.write("The level number must be an integer from 1 to 12.\n")
        sys.exit(1)
    
    try:
        r = Repton2(uef_file)
    except NotFound:
        sys.stderr.write("Failed to find REPTONB file in the specified file: %s\n" % uef_file)
        sys.exit(1)
    except IncorrectSize:
        sys.stderr.write("The REPTONB file was not the expected size.\n")
        sys.exit(1)
    
    level = r.read_levels()[level_number - 1]
    
    for row in range(32):
    
        for column in range(32):

            value = level[row][column]
            
            try:
                char = chars[value]
                sys.stdout.write(char)
                #sys.stdout.write("%02x " % value)
            except KeyError:
                if value < 10:
                    sys.stdout.write(chr(ord("0") + value))
                else:
                    sys.stdout.write(chr(ord("a") + value - 10))
        
        print
    
    sys.exit()
