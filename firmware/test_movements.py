import unittest
import time
import pickle
import logging
import struct
from comms_messages import *
from control import Control

buflen = 32
freq = 50.0

PORT = '/dev/ttyUSB0'

logging.basicConfig(level=logging.INFO)


class TestMovements(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.info("setup")
        cls._robot = Control(PORT)

    def test_error_pos(self):
        # home
        self._robot.send_packet(HOME, 0, 0)
        status, data = self._robot.get_response()
        assert status == HOME
       
        # wait for home to finish TODO this properly
        time.sleep(2)

        from moves import Moves
        moves = Moves()
        # add_point takes rectangular points
        moves.add_point(0, 0, 0)
        moves.add_point(600, 0, 0)
        moves.add_point(10, 0, 0)
        moves.add_point(400, 0, 0)
        moves.add_point(10, 0, 0)
        moves.process()
        points = moves.get_data()

        self.run_robot(points)

    def run_robot(self, points):
        self._robot.send_packet(STOP)
        status, data = self._robot.get_response()
        self._robot.send_packet(FLUSH)
        status, data = self._robot.get_response()
        print(status)
        assert status == BUFFER_EMPTY
       
        results = { 'index' : [], 'commanded' : [], 'measured' : [] } 
        i = 1
        last_index = 0
        index_offset = 0
        while i < len(points['i']):
            # fetch error
            if i % 10 == 0:
                self._robot.send_packet(STATUS)
                status, index = self._robot.get_response()
                if index < last_index:
                    index_offset += 256

                self._robot.send_packet(GET_LPOS)
                status, lpos = self._robot.get_response()
                assert status == GET_LPOS
                logging.info("[%03d] command = %03d actual = %03d" % (index + index_offset, points['i'][index+index_offset]['a'], lpos))
                results['index'].append(index + index_offset)
                results['commanded'].append(points['i'][index + index_offset]['a'])
                results['measured'].append(lpos)
                last_index = index

                
            if i == buflen / 2:
                self._robot.send_packet(START)
                status, data = self._robot.get_response()

            a = points['i'][i]['a']
            b = points['i'][i]['b']
            can = points['i'][i]['can']
            logging.debug("writing %d (%d,%d can %d)" % (i,a,b,can))
            self._robot.send_packet(LOAD, a, b, can, i)
            status, data = self._robot.get_response()
            logging.debug(self._robot.status_str(status))

            if status == BUFFER_OK:
                pass
            elif status == BUFFER_LOW:
                pass
            elif status == BUFFER_HIGH:
                time.sleep(buflen / 2 * (1 / freq))
            else:
                self.fail("packet %d unexpected status: %s [%s]" % (i, self._robot.status_str(status), data))

            i += 1
        with open('error.pkl', 'w') as fh:
            pickle.dump(results, fh)

        
if __name__ == '__main__':
    unittest.main()
