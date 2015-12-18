# Setup

install all the requirements in each directory:

* svg_converter
* planner (bokeh only required for cool visualisations)
* firmware

create directory structure for design files:

    mkdir -p designs/checks
    mkdir designs/gcodes
    mkdir designs/originals
    mkdir designs/points
    mkdir designs/visualisation

# Config

edit planner/conf.py for your robot's settings

# Use

create an svg and save in designs/originals, eg square.svg

    cd svg_converter
    convert_svg square 500

notes:

* name of file to convert is without .svg extension
* optional width after filename, defaults to 500

If all goes well, you should have new files in ./designs:

* gcodes/square.gcode - gcode like file for all the movements
* points/square.d - the movement commands for the robot
* checks/square.check.svg - svg picture showing placement of pic
* visualisation/square.html - html file showing movement planning steps

# Run

To see options for touch off and movement:

    cd firmware
    ./control.py -h

To run a file

    ./control.py --file ../designs/points/square.d

Use `ctrl-Z` for pause and `fg` to resume
