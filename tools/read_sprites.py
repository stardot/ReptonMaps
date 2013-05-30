#!/usr/bin/env python

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
    
    n = 0
    
    for sprite in sprites:
    
        im = Image.fromstring("P", (8, 16), sprite)
        im.putpalette((0,255,0, 255,255,0, 255,0,0, 0,0,0))
        im.save(os.path.join(output_dir, "%02i.png" % n))
        
        n += 1
    
    sys.exit()
