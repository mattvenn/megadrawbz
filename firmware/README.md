# polargraph servo

firmware for servos for a large polargraph/v-plotter

## setup

* servos should be wound fully with homing switch activated before packing
* drill holes/use clamps to attach servos to wall
* weights attached to servo ends
* wire servos (power & signal)
* measure height & width of fixing points
* send command to drop weights
* attach gondola
* go!

## removal

* send command to get low point
* detach gondola and attach weights
* home both servos
* unscrew/unmount

## to do

* homing button - prototyped with a microswitch & plate
* stall detect (current or encoder)?
* homing signal
* python keyboard control of both servos (in/out)

## programming notes

with programmer attached, breaks rs485 signal (due to leakage into TX pin?).
With a diode between TX programmer and RX on the board, both can work.

## can xbee setup

minicom -D /dev/ttyUSB0  -b 9600
then CTRL-A E to enable local echo

http://www.instructables.com/id/Processing-Controls-RC-Car-with-XBee-modules/step10/XBee-Configuration/

Type +++ to enter command mode, CoolTerm will respond with OK
ATID 1
ATMY 1
ATDH 0 
ATDL 2 
ATBD 6
ATWR

1 = 2400bps
2 = 4800bps
3 = 9600bps
4 = 19200bps
5 = 38400bps
6 = 57600 bps
7 = 115200 bps

## timing info

* messages sent every 20ms (50Hz).
* software serial has stop & start bits, plus 8 bits for the data.
* slave messages are 3 bytes (so 30 bits with software serial)
    * 57600 msg takes 0.5ms
    * 19200 msg takes 1.6ms
    * 9600 msg takes 3.1ms
    * 2400 msg takes 12ms
