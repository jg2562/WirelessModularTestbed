from xbee import ZigBee
from digi.xbee.devices import ZigBeeDevice
import serial

def main():
    ser = serial.Serial('/dev/ttyAMA0', 9600)
    port = '/dev/ttyAMA0'
    baud = 9600
    print('Port Opened')
    data = 'Hello'
    remote_node_id = bytearray.fromhex('00 21 2E FF FF 02 45 01')
    
    
    #zigbee = ZigBee(ser)
    zigbee = ZigBeeDevice(port, baud)
    
    zigbee.open()
    print('Device open')
    zigbee_net = zigbee.get_network()
    #remote = zigbee_net.discover_device(remote_node_id)
    
    print('Network open...sending data')
    while True:
        #zigbee.send('at', frame_id='A', command='DH')
        #zigbee.write('1')
        zigbee.send_data(remote_node_id, data)
        print('...')
    response = zigbee.wait_read_frame()
    print(response)


if __name__ == '__main__':
    main()