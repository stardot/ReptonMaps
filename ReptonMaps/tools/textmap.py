#!/usr/bin/env python

"""
textmap.py - A tool for exporting the levels from Repton as text.

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
from Repton import IncorrectSize, NotFound, Repton

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
    
    try:
        r = Repton(uef_file)
    except NotFound:
        sys.stderr.write("Failed to find REPTON2 file in the specified file: %s\n" % uef_file)
        sys.exit(1)
    except IncorrectSize:
        sys.stderr.write("The REPTON2 file was not the expected size.\n")
        sys.exit(1)
    
    level = r.read_levels()[level - 1]
    
    for row in range(32):
    
        for column in range(32):

            value = level[row][column]
            
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
