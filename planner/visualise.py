#!/usr/bin/env python
from conf import conf
from bokeh.plotting import figure, output_file, show, save, ColumnDataSource, gridplot
import argparse
#from bokeh.models import HoverTool, PanTool, WheelZoom
import pickle
from pprint import pprint

p_width = 500


parser = argparse.ArgumentParser(description="visualise points")
parser.add_argument('--file', action='store', default='points.d', help="file to open")
parser.add_argument('--out', action='store', default='points.html', help="file to write")
args = parser.parse_args()

with open(args.file) as fh:
    data = pickle.load(fh)
x = []
y = []
for p in data['p']:
    x.append(p['point'][0])
    y.append(p['point'][1])

init_source = ColumnDataSource(
        data=dict(
            x=x,
            y=y,
        )
    )
x = []
y = []
max_spd = []
ltd_spd = []
points = range(len(data['bp']))
    
for p in data['bp']:
    x.append(p['point'][0])
    y.append(p['point'][1])
    max_spd.append(p['max_spd'])
    ltd_spd.append(p['ltd_spd'])

#pprint(data['bp'])
p_source = ColumnDataSource(
        data=dict(
            points=points,
            x=x,
            y=y,
            max_spd=max_spd,
            ltd_spd=ltd_spd,
        )
    )

x = []
y = []
a = []
b = []
can = []
for i in data['i']:
    x.append(i['xy'][0])
    y.append(i['xy'][1])
    a.append(i['a'])
    b.append(i['b'])
    can.append(i['can'])

points = range(len(data['i']))
i_source = ColumnDataSource(
        data=dict(
            x=x,
            y=y,
            a=a,
            b=b,
            can=can,
            points=points,
        )
    )

"""
hover = HoverTool(
        tooltips=[
          ("index", "$index"),
          ("max spd", "@max_spd"),
        ]
    )
"""
TOOLS = 'wheel_zoom,hover,pan,tap,resize,reset'
# output to static HTML file
output_file(args.out, title=args.file)
p1 = figure(plot_width=p_width, title="points", tools=TOOLS, x_range=(0,conf['width']),y_range=(conf['height'],0))
p1.line('x', 'y', line_width=2, source=init_source)
p1.square('x', 'y', source=init_source)

p2 = figure(plot_width=p_width, title="segments with max speeds", tools=TOOLS, x_range=(0,conf['width']), y_range=(conf['height'],0))
p2.line('x', 'y', line_width=2, source=p_source)
p2.square('x', 'y', size=max_spd, source=p_source)
p2.square('x', 'y', size=2, color="red", source=p_source)

p3 = figure(plot_width=p_width, title="max spd & ltd spd against points", tools=TOOLS)
p3.line('points', 'max_spd', line_width=2, source=p_source)
p3.line('points', 'ltd_spd', line_width=2, line_color="red", source=p_source)

p4 = figure(plot_width=p_width, title="interpolated points at fixed freq", tools=TOOLS, x_range=(0,conf['width']), y_range=(conf['height'],0))
p4.line('x','y', line_width=2, source=i_source)
p4.square('x','y', size=4, source=i_source)

p5 = figure(plot_width=p_width, title="string lengths fixed freq", tools=TOOLS )
p5.line('points', 'a', line_width=2, line_color="red", source=i_source)
p5.line('points', 'b', line_width=2, source=i_source)
p5.line('points', 'can', line_width=2, line_color="green", source=i_source)
# show the results
p = gridplot([[p1, p2],[p3, p4], [p5]])
#show(p)
save(p)
