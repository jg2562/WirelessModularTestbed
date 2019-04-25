.. _network:

Network Program
==================

The networking program handles all creation of antennas along with several other simplifications for the user for easy antenna management.

The networking software can be controlled through both a linux socket and fifo file.

The networking software currently takes the following commands

.. tabularcolumns:: |l|l|
+---------------+---------------------------------------------------------------------------------+
|create         | Creates an antenna and gives back the files it attaches to                      |
+---------------+---------------------------------------------------------------------------------+
|create_attach  |  Creates an antenna and attach to files passed in                               |
+---------------+---------------------------------------------------------------------------------+
|upload         | upload the given file to the given antenna (mainly used internally by download) |
+---------------+---------------------------------------------------------------------------------+
|download       | download the given file from the given antenna                                  |
+---------------+---------------------------------------------------------------------------------+
|run            | Runs the given command as a shell command                                       |
+---------------+---------------------------------------------------------------------------------+
