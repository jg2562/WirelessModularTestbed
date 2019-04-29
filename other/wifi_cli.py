import socket

wifi_add = '10.17.167.26'
wifi_port = 5002

s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((wifi_add, wifi_port))

while True:
    data = s.recv(1024)
    msg = data.decode('utf-8')
    print(msg)
    
s.close()