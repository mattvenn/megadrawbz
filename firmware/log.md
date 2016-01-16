## Thu Jan  7 16:55:43 GMT 2016

TODO
doesn't stop spraying at end!

pid tuning:

    ./control.py  --setpid 1.5,0,0

found errors with not converting string lengtsh to x y on premove - fixed

TODO
convert_svg not clear, needs to be converted to python with arguments for width:

got this when converting an unflattened circle:

    RuntimeError: maximum recursion depth exceeded in cmp
    creating path visualisation in ../designs/visualisation/circle.html

`fixed` by doing this:

    import sys
    sys.setrecursionlimit(2000)

maybe find a better way to write algorithm?

## Fri Dec  4 23:26:19 GMT 2015

investigating why keep getting serial timeout on the unit tests
 fails about 5 in 20 of 500 sends :

    while true; do python test_arduino.py TestBuffer.test_keep_buffer_full >> log 2>&1 ; done
* put led in servo code to see how much space is left, plenty
* put led in servo code serial read, find that when it fails the servo doesn't get it's message
* commented out sserial stuff, starst working
* uncomment, fails
* change TX pin from A5 to A4, seems to start working again??!!

## Fri Dec 11 17:59:16 GMT 2015

played with pid, and this seemed good over weights from 350 to 1.4kg
paying in and out 500mm

./control.py  --setpid 0.55,0.001,0.55 --port=/dev/ttyUSB1
