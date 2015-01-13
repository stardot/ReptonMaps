#!/usr/bin/env python

"""
read_sprites.py - A tool for exporting the sprites from Repton.

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

import os, sys

import Image
from Repton import IncorrectSize, NotFound, Repton

if __name__ == "__main__":

    if len(sys.argv) != 3:
    
        sys.stderr.write("Usage: %s <Repton UEF file> <output directory>\n" % sys.argv[0])
        sys.exit(1)
    
    uef_file = sys.argv[1]
    output_dir = sys.argv[2]
    
    try:
        r = Repton(uef_file)
    except NotFound:
        sys.stderr.write("Failed to find REPTON2 file in the specified file: %s\n" % uef_file)
        sys.exit(1)
    except IncorrectSize:
        sys.stderr.write("The REPTON2 file was not the expected size.\n")
        sys.exit(1)
    
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    
    sprites = r.read_sprites()
    
    if r.version == "Electron":
        size = (8, 16)
    else:
        size = (16, 32)
    
    n = 0
    
    for sprite in sprites:
    
        im = Image.fromstring("P", size, sprite)
        im.putpalette((0,255,0, 255,255,0, 255,0,0, 0,0,0))
        im.save(os.path.join(output_dir, "%02i.png" % n))
        
        n += 1
    
    sys.exit()
