The ReptonMaps project is a set of tools and modules to read, edit and write
maps for the Acorn Electron cassette versions of Superior Software's Repton
and Repton 2, and the BBC Micro DFS disk version of Repton.

The main tool is a GUI editor for editing levels in an existing Repton or
Repton 2 executable, stored in a Universal Emulator Format (UEF) or Single
Sided Disk (SSD) file. This depends on the cross-platform PyQt4 GUI
framework. This tool is typically run from the command line from within the
ReptonMaps directory itself, like this:

  ./editor.py Repton.uef

You will also need to provide a suitable Repton.uef or Repton2.uef file
containing the files for the Acorn Electron version of Repton or Repton 2,
or a Repton.ssd file containing the files for the BBC Micro version of
Repton. These are not provided in this package.

It is recommended that you save modified levels to a new UEF or SSD file and
keep the original as a backup.


Copyright and License Information
---------------------------------

Copyright (C) 2015 David Boddie <david@boddie.org.uk>

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
