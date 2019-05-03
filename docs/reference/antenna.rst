.. _antennas:

Antenna Programs
====================

The antenna files are used as bridges between the system and any hardware antennas.

In order to add a new type of antenna to the system, first create a file for the antenna software. Then take in the parameters: mode, file in, file out

The order in which the files are passed are the same order that mode declares them. E.g. a mode of 'wr' would pass the files in as 'write_file read_file'

After the files, any parameters were specified passed for this antenna file.

After the files have been created, simply pass the data between the antenna interface software and the file. At which point, the antenna has been added.

