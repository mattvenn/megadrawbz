#!/usr/bin/env python
import serial
import time
import logging
import struct
import pickle
import crcmod
import argparse
from conf import conf

#status
BUFFER_OK = 0
BUFFER_EMPTY = 1
BUFFER_FULL = 2
BAD_CKSUM = 3
MISSING_DATA = 4
BUFFER_LOW = 5
BUFFER_HIGH = 6
BAD_CMD = 7

#commands
START = 8
STOP = 9
LOAD = 10 
FLUSH = 11 
STATUS = 12 
SET_POS = 13
LOAD_P = 14
LOAD_I = 15
LOAD_D = 16
GET_LPOS = 17
GET_RPOS = 18
SLV_TIMEOUT = 19

buflen = 32
freq = 50.0

logging.basicConfig(level=logging.DEBUG)
crc8_func = crcmod.predefined.mkPredefinedCrcFun("crc-8-maxim")

class Control():

    def __init__(self, port="/dev/ttyUSB0"):
        print("opening port " + port)
        self._serial_port=serial.Serial()
        self._serial_port.port=port
        self._serial_port.timeout=2
        self._serial_port.baudrate=115200
        self._serial_port.open()
        self._serial_port.setDTR(True)

    """
    def __exit__(self):
        self._serial_port.close()
    """

    def status_str(self, status):
        if status == BUFFER_OK:
            return 'BUFFER_OK'
        if status == BUFFER_EMPTY:
            return 'BUFFER_EMPTY'
        if status == BUFFER_FULL:
            return 'BUFFER_FULL'
        if status == BAD_CKSUM:
            return 'BAD_CKSUM'
        if status == MISSING_DATA:
            return 'MISSING_DATA'
        if status == BUFFER_LOW:
            return 'BUFFER_LOW'
        if status == BUFFER_HIGH:
            return 'BUFFER_HIGH'
        if status == START:
            return 'START'
        
    def get_response(self):
        response = self._serial_port.read(4)
        if response:
            status, data, cksum = struct.unpack('<BHB', response)
            bin = struct.pack('<BH',status,data)
            # check cksum
            assert cksum == crc8_func(bin)
            return status, data
        else:
            logging.error("response time out")

    def send_packet(self, command, lpos=0, rpos=0, can=0, id=0):
        id = id % 256
        bin = struct.pack('<BHHBB', command, lpos, rpos, can, id)
        bin = struct.pack('<BHHBBB',command, lpos, rpos, can, id, crc8_func(bin))

        self.send_rs485_data(bin)

    def send_rs485_data(self, bin):
        self._serial_port.setDTR(False)
        time.sleep(0.001)
        self._serial_port.write(bin)
        time.sleep(0.001)
        self._serial_port.setDTR(True)

    def touchoff(self, l, r):
        logging.debug("touchoff %d,%d" % (l,r))
        self.send_packet(SET_POS,l,r)
        status, data = self.get_response()
        assert status == SET_POS

    def get_pos(self):
        self.send_packet(GET_LPOS)
        status, lpos = self.get_response()
        assert status == GET_LPOS

        self.send_packet(GET_RPOS)
        status, rpos = self.get_response()
        assert status == GET_RPOS
        logging.info("l = %d, r = %d" % (lpos, rpos))
        return lpos, rpos
        
    def single_load(self, l=0, r=0, can=0):
        logging.debug("move to %d,%d can = %d" % (l, r, can))
        self._serial_port.flushInput()
        self.send_packet(STOP)
        status, data = self.get_response()

        self.send_packet(FLUSH)
        status, data = self.get_response()

        self.send_packet(START)
        status, data = self.get_response()

        self.send_packet(LOAD, l, r, can, 1)
        status, data = self.get_response()

    def setpid(self, p, i, d):
        p = int(p * 1000)
        i = int(i * 1000)
        d = int(d * 1000)
        logging.debug("set p,i,d to %s,%s,%s" % (p,i,d))
        self.send_packet(LOAD_P, p, p)
        status, data = self.get_response()
        assert status == LOAD_P

        self.send_packet(LOAD_I, i, i)
        status, data = self.get_response()
        assert status == LOAD_I

        self.send_packet(LOAD_D, d, d)
        status, data = self.get_response()
        assert status == LOAD_D

    def pre_move(self, points):
        i = 0
        a = points['i'][i]['a']
        b = points['i'][i]['b']
        logging.info("first move is to %d, %d" % (a,b))
        a_cur, b_cur = self.get_pos()
        from moves import Moves
        moves = Moves()
        moves.add_point(float(a_cur), float(b_cur), 0)
        moves.add_point(float(a), float(b), 0)
        moves.process()
        points = moves.get_data()
        self.run_robot(points)
        
    def run_robot(self, points):
        self._serial_port.flushInput()
        self.send_packet(STOP)
        status, data = self.get_response()
        self.send_packet(FLUSH)
        status, data = self.get_response()
        assert status == BUFFER_EMPTY
        
        i = 1
        while i < len(points['i']):
            if i == buflen / 2:
                self.send_packet(START)
                status, data = self.get_response()

            a = points['i'][i]['a']
            b = points['i'][i]['b']
            can = points['i'][i]['can']
            if can == 0:
                can = conf['can_off']
            if can == 1:
                can = conf['can_on']
            logging.debug("writing %d (%d,%d can %d)" % (i,a,b,can))
            self.send_packet(LOAD, a, b, can, i)
            status, data = self.get_response()
            logging.debug(self.status_str(status))

            if status == BUFFER_OK:
                pass
            elif status == BUFFER_LOW:
                pass
            elif status == BUFFER_HIGH:
                time.sleep(buflen / 2 * (1 / freq))
            else:
                self.fail("packet %d unexpected status: %s [%s]" % (i, self.status_str(status), data))

            i += 1

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="control megadrawbz")
    parser.add_argument('--file', help='megadrawbz file to draw')
    parser.add_argument('--port', action='store', help="serial port", default='/dev/ttyUSB0')
    parser.add_argument('--touchoff', action='store', help="specify length of strings a,b (mm)")
    parser.add_argument('--setpid', action='store', help="p,i,d")
    parser.add_argument('--moveto', action='store', help="change string lengths to a,b (mm)")
    parser.add_argument('--can', action='store', default=90, help="can trigger amount", type=int)
    parser.add_argument('--getpos', const=True, action='store_const', help="get position")
    parser.add_argument('--nopremove', const=True, action='store_const', help="get position")
    #parser.add_argument('--safez', action='store', dest='safez', type=float, default=1, help="z safety")

    start_time = time.time()
    args = parser.parse_args()
    robot = Control(args.port)
    if args.touchoff:
        l, r = args.touchoff.split(',')
        robot.touchoff(int(l), int(r))
    elif args.moveto:
        l, r = args.moveto.split(',')
        can = args.can
        robot.single_load(int(l), int(r), can)
    elif args.setpid:
        p, i, d = args.setpid.split(',')
        robot.setpid(float(p), float(i), float(d))
    elif args.file:
        with open(args.file) as fh:
            points = pickle.load(fh)
        logging.debug("file is %d points long" % len(points['i']))
        if not args.nopremove:
            robot.pre_move(points)
        robot.run_robot(points)
    elif args.getpos:
        robot.get_pos()
    else:
        parser.print_help()
   
    logging.info("run took %d seconds" % (time.time() - start_time))
