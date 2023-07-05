# file: qtfscan.py
# create: 2023 04 24
# author: Roch Schanen

DEBUG_FLAGS = [
    # "ALL",
    ]

#####################################################################

# LIBRARIES

# standard libraries
from sys import exit
from time import sleep, time, strftime, localtime
from datetime import datetime

# from package: "https://numpy.org/"
from numpy import pi, cos, sin
from numpy import array
from numpy import loadtxt
from numpy import ceil, floor
from numpy import log, log10, exp, square
from numpy import linspace, logspace

# from package: "https://matplotlib.org/"
from matplotlib.pyplot import figure
from matplotlib.pyplot import fignum_exists
from matplotlib.backends.backend_pdf import PdfPages

# from package: "https://scipy.org/"
from scipy.optimize import curve_fit as fit

#####################################################################

# import wx

# a = wx.App()
# f = wx.Frame()

# d = wx.FileDialog(f,
#     message     = "Open",
#     wildcard    = "data files (*.dat)|*.dat", 
#     style       = wx.FD_OPEN
#                 | wx.FD_FILE_MUST_EXIST,
#                 # | wx.FD_MULTIPLE,
#     )

# d.ShowModal()
# # fp = d.GetPaths()
# fp = d.GetPath()
# d.Destroy()

fp = "./QTF_TO_20230705T090205.dat"

#####################################################################

# LOCAL FUNCTIONS AND CLASSES

def debug(*flags):
    for f in flags: 
        if f.upper() in DEBUG_FLAGS:
            return True
    if "ALL" in DEBUG_FLAGS:
        return True
    return False

def selectfigure(name):
    if not fignum_exists(name):
        # create figure
        fg = figure(name)
        # set A4 paper dimensions
        fg.set_size_inches(8.2677, 11.6929)
        # create square axis
        w, h = array([1, 1 / 1.4143])*0.7
        x, y = (1-w)/2, (1-h)/2
        ax = fg.add_axes([x, y, w, h])
    else:
        # select figure
        # (here the figure can be of any type)
        fg = figure(name)
        # get axes
        ax = fg.get_axes()[0]
    # done
    return fg, ax

def headerText(text, fg):
    w, h = array([1, 1 / 1.4143])*0.7
    x, y = (1-w)/2, (1-h)/2
    # tx = fg.text(x+w/2, 3*y/2+h, text)
    tx = fg.text(x, 3*y/2+h, text)
    tx.set_fontfamily('monospace')
    tx.set_horizontalalignment('left')
    tx.set_verticalalignment('center')
    tx.set_fontsize("small")
    return tx

def footerText(text, fg):
    w, h = array([1, 1 / 1.4143])*0.7
    x, y = (1-w)/2, (1-h)/2
    # tx = fg.text(x+w/2, y/2, text)
    tx = fg.text(x, y/2, text)
    tx.set_fontfamily('monospace')
    tx.set_horizontalalignment('left')
    tx.set_verticalalignment('center')
    tx.set_fontsize("small")
    return tx

def _getTickIntervals(start, stop, ticks):

    ln10 = 2.3025850929940459

    # trial table
    T = [0.010, 0.020, 0.025, 0.050,
         0.100, 0.200, 0.250, 0.500,
         1.000, 2.000, 2.500, 5.000]

    # corresponding tick sub division intervals
    S = [5.0,   4.0,   5.0,   5.0,
         5.0,   4.0,   5.0,   5.0,
         5.0,   4.0,   5.0,   5.0]

    span = stop - start                         # get span
    d = exp(ln10 * floor(log10(span)))          # find decade
    span /= d                                   # re-scale

    # find number of ticks below and closest to n
    i, m = 0, floor(span / T[0])                # start up
    while m > ticks:                            # next try?
        i, m = i + 1, floor(span / T[i + 1])    # try again 

    # re-scale
    mi =  d * T[i]   # main tick intervals
    si = mi / S[i]   # sub tick intervals

    # done
    return mi, si

def _getTickPositions(start, stop, ticks):

    # get intervals
    mi, si = _getTickIntervals(start, stop, ticks)

    # main ticks (round is the built-in python version)
    ns = ceil(start / mi - 0.001) * mi  # start
    ne = floor(stop / mi + 0.001) * mi  # end
    p  = round((ne - ns) / mi) + 1      # fail safe
    M  = linspace(ns, ne, p)            # main positions

    # sub ticks (round is the built-in python version)
    ns = ceil(start / si + 0.001) * si  # start
    ne = floor(stop / si - 0.001) * si  # end
    p  = round((ne - ns) / si) + 1      # fail safe
    S  = linspace(ns, ne, p)            # sub positions

    # done
    return M, S

class Document():

    def __init__(self, pathname = None):
        if pathname is not None:
            self._DOC = self.opendocument(pathname)
        return

    def opendocument(self, pathname):
        self._DOC = PdfPages(pathname)
        return self._DOC

    def exportfigure(self, name):
        if debug("doc"): print(f"export '{name}'")
        args = selectfigure(name)
        self._DOC.savefig(args[0])
        return

    def closedocument(self):
        self._DOC.close()
        return

def seconds(s):
    t =  float(s[0:2])*3600
    t += float(s[3:5])*60
    t += float(s[6: ])*1
    return t

# in-phase fitting function
def FX(t, p, w, h, o):
    x = (t-p)/w
    y = h/(1+square(x))+o
    return y

