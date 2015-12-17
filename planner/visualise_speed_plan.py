from bokeh.plotting import figure, output_file, show, ColumnDataSource, gridplot
import math

angle = []
speed = []
a = 0
while a < 360:
    angle.append(a)
    a += 1
    ang = a
    if ang > 90:
        ang = 90
    speed.append( 1 - math.sin(math.radians(ang)))

source = ColumnDataSource(
        data=dict(
            angle=angle,
            speed=speed,
        )
    )

output_file("lines.html", title="speed calculation")
TOOLS = 'wheel_zoom,hover,pan,tap,resize,reset'
p1 = figure(plot_width=600, plot_height=600, title="angle vs speed", tools=TOOLS, x_range=(0,360),y_range=(0,1))
p1.line('angle', 'speed', line_width=2, source=source)
show(p1)
