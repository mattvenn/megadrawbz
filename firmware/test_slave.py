

    @unittest.skip("skipping")
    def test_read_slave_nums(self):
        slave_port=serial.Serial()
        slave_port.port='/dev/ttyUSB0'
        slave_port.timeout=1
        slave_port.baudrate=115200
        slave_port.open()

        slave_port.write('a')
        ok = int(slave_port.readline())
        bad_cksum = int(slave_port.readline())
        logging.debug("bad cksum = %d, ok = %d" % (bad_cksum, ok))

    def test_slave_direct(self):
        slave_port=serial.Serial()
        slave_port.port='/dev/ttyUSB0'
        slave_port.timeout=1
        slave_port.baudrate=57600
        slave_port.open()
        
    # @unittest.skip("skipping")
    def test_slave_comms(self):
        slave_port=serial.Serial()
        slave_port.port='/dev/ttyUSB0'
        slave_port.timeout=1
        slave_port.baudrate=115200
        slave_port.open()

        # this doesn't always work, don't know why
        import ipdb; ipdb.set_trace()
        slave_port.write('b') # clear sums
        slave_port.write('a')
        ok = int(slave_port.readline())
        bad_cksum = int(slave_port.readline())
        self.assertEqual(ok, 0)
        self.assertEqual(bad_cksum, 0)

        # run tests on buffer
        num = 1000
        self.test_keep_buffer_full(num)

        # wait for buffer to empty
        time.sleep(1.5 * buflen * (1 / freq))

        self.send_packet(STATUS)
        status, data = self.get_response()
        self.assertEqual(status, BUFFER_EMPTY)

        slave_port.write('a')
        ok = int(slave_port.readline())
        bad_cksum = int(slave_port.readline())
        logging.debug("bad cksum = %d, ok = %d" % (bad_cksum, ok))
        self.assertEqual(ok, num-1)  # starts at 1
        self.assertEqual(bad_cksum, 0)
    
