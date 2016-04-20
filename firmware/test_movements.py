
    # move up & down ,fetching stopping pos and printing error
    def test_run_get_pos(self):
        self.send_packet(STOP)
        status, data = self.get_response()

        self.send_packet(FLUSH)
        status, data = self.get_response()

        self.send_packet(START)
        status, data = self.get_response()
        self.assertEqual(status, START)

        # do test around 1m string length
        amount = 50
        lpos = 1000
        rpos = 1000

        for i in range(1,20):
            self.send_packet(LOAD, lpos + amount, rpos + amount, 0, i)
            status, data = self.get_response()

            # wait for move
            time.sleep(1)

            self.send_packet(GET_LPOS)
            status, data = self.get_response()
            assert status == GET_LPOS
            print("L commanded = %d, cur = %d, err = %d" % (lpos+amount,data,lpos+amount-data))

            self.send_packet(GET_RPOS)
            status, data = self.get_response()
            assert status == GET_RPOS
            print("R commanded = %d, cur = %d, err = %d" % (lpos+amount,data,lpos+amount-data))
            amount *= -1
        
    def test_accuracy(self, num=2, amount=500):
        self._serial_port.flushInput()
        self.send_packet(STOP)
        status, data = self.get_response()
        self.assertEqual(status, STOP)
        self.send_packet(FLUSH)
        status, data = self.get_response()
        self.assertEqual(status, BUFFER_EMPTY)

        self.send_packet(SET_POS,0,0)
        status, data = self.get_response()
        self.assertEqual(status, SET_POS)

        self.send_packet(START)
        status, data = self.get_response()
        self.assertEqual(status, START)

        i = 1
        while i < num * 2:
            logging.debug(i)
            self.send_packet(LOAD, amount, amount, 0, i)
            status, data = self.get_response()
            logging.debug(self.status_str(status))
            #self.assertEqual(status, BUFFER_LOW)

            time.sleep(3)
            i += 1

            logging.debug(i)
            self.send_packet(LOAD, 0, 0, 0, i)
            status, data = self.get_response()
            logging.debug(self.status_str(status))
            #self.assertEqual(status, BUFFER_LOW)

            i += 1
            time.sleep(3)

    def test_run_robot(self):
        with open('points.d') as fh:
            points = pickle.load(fh)
        logging.debug("file is %d points long" % len(points['i']))

        self._serial_port.flushInput()
        self.send_packet(STOP)
        status, data = self.get_response()
        self.send_packet(FLUSH)
        status, data = self.get_response()
        self.assertEqual(status, BUFFER_EMPTY)
        
        i = 1
        while i < len(points['i']):
            if i == buflen / 2:
                self.send_packet(START)
                status, data = self.get_response()

            a = points['i'][i]['a']
            b = points['i'][i]['b']
            can = points['i'][i]['can']
            if can == 0:
                can = 30
            if can == 1:
                can = 90
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

    """
    timing info

    * messages sent every 20ms (50Hz).
    * software serial has stop & start bits, plus 8 bits for the data.
    * slave messages are 3 bytes (so 30 bits with software serial)
        * 57600 msg takes 0.5ms
        * 19200 msg takes 1.6ms
        * 9600 msg takes 3.1ms
        * 2400 msg takes 12ms



    """

        
