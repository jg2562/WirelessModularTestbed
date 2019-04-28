import socket
import os
import time
import selectors
import argparse
import sys
from PyQt4 import QtGui, QtCore, uic

server_address = "network_command"
port = 65432

class DataThread(QtCore.QThread):
    def __init__(self, sel):
        super().__init__()
        self.sel = sel

    def __del__(self):
        self.wait()

    def run(self):
        while True:
            for key, mask in self.sel.select():
                key.data()

def send_command(command):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(server_address)
        sock.send(command.encode('utf-8') + b'\0')
        data = ""
        while len(data) == 0 or data[-1] != '\0':
            buf = sock.recv(1024)
            data += buf.decode('utf-8')
        return data[:-1].strip()

def send_chat(win, bt, fm):
    def _send_chat():
        user = win.userLine.text()
        msg = win.sendLine.text()
        win.sendLine.setText("")
        # os.write(fm, user.encode('utf-8'))
        os.write(bt, user.encode('utf-8') + ": ".encode('utf-8') + msg.encode('utf-8'))
    return _send_chat


def receive_data(win, bt, fm):
    meta = None
    msg = None

    def attempt_process():
        nonlocal meta
        nonlocal msg
        if msg is not None:
            win.chatLabel.setText(win.chatLabel.text() + msg + "\n")
            meta = None
            msg = None
            
    def receive_meta():
        nonlocal meta
        if meta:
            return
        meta = os.read(fm, 1024).decode('utf-8')
        attempt_process()

    def receive_msg():
        nonlocal msg
        if msg:
            return
        msg = os.read(bt, 1024).decode('utf-8')
        attempt_process()
    return receive_meta, receive_msg
    

def main():
    # Get arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('device', choices=['server','client'])
    parser.add_argument('--bt_add', default="B8:27:EB:4B:65:06")
    parser.add_argument('--bt_port', type=int, default=0x1001)
    parser.add_argument('--fm_freq', type=float, default=101.1)

    args = parser.parse_args()

    # Get arg data
    bt_add = args.bt_add
    bt_port = args.bt_port
    device = args.device
    fm_freq = args.fm_freq

    # # Start bluetooth
    if device == 'client':
        data = send_command("create bluetooth_client rw --address {} --port {}".format(bt_add,bt_port))
    else:
        data = send_command("create bluetooth_server rw --port {}".format(bt_port))
    # data = send_command("create echo rw")
    bt_in_file, bt_out_file = data.split(" ")

    # # Start fm
    # data = send_command("create fm_{} rw --frequency {}".format(device,fm_freq))
    # data = send_command("create echo rw")
    # fm_in_file, fm_out_file = data.split(" ")

    out = 1

    try:
        # Open file handles
        bt_in_fh = os.open(bt_in_file, os.O_RDONLY)
        bt_out_fh = os.open(bt_out_file, os.O_WRONLY)
        # fm_in_fh = os.open(fm_in_file, os.O_RDONLY)
        # fm_out_fh = os.open(fm_out_file, os.O_WRONLY)
        fm_in_fh = None
        fm_out_fh = None

        # Wait for connections
        # time.sleep(5)

        # Start application
        app = QtGui.QApplication(sys.argv)
        win = uic.loadUi("test/chat.ui")

        sel = selectors.DefaultSelector()

        rec_meta, rec_msg = receive_data(win, bt_in_fh, fm_in_fh)
        try:
            sel.register(bt_in_fh, selectors.EVENT_READ, rec_msg)
            # sel.register(fm_in_fh, selectors.EVENT_READ, rec_meta)

            win.sendButton.clicked.connect(send_chat(win, bt_out_fh, fm_out_fh))
            win.sendLine.returnPressed.connect(send_chat(win, bt_out_fh, fm_out_fh))

            thread = DataThread(sel)
            thread.start()

            win.show()
            out = app.exec()
        finally:
            del thread
            sel.unregister(bt_in_fh)
            # sel.unregister(fm_in_fh)

    finally:
        os.close(bt_in_fh);
        os.close(bt_out_fh);
        # os.close(fm_in_fh);
        # os.close(fm_out_fh);
        pass
    sys.exit(out)

if __name__ == "__main__":
    main()
