#!/usr/bin python3

import os
import socket
import subprocess as sp
import selectors
import json
import hashlib

class Interface:
    def __init__(self, filename, mode):
        self.filename = filename
        self.mode = mode
        self.created = False
        self.opened = False
        self.fh = None
        self._create()

    def _create(self):
        # Creates file if non-existent
        if not os.path.exists(self.filename):
            os.mkfifo(self.filename)
            self.created = True
        return self.filename

    def get_mode(self):
        return self.mode

    def get_file(self):
        return self.filename

    def get_fh(self):
        return self.fh

    def open(self):
        # Opens a file handle based on mode
        # Needs to be non-blocking to prevent network software from halting
        self.fh = os.open(self.filename, (os.O_RDONLY if "r" else os.O_WRONLY) | os.O_NONBLOCK)
        self.opened = True

    def close(self): 
        # If file handle has been opened, close it
        if self.opened:
            os.close(self.fh)

        # If interface created the file, delete it
        if self.created:
            os.remove(self.filename)

class Antenna:
    def __init__(self, process, ant_type, modes, original_process_args, file_path, interfaces={}):

        # Save off antenna type and modes
        self.ant_type = ant_type
        self.modes = modes

        # Create a dictionary of all interfaces, also generate interfaces for all files
        self.interfaces = {mode:self._create_interface(self._create_filename(file_path, mode)
                                                       if mode not in interfaces else interfaces[mode], mode) for mode in self.modes}

        # Create the arguments to be passed into the process
        process_args = [self.interfaces[mode].get_file() for mode in self.modes] + original_process_args
        

        # Create the command to be run and run it
        cmd = " ".join([process, modes] + process_args)
        self.process = sp.Popen(cmd, shell=True, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)

    def name(self):
        return self.ant_type

    def get_interfaces(self):
        # Returns all interfaces in order of mode
        return [self.interfaces[mode] for mode in self.modes]

    def call(self, data):
        # Call the interface
        return self.process.communicate(data, timeout=1)

    def close(self):
        # Kill process, then close all interfaces
        self.process.terminate()
        [self.interfaces[mode].close() for mode in self.interfaces]

    def get_stderr(self):
        return self.process.stderr

    def _create_filename(self, file_path, mode):
        # Creates basic filename based on antenna type and mode
        return os.path.join(file_path, self.ant_type + "_" + mode)

    def _create_interface(self, file, mode):
        return Interface(file, mode)

