from xbee.thread import XBee
import serial

def main():
    ser = serial.Serial('/dev/ttyAMA0', 9600)
    zigbee = XBee(ser)
    zigbee.send('at', frame_id='A', command='DH')
    
    response = zigbee.wait_read_frame()
    print(response)


if __name__ == '__main__':
    main()