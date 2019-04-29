import socket
HOST=input('Enter IP: ')
PORT=5002
s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)
conn, addr=s.accept()
s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
print ('Connected by', addr)

while True:
    msg = input('> ')
    data = msg.encode('utf-8')
    conn.send(data)