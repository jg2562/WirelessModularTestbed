
buff = b''
while True:
    buff += sock.recv(1024)
    num = struct.unpack('!i', buff[:4])[0]
    num += 1
    print(num)
    send_data = struct.pack('!i', num)
    sock.send(send_data)