class NetworkManager:
    def __init__(self, config):
        self._setup(config)
        # Save off hash algorithm to be used later
        self.hash_algo = hashlib.sha256
        self.block_size = 65536

    def reset(self, config):
        self.close()
        self._setup(config)

    def process(self):
        # Get events then run through all of them calling their callback
        events = self.sel.select()
        for key, mask in events:
            callback = key.data[0]
            callback(key)

    def close(self):
        # Close all antennas
        [antenna.close() for antenna in self.antennas]
        # Close interfaces then remove server socket
        self.in_interface.close()
        self.out_interface.close()
        self.server_socket.close()
        os.remove(self.config["server socket"])

    def _setup(self, config):
        # Save config
        self.config = config

        # Setup everything to default values
        os.makedirs(self.config["pipe dir"],exist_ok=True)
        self.antennas = []
        self.antenna_dict = {}
        self.sel = selectors.DefaultSelector()
        self.fifo_files = set()

        # Run all config commands
        self._run_config_precommands()

        # Create the two interfaces for the network
        self.in_interface = Interface(os.path.join(self.config["pipe dir"], "network_manager_r"), "r")
        self.out_interface = Interface(os.path.join(self.config["pipe dir"], "network_manager_w"), "w")
        # Open the two interfaces
        self.in_interface.open()
        self.out_interface.open()

        # Remove old socket if previous not properly closed 
        try:
            os.remove(self.config["server socket"])
        except OSError:
            pass

        # Create and bind to socket and begin listening
        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.bind(self.config["server socket"])
        self.server_socket.listen()

        # Register the socket and interface
        self.sel.register(self.server_socket, selectors.EVENT_READ, data=(self._handle_connection, None))
        self.sel.register(self.in_interface.get_fh(), selectors.EVENT_READ, data=(self._handle_file, None))

    def _run_config_precommands(self):
        # Check if the commands are in the config
        if "commands" in self.config:
            # Process all commands
            cmds = self.config["commands"]
            for cmd in cmds:
                self._process_command(cmd.split(" ", 1))

    def _create_connection(self, data):
        # Get information from data
        ant_type, modes, *original_process_args = data.split(" ")

        # Create the antenna
        antenna = Antenna(self.config["processes"][ant_type], ant_type, modes, original_process_args, self.config["pipe dir"])
        print("Antenna started")

        # Save off the antenna
        self.antennas.append(antenna)
        self.antenna_dict[antenna.name()] = antenna

        # Register the standard err in case of failure
        self.sel.register(antenna.get_stderr(), selectors.EVENT_READ, data=(self._antenna_error, antenna))

        # Return interfaces to antenna
        return " ".join([interface.get_file() for interface in antenna.get_interfaces()]).encode('utf-8')

    def _create_attach_connection(self, data):
        # Get information from data
        ant_type, modes, *original_process_args = data.split(" ")

        # Gather interfaces from data
        additional_interfaces = original_process_args[:len(modes)]
        original_process_args = original_process_args[len(modes):]
        # Create the interfaces
        interfaces = {mode: additional_interfaces[i] for i, mode in enumerate(modes)}

        # Geenrate the antenna with the interfaces
        antenna = Antenna(self.config["processes"][ant_type], ant_type, modes,
                          original_process_args, self.config["pipe dir"], interfaces=interfaces)

        print("Antenna started")

        # Save off the antenna
        self.antennas.append(antenna)
        self.antenna_dict[antenna.name()] = antenna

        # Register the standard err in case of failure
        self.sel.register(antenna.get_stderr(), selectors.EVENT_READ, data=(self._antenna_error, antenna))

        # Return interfaces to antenna
        return " ".join([interface.get_file() for interface in antenna.get_interfaces()]).encode('utf-8')

    def _call_antenna(self, data):
        # Get the data in the first area
        antenna_name = data[0]
        # Find antenna and call it
        antenna = self.antenna_dict[antenna.name()] 
        antenna.call(data[1:])

    def _run_shell_command(self, data):
        # Run shell command
        out = sp.run(data, shell=True)
        return str(out.returncode).encode('utf-8')

    def _upload_file(self, filename):
        # Create Hash algorithm
        hasher = self.hash_algo()
        buf = b''
        # Read it into buffer and hash it
        with open(filename, "rb") as fh:
            buf = fh.read()
            hasher.update(buf)

        # Send hashed value and buffer
        return hasher.digest() + buf

    def _download_file(self, data):
        # Get files from data
        out_file, download_file = data.split(" ")

        # Unregister interface to prevent weird errors
        self.sel.unregister(self.in_interface.out)

        # Create hasher
        hasher = self.hash_algo()

        # Create an internal download function
        def __download():
            # Write command to other device
            os.write(self.out_interface.get_fh(), ("upload " + download_file).encode('utf-8'))

            # Read in the hash they're sending back into hash
            buf = os.read(self.in_interface.get_fh(), hasher.digest_size)
            hash_down = buf

            # Read in more data and repeat until buffer empty
            buf = os.read(self.in_interface.get_fh(), 1024)
            out_buf = buf
            while len(buf) > 0:
                out_fh.write(buf)
                buf = os.read(self.in_interface.get_fh(), 1024)
                out_buf += buf
            return hash_down, buf
        
        # download file
        hash_down, buf = __download()
        # Update hash
        hasher.update(buf)

        # Check if hashes match, otherwise repeat
        while hash_down != hasher.digest():
            hash_down, buf = __download()

            hasher = self.hash_algo()
            hasher.update(buf)
            pass

        # Write file data to file
        out_fh = open(out_file, "wb")
        out_fh.write(buf)
        out_fh.close()

        # Reregister interface
        self.sel.register(self.in_interface.get_fh(), selectors.EVENT_READ, data=(self._handle_file, None))

    def _process_command(self, command_list):
        # Create a list of commands
        commands = {"create": self._create_connection,
                    "create_attach": self._create_attach_connection,
                    "upload": self._upload_file,
                    "download": self._download_file,
                    "run": self._run_shell_command}
        # Parse out command and call command
        command_name, command_data = command_list
        try:
            return commands[command_name](command_data)
        except KeyError:
            print("Invalid command: " + str(command_name))
            return "".encode('utf-8')

    def _close_antenna(self, antenna):
        # Unregister the antenna standard error
        self.sel.unregister(antenna.get_stderr())
        # Close antenna
        antenna.close()
        # Remove stored antenna
        self.antennas.remove(antenna)
        del self.antenna_dict[antenna.name()]

    def _antenna_error(self, key):
        # Let use know antenna failed
        print("Antenna failed")
        print(os.read(key.fd,1024).decode('utf-8'))
        # Close antenna
        self._close_antenna(key.data[1])

    def _handle_file(self, key):
        try:
            # Get data from file
            data = ""
            while len(data) == 0 or data[-1] != '\0':
                buf = os.read(self.in_interface.get_fh(),1024)
                data += buf.decode('utf-8')
            # Preprocess data
            data = data[:-1].strip()
            # Call command
            val = self._process_command(data.split(" ", 1))
            # Send back command
            os.write(self.out_interface.get_fh(),val + b'\0')
        except IOError:
            pass

    def _handle_connection(self, key):
        conn, addr = self.server_socket.accept()
        try:
            # Receive command
            try:
                # Get data from file
                data = ""
                while len(data) == 0 or data[-1] != '\0':
                    buf = conn.recv(1024)
                    data += buf.decode('utf-8')
                # Preprocess data
                data = data[:-1].strip()
            except IOError as e:
                print("Receive connection IO ERROR: " + str(e))
                pass

            # Call command
            val = self._process_command(data.split(" ", 1))

            # Send back command data
            try:
                # Send back command
                conn.send(val + b'\0')
            except IOError as e:
                print("Send connection IO ERROR: " + str(e))
        finally:
            try:
                conn.close()
            except OSError:
                pass

def main():
    # Create an empty config in case of failure
    config = {}

    # Load config
    with open("default_config.json") as fh:
        config = json.load(fh)

    # Create network manager
    manager = NetworkManager(config)
    
    # Have manager continually process
    try:
        while True:
            manager.process()
    finally:
        manager.close()

if __name__ == "__main__":
    main()
