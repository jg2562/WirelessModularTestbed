.. _network:

Network Program
==================

The networking program handles all creation of antennas along with several other simplifications for the user for easy antenna management.

The networking software can be controlled through both a linux socket and fifo file.

The networking software currently takes the following commands:


create
   ``create ANTENNA MODE [PARAMS...]``

   Returns:

   ``ID [FILES...]``

   Creates an antenna. Will create an return antenna id and files to attach to in order of mode. Once the antenna has been created, you can start to sending data through the files into the antenna.

   **Parameters**
     * **ANTENNA** The antenna type to create
     * **MODE** The mode to create the antenna with. i.e. for read/write do rw
     * **PARAMS** The params will be passed onto the antenna file

   **Returns**
     * **ID** The id of the antenna
     * **FILES** The files to interface with the antenna

   **Example**
	 >>> create bluetooth_client rw
	 bluetooth_client_12345678 bluetooth_client_12345678_r bluetooth_client_12345678_w

create-attach
   ``create-attach ANTENNA MODE [FILES...] [PARAMS...]``

   Returns:

   ``ID [FILES...]``

   Similar to create, creates an antenna but uses supplied files. Will create an return antenna id and files to attach to in order of mode. Once the antenna has been created, you can start to sending data through the files into the antenna.

   **Parameters**
     * **ANTENNA** The antenna type to create
     * **MODE** The mode to create the antenna with. i.e. for read/write do rw
     * **FILES** The files for the antenna to use as the interface
     * **PARAMS** The params will be passed onto the antenna file

   **Returns**
     * **ID** The id of the antenna
     * **FILES** The files to interface with the antenna

   **Example**
	 >>> create-attach bluetooth_client rw my_read_file my_write_file
	 bluetooth_client_12345678 my_read_file my_write_file

upload
   ``upload FILENAME``

   Returns:

   ``HASH FILE``

   Uploads the file back through the given connection. The hash is not separated by a space in the returned byte values. The data is also returned as a byte file.

   **Parameters**
     * **FILENAME** The filename to upload

   **Returns**
     * **HASH** The hash of the file
     * **FILE** The bytes of the file

   **Example**
	 >>> upload my_file
	 1234567890abcdefghijklmnopqrstuvwxyz

download
   ``download ID FILENAME``

   Returns:

   ``None``

   Downloads the file back through the given antenna. It will continue to try to download until the hash matches.

   **Parameters**
     * **ID** The antenna id to download the file through.
     * **FILENAME** The filename to download.

   **Example**
	 >>> download bluetooth_client_12345678 my_file
	 None

info
   ``info CMD ID``

   Returns:

   ``INFO``

   Gets info about the antenna. The type of info returned is based on the command given.

   **Parameters**
     * **CMD** The command for the info command. Currently, there's only 'status' which reports the status of the antenna
     * **ID** The antenna id for the info command

   **Returns**
     * **INFO** Returned info based on the command passed in

   **Example**
	 >>> info status bluetooth_client_12345678
	 Working

close
   ``close ID``

   Returns:

   ``INFO``

   Closes the antenna with the given id.

   **Parameters**
     * **ID** The antenna id to close

   **Returns**
     * **INFO** Returns the return code of the antenna program or an error message.

   **Example**
	 >>> close bluetooth_client_12345678
	 0

run
   ``run CMD``

   Returns:

   ``RETURN``

   Runs the command as a shell command.

   **Parameters**
     * **CMD** The command to run

   **Returns**
     * **RETURN** Returns the returned value from the run command

   **Example**
	 >>> run echo "hi"
	 hi