# quadrature fitting function
def FY(t, p, w, h, o):
    x = (t-p)/w
    y = -x*h/(1+square(x))+o
    # y = +x*h/(1+square(x))+o
    return y

#####################################################################

# IMPORT DATA

data = loadtxt(fp,
    converters = {
        0: seconds,
        1: float,
        2: float,
        3: float,
    })

T = data[:, 0]
F = data[:, 1]
X = data[:, 2]
Y = data[:, 3]

#####################################################################

# ROTATE BY AN ANGLE "A" BEFORE DISPLAY

a_deg   = 20.0
a_rad   = a_deg*pi/180
xr      = X*cos(a_rad)-Y*sin(a_rad)
yr      = X*sin(a_rad)+Y*cos(a_rad)
X, Y    = xr, yr
# To adjust the lockin, substract the
# value of a from the lockin phase.

#####################################################################

# COMPUTE DATA SPAN AND ENGINEERING UNITS AND SHIFT EXPONENT

fs, fe = min(F), max(F)
xs, xe = min(X), max(X)
ys, ye = min(Y), max(Y)

zs, ze = min(xs, ys), max(xe, ye)

# get engineering units
f, s = {
     0: (1E+00,  ""),
    -1: (1E+03, "m"),
    -2: (1E+06, "µ"),
    -3: (1E+09, "n"),
    -4: (1E+12, "p"),
    +1: (1E-03, "K"),
    +2: (1E-06, "M"),
    +3: (1E-09, "G"),
    +4: (1E-12, "T"),
}[int(floor(log10(ze-zs)/3))]

# re-scale data and span limits
X, Y    =  X*f,  Y*f
xs, xe, = xs*f, xe*f
ys, ye  = ys*f, ye*f 
zs, ze  = zs*f, ze*f

#####################################################################

# FIGURE "FREQUENCY"

fg, ax = selectfigure("frequency")

# fix X labels and ticks
xf =  0.1*(fe-fs)
ax.set_xlim(fs-xf, fe+xf)
MX, SX = _getTickPositions(fs-xf, fe+xf, 7)
ax.set_xticks(MX)
ax.set_xticks(SX, minor = True)

# fix Y labels and ticks
dz =  0.1*(ze-zs)
ax.set_ylim(zs-dz, ze+dz)
MY, SY = _getTickPositions(zs-dz, ze+dz, 9)
ax.set_yticks(MY)
ax.set_yticks(SY, minor = True)

# fix grid style
ax.tick_params(axis = "both", which = "both", direction = "in")
ax.grid("on", which = "minor", linewidth = 0.3)
ax.grid("on", which = "major", linewidth = 0.6)

# set axes labels
ax.set_xlabel(f"Frequency / Hz")
ax.set_ylabel(f"Signal / {s}V")

# plot data
ax.plot(F, X, 'b.', linewidth = 0.600)
ax.plot(F, Y, 'r.', linewidth = 0.600)

# define starting parameters and fit
parSx = [32705.0, 5.0, 1.0,  2.0]
parSy = [32705.0, 5.0, 1.0, 18.0]

# parX = parSx
parX, parXC = fit(FX, F, X, p0 = parSx)
# parY = parSy
parY, parYC = fit(FY, F, Y, p0 = parSy)

# plot fits
ax.plot(F, FX(F, *parX), "--k", linewidth = 0.6)
ax.plot(F, FY(F, *parY), "--k", linewidth = 0.6)

# import header from file and export to header text
fh = open(fp, 'r')
L = fh.readlines()
fh.close()
t = ""
for l in L[:10]:
    t += l[2:]
t += f"\nrotation : {-a_deg} degrees"
headerText(t, fg)

# export fit results to footer text
t =  f"                   phase      quadrature\n\n"
t += f"position :{parX[0]:12.3f}Hz, {parY[0]:12.3f}Hz\n"
t += f"width    :{parX[1]:12.3f}Hz, {parY[1]:12.3f}Hz\n"
t += f"height   :{parX[2]:12.3f}{s}V, {parY[2]:12.3f}{s}V\n"
t += f"offset   :{parX[3]:12.3f}{s}V, {parY[3]:12.3f}{s}V\n"
footerText(t, fg)

#####################################################################

# FIGURE "XY"

fg, ax = selectfigure("XY")

# fix X labels and ticks
dx =  0.1*(xe-xs)
ax.set_xlim(xs-dx, xe+dx)
MX, SX = _getTickPositions(xs-dx, xe+dx, 7)
ax.set_xticks(MX)
ax.set_xticks(SX, minor = True)


# fix Y labels and ticks
dy =  0.1*(ye-ys)
ax.set_ylim(ys-dy, ye+dy)
MY, SY = _getTickPositions(ys-dy, ye+dy, 7)
ax.set_yticks(MY)
ax.set_yticks(SY, minor = True)

# fix grid style
ax.tick_params(axis = "both", which = "both", direction = "in")
ax.grid("on", which = "minor", linewidth = 0.3)
ax.grid("on", which = "major", linewidth = 0.6)

# set axes labels
ax.set_xlabel(f"X signal / {s}V")
ax.set_ylabel(f"Y Signal / {s}V")

# plot data
ax.plot(X, Y, 'k.')

#####################################################################

# create and export pdf document

D = Document()
D.opendocument("./display.pdf")

D.exportfigure("frequency")
# D.exportfigure("XY")

D.closedocument()
