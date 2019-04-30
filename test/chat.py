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

def send_chat(win, bt, wifi):
    def _send_chat():
        meta = win.userLine.text()
        msg = win.sendLine.text()

        win.sendLine.setText("")
        add_msg(win.chatLabel, meta, msg)
        
        os.write(wifi, meta.encode('utf-8'))
        os.write(bt, msg.encode('utf-8'))
    return _send_chat

def add_msg(label, meta, msg):
    label.setText(label.text() + combine_msg(meta, msg) + "\n")

def combine_msg(meta, msg):
    return meta + ": " + msg

def receive_data(win, bt, wifi):
    meta = None
    msg = None

    def attempt_process():
        nonlocal meta
        nonlocal msg
        if meta is not None and msg is not None:
            add_msg(win.chatLabel, meta, msg)
            meta = None
            msg = None
            
    def receive_meta():
        nonlocal meta
        if meta:
            return
        meta = os.read(wifi, 1024).decode('utf-8')
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
    parser.add_argument('--bt_add', default="B8:27:EB:64:2E:AB")
    parser.add_argument('--bt_port', type=int, default=0x1001)
    parser.add_argument('--wifi_add', required=False)
    parser.add_argument('--wifi_port', type=float, default=3001)

    args = parser.parse_args()

    # Get arg data
    bt_add = args.bt_add
    bt_port = args.bt_port
    device = args.device
    wifi_add = args.wifi_add
    wifi_port = args.wifi_port

    if device == 'client' and wifi_add is None:
        print("Client needs wifi address")
        raise ValueError("Bad wifi address")

    # # Start bluetooth
    if device == 'client':
        data = send_command("create bluetooth_client rw --address {} --port {}".format(bt_add,bt_port))
    else:
        data = send_command("create bluetooth_server rw --port {}".format(bt_port))
    bt_id, bt_in_file, bt_out_file = data.split(" ")

    # Start wifi
    if device == 'client':
        data = send_command("create wifi_client rw --address {} --port {}".format(wifi_add,wifi_port))
    else:
        data = send_command("create wifi_server rw --port {}".format(wifi_port))

    wifi_id, wifi_in_file, wifi_out_file = data.split(" ")

    out = 1

    try:
        # Open file handles
        bt_in_fh = os.open(bt_in_file, os.O_RDONLY)
        bt_out_fh = os.open(bt_out_file, os.O_WRONLY)
        wifi_in_fh = os.open(wifi_in_file, os.O_RDONLY)
        wifi_out_fh = os.open(wifi_out_file, os.O_WRONLY)

        # Wait for connections
        # time.sleep(5)

        # Start application
        app = QtGui.QApplication(sys.argv)
        win = uic.loadUi("test/chat.ui")

        sel = selectors.DefaultSelector()

        rec_meta, rec_msg = receive_data(win, bt_in_fh, wifi_in_fh)
        try:
            sel.register(bt_in_fh, selectors.EVENT_READ, rec_msg)
            sel.register(wifi_in_fh, selectors.EVENT_READ, rec_meta)

            win.sendButton.clicked.connect(send_chat(win, bt_out_fh, wifi_out_fh))
            win.sendLine.returnPressed.connect(send_chat(win, bt_out_fh, wifi_out_fh))

            thread = DataThread(sel)
            thread.start()

            win.show()
            out = app.exec()
        finally:
            del thread
            sel.unregister(bt_in_fh)
            sel.unregister(wifi_in_fh)

    finally:
        os.close(bt_in_fh);
        os.close(bt_out_fh);
        os.close(wifi_in_fh);
        os.close(wifi_out_fh);
        pass
    sys.exit(out)

if __name__ == "__main__":
    main()
