import unittest
import time
import logging
import struct
from comms_messages import *
from control import Control

buflen = 32
freq = 50.0

PORT = '/dev/ttyUSB0'

logging.basicConfig(level=logging.INFO)


class TestComms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._robot = Control(PORT)

    def test_send_flush(self):
        self._robot.send_packet(FLUSH)
        status, data = self._robot.get_response()
        self.assertEqual(status, BUFFER_EMPTY)

    def test_send_PID(self):
        """
        float kp = .45;
        float ki = 0.000;
        float kd = .25;
        """
        self._robot.send_packet(LOAD_P, 450)
        status, data = self._robot.get_response()
        self.assertEqual(status, LOAD_P)

        self._robot.send_packet(LOAD_I, 0)
        status, data = self._robot.get_response()
        self.assertEqual(status, LOAD_I)

        self._robot.send_packet(LOAD_D, 250)
        status, data = self._robot.get_response()
        self.assertEqual(status, LOAD_D)

    def test_set_pos(self,l=100, r=100):
        self._robot.send_packet(SET_POS,l, r)
        status, data = self._robot.get_response()
        self.assertEqual(status, SET_POS)

    def test_get_lpos(self):
        self.test_send_flush()
        for pos in range(10,100,10):
            self._robot.send_packet(SET_POS,pos,pos)
            status, data = self._robot.get_response()
            assert status == SET_POS

            time.sleep(0.01)
            self._robot.send_packet(GET_LPOS)
            status, data = self._robot.get_response()
            assert status == GET_LPOS
            assert data == pos - 1 # why ?

    @unittest.skip("skipping")
    def test_get_rpos(self):
        for pos in range(10,100,10):
            self._robot.send_packet(SET_POS,pos,pos)
            status, data = self._robot.get_response()
            assert status == SET_POS

            self._robot.send_packet(GET_RPOS)
            status, data = self._robot.get_response()
            assert status == GET_RPOS
            assert data == pos - 1 # why?

    def test_send_stop(self):
        self._robot.send_packet(STOP)
        status, data = self._robot.get_response()
        self.assertEqual(status, STOP)

    def test_good_cksum(self):
        self.test_send_stop()
        self.test_send_flush()
        for i in range(1,50):
            logging.debug(i)
            self._robot.send_packet(LOAD, i, i, 0, i)
            status, data = self._robot.get_response()
            self.assertNotEqual(status, BAD_CKSUM)

    def test_bad_cksum(self):
        self.test_send_stop()
        self.test_send_flush()
        for i in range(1,100):
            logging.debug(i)
            bin = struct.pack('<BHHBBB',START, i, i, i, i, 0xFF)
            self._robot.send_rs485_data(bin)
            status, data = self._robot.get_response()
            self.assertEqual(status, BAD_CKSUM)

    def test_buffer_underrun(self):
        self._robot.send_packet(FLUSH)
        status, data = self._robot.get_response()
        self.assertEqual(status, BUFFER_EMPTY)
        self._robot.send_packet(START)
        status, data = self._robot.get_response()
        self.assertEqual(status, START)

        # run at less than frequency
        for i in range(1, buflen / 2):
            logging.debug(i)
            self._robot.send_packet(LOAD, 0, 0, 0, i)
            status, data = self._robot.get_response()
            time.sleep(20 * (1 / freq))

        self._robot.send_packet(STATUS)
        status, data = self._robot.get_response()
        self.assertEqual(status, BUFFER_EMPTY)

    def test_buffer_overrun(self):
        self._robot.send_packet(FLUSH)
        status, data = self._robot.get_response()
        self.assertEqual(status, BUFFER_EMPTY)
        self._robot.send_packet(STOP)
        status, data = self._robot.get_response()
        self.assertEqual(status, STOP)

        for i in range(1, buflen + 1):
            logging.debug(i)
            self._robot.send_packet(LOAD, 0, 0, 0, i)
            status, data = self._robot.get_response()
            time.sleep(0.1 * (1 / freq))

        self.assertEqual(status, BUFFER_FULL)

        
    def test_missing_data(self):
        self._robot.send_packet(STOP)
        status, data = self._robot.get_response()
        self._robot.send_packet(FLUSH)
        status, data = self._robot.get_response()
        self.assertEqual(status, BUFFER_EMPTY)

        for i in range(1, buflen / 2):
            logging.debug(i)
            self._robot.send_packet(LOAD, 0, 0, 0, i)
            status, data = self._robot.get_response()

        self._robot.send_packet(LOAD)
        status, data = self._robot.get_response()

        self.assertEqual(status, MISSING_DATA)
        self.assertEqual(data, buflen / 2 - 1)

    def test_single_load(self):
        self._robot.send_packet(STOP)
        status, data = self._robot.get_response()
        self.assertEqual(status, STOP)
        self._robot.send_packet(FLUSH)
        status, data = self._robot.get_response()
        self.assertEqual(status, BUFFER_EMPTY)

        self._robot.send_packet(START)
        status, data = self._robot.get_response()
        self.assertEqual(status, START)

        self._robot.send_packet(LOAD, 0, 0, 30, 1)
        status, data = self._robot.get_response()
        self.assertEqual(status, BUFFER_LOW)

    def test_keep_buffer_full(self, num=500):

        self.test_send_stop()
        self.test_set_pos(0, 0)
        self.test_send_flush()

        for i in range(1, num):
            logging.debug(i)
            if i == buflen / 2:
                logging.debug("starting servo")
                self._robot.send_packet(START)
                status, data = self._robot.get_response()
                self.assertEqual(status, START)

            can = i % 70
            self._robot.send_packet(LOAD, 0, 0, can, i)
            status, data = self._robot.get_response()

            if status == BUFFER_OK:
                pass
            elif status == BUFFER_LOW:
                pass
            elif status == BUFFER_HIGH:
                logging.debug("buffer high, waiting...")
                time.sleep(buflen / 4 * (1 / freq))
            else:
                self.fail("packet %d unexpected status: %s [%s]" % (i, self.status_str(status), data))


if __name__ == '__main__':
    unittest.main()
    exit(0)

    # just run the one test
    slave = unittest.TestSuite()
    slave.addTest(TestBuffer('test_slave_comms')) 

    log_file = 'log_file.txt'
    with open(log_file, "a") as fh:
        runner = unittest.TextTestRunner(fh)
        runner.run(slave)
