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
        self.fh = os.open(self.filename, (os.O_RDONLY if "r" else os.O_WRONLY) | os.O_NONBLOCK)
        self.opened = True

    def close(self):
        if self.opened:
            os.close(self.fh)

        if self.created:
            os.remove(self.filename)

class Antenna:
    def __init__(self, process, ant_type, modes, original_process_args, file_path, interfaces={}):

        self.ant_type = ant_type
        self.modes = modes

        self.interfaces = {mode:self._create_interface(self._create_filename(file_path, mode)
                                                       if mode not in interfaces else interfaces[mode], mode) for mode in self.modes}

        process_args = [self.interfaces[mode].get_file() for mode in self.modes] + original_process_args
        

        cmd = " ".join([process, modes] + process_args)
        self.process = sp.Popen(cmd, shell=True, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)

    def name(self):
        return self.ant_type

    def get_interfaces(self):
        return [self.interfaces[mode] for mode in self.modes]

    def call(self, data):
        return self.process.communicate(data, timeout=1)

    def close(self):
        self.process.terminate()
        [self.interfaces[mode].close() for mode in self.interfaces]

    def get_stderr(self):
        return self.process.stderr

    def _create_filename(self, file_path, mode):
        return os.path.join(file_path, self.ant_type + "_" + mode)

    def _create_interface(self, file, mode):
        return Interface(file, mode)

class NetworkManager:
    def __init__(self, config):
        self._setup(config)
        self.hash_algo = hashlib.sha256
        self.block_size = 65536

    def reset(self, config):
        self.close()
        self._setup(config)

    def process(self):
        events = self.sel.select()
        for key, mask in events:
            callback = key.data[0]
            callback(key)

    def close(self):
        [antenna.close() for antenna in self.antennas]
        self.in_interface.close()
        self.out_interface.close()
        self.server_socket.close()
        os.remove(self.config["server socket"])

    def _setup(self, config):
        self.config = config

        os.makedirs(self.config["pipe dir"],exist_ok=True)
        self.antennas = []
        self.antenna_dict = {}
        self.sel = selectors.DefaultSelector()
        self.fifo_files = set()
        self.in_interface = Interface(os.path.join(self.config["pipe dir"], "network_manager_r"), "r")
        self.out_interface = Interface(os.path.join(self.config["pipe dir"], "network_manager_w"), "w")
        self.in_interface.open()
        self.out_interface.open()

        try:
            os.remove(self.config["server socket"])
        except OSError:
            pass

        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.bind(self.config["server socket"])
        self.server_socket.listen()
        self.sel.register(self.server_socket, selectors.EVENT_READ, data=(self._handle_connection, None))
        self.sel.register(self.in_interface.get_fh(), selectors.EVENT_READ, data=(self._handle_file, None))

    def _create_connection(self, data):
        ant_type, modes, *original_process_args = data.split(" ")

        antenna = Antenna(self.config["processes"][ant_type], ant_type, modes, original_process_args, self.config["pipe dir"])
        print("Antenna started")
        self.antennas.append(antenna)
        self.antenna_dict[antenna.name()] = antenna
        self.sel.register(antenna.get_stderr(), selectors.EVENT_READ, data=(self._antenna_error, antenna))
        return " ".join([interface.get_file() for interface in antenna.get_interfaces()]).encode('utf-8')

    def _create_attach_connection(self, data):
        ant_type, modes, *original_process_args = data.split(" ")
        additional_interfaces = original_process_args[:len(modes)]
        original_process_args = original_process_args[len(modes):]
        interfaces = {mode: additional_interfaces[i] for i, mode in enumerate(modes)}

        antenna = Antenna(self.config["processes"][ant_type], ant_type, modes,
                          original_process_args, self.config["pipe dir"], interfaces=interfaces)

        print("Antenna started")
        self.antennas.append(antenna)
        self.antenna_dict[antenna.name()] = antenna
        self.sel.register(antenna.get_stderr(), selectors.EVENT_READ, data=(self._antenna_error, antenna))
        return " ".join([interface.get_file() for interface in antenna.get_interfaces()]).encode('utf-8')

    def _call_antenna(self, data):
        antenna_name = data[0]
        antenna = self.antenna_dict[antenna.name()] 
        antenna.call(data[1:])

    def _run_shell_command(self, data):
        out = sp.run(data, shell=True)
        return str(out.returncode).encode('utf-8')

    def _upload_file(self, filename):
        hasher = self.hash_algo()
        buf = b''
        with open(filename, "rb") as fh:
            buf = fh.read()
            hasher.update(buf)

        return hasher.digest() + buf

    def _download_file(self, data):
        out_file, download_file = data.split(" ")
        self.sel.unregister(self.in_interface.out)

        def __download():
            hasher = self.hash_algo()
            os.write(self.out_interface.get_fh(), ("upload " + download_file).encode('utf-8'))

            buf = os.read(self.in_interface.get_fh(), hasher.digest_size)
            hash = buf

            buf = os.read(self.in_interface.get_fh(), 1024)
            out_buf = buf
            while len(buf) > 0:
                out_fh.write(buf)
                buf = os.read(self.in_interface.get_fh(), 1024)
                out_buf += buf
            return hash_down, buf
        
        hash_down, buf = __download()
        hasher = self.hash_algo()
        hasher.update(buf)

        while hash_down != hasher.digest():
            hash_down, buf = __download()

            hasher = self.hash_algo()
            hasher.update(buf)
            pass

        out_fh = open(out_file, "wb")
        out_fh.write(buf)
        out_fh.close()

        self.sel.register(self.in_interface.get_fh(), selectors.EVENT_READ, data=(self._handle_file, None))

    def _process_command(self, command_list):
        commands = {"create": self._create_connection,
                    "create_attach": self._create_attach_connection,
                    "upload": self._upload_file,
                    "download": self._download_file,
                    "run": self._run_shell_command}
        command_name, command_data = command_list
        try:
            return commands[command_name](command_data)
        except KeyError:
            print("Invalid command: " + str(command_name))
            return "".encode('utf-8')

    def _close_antenna(self, antenna):
        self.sel.unregister(antenna.get_stderr())
        antenna.close()
        self.antennas.remove(antenna)
        del self.antenna_dict[antenna.name()]

    def _antenna_error(self, key):
        print("Antenna failed")
        print(os.read(key.fd,1024).decode('utf-8'))
        self._close_antenna(key.data[1])

    def _handle_file(self, key):
        try:
            data = ""
            while len(data) == 0 or data[-1] != '\0':
                buf = os.read(self.in_interface.get_fh(),1024)
                data += buf.decode('utf-8')
            data = data[:-1].strip()
            val = self._process_command(data.split(" ", 1))
            os.write(self.out_interface.get_fh(),val + b'\0')
        except IOError:
            pass

    def _handle_connection(self, key):
        conn, addr = self.server_socket.accept()
        try:
            try:
                data = ""
                while len(data) == 0 or data[-1] != '\0':
                    buf = conn.recv(1024)
                    data += buf.decode('utf-8')
                data = data[:-1].strip()
            except IOError as e:
                print("Receive connection IO ERROR: " + str(e))
                pass

            val = self._process_command(data.split(" ", 1))

            try:
                conn.send(val + b'\0')
            except IOError as e:
                print("Send connection IO ERROR: " + str(e))
        finally:
            try:
                conn.close()
            except OSError:
                pass

def main():
    config = {}
    with open("default_config.json") as fh:
        config = json.load(fh)
    manager = NetworkManager(config)
    try:
        while True:
            manager.process()
    finally:
        manager.close()

main()
