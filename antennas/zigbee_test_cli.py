from xbee import ZigBee
from digi.xbee.devices import ZigBeeDevice
import serial
import time  

def main():
    ser = serial.Serial('/dev/ttyAMA0', 9600)
    port = '/dev/ttyAMA0'
    baud = 9600
    address = bytearray.fromhex('00 21 2E FF FF 02 46 33')
    
    zigbee = ZigBeeDevice(port, baud)
    zigbee.open()
    
    print(data_recieve_callback)
    print('Initialized...connecting')
    #zigbee.remote_at(dest_addr_long=address, command='D1', options='\x00')
    #print('Connected')
    #while True:
    #    print('...')
    #    response = zigbee.wait_read_frame()
    #    print(response)


if __name__ == '__main__':
    main()