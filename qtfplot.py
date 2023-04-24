# file: qtfscan.py
# create: 2023 04 24
# author: Roch Schanen

#####################################################################

# LIBRARIES

# standard libraries
from sys import exit
from time import sleep, time, strftime, localtime
from datetime import datetime

# from package: "https://numpy.org/"
from numpy import linspace, logspace
from numpy import ceil, floor
from numpy import log, log10, exp
# from numpy import full
# from numpy import copy
# from numpy import diff
from numpy import array
# from numpy import invert
# from numpy import arange
# from numpy import asarray
# from numpy import gradient
# from numpy import meshgrid
# from numpy import sum as SUM
# from numpy import multiply as MLT
# from numpy.random import rand

# from package "https://python-pillow.org/"
# from PIL import Image
# from PIL import ImageDraw

# from package "https://scipy.org/"
# from scipy.constants import epsilon_0 as EPS0

# from package: "https://matplotlib.org/"
# from matplotlib.pyplot import sca
# from matplotlib.pyplot import Circle
from matplotlib.pyplot import figure
# from matplotlib.pyplot import Rectangle
from matplotlib.pyplot import fignum_exists
# from matplotlib.pyplot import cm
from matplotlib.backends.backend_pdf import PdfPages

DEBUG_FLAGS = []

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
    tx = fg.text(x+w/2, 3*y/2+h, text)
    tx.set_fontfamily('monospace')
    tx.set_horizontalalignment('centre')
    tx.set_verticalalignment('centre')
    tx.set_fontsize('large')
    return tx

def footerText(text, fg):
    w, h = array([1, 1 / 1.4143])*0.7
    x, y = (1-w)/2, (1-h)/2
    tx = fg.text(x+w/2, y/2, text)
    tx.set_fontfamily('monospace')
    tx.set_horizontalalignment('centre')
    tx.set_verticalalignment('centre')
    tx.set_fontsize('large')
    return tx

def _getTickPositions(start, stop, ticks):

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

#####################################################################

fp = "./TO_QTF_20230424T135609.dat"

from numpy import loadtxt

# s = "13:56:15.659472"

def seconds(s):
    t =  float(s[0:2])*3600
    t += float(s[3:5])*60
    t += float(s[6: ])*1
    return t

codic = {
    0: seconds,
    1: float,
    2: float,
    3: float,
}

data = loadtxt(fp, converters = codic)

T = data[:, 0]
F = data[:, 1]
X = data[:, 2]
Y = data[:, 3]

D = Document()
D.opendocument("./display.pdf")
fg, ax = selectfigure("displayfigure")

fs, fe = min(F), max(F)
xf =  0.1*(fe-fs)
ax.set_xlim(fs-xf, fe+xf)
MX, SX = _getTickPositions(fs-xf, fe+xf, 7)
ax.set_xticks(MX)
ax.set_xticks(SX, minor = True)
ax.tick_params(axis = "both", which = "both", direction = "in")
ax.grid("on", which = "minor", linewidth = 0.3)
ax.grid("on", which = "major", linewidth = 0.6)

# xs, xe = min(X), max(X)
# ys, ye = min(Y), max(Y)

# xf =  0.1*(fe-fs)
# ax.set_xlim(fs-xf, fe+xf)
# MX, SX = _getTickPositions(fs-xf, fe+xf, 7)
# ax.set_xticks(MX)
# ax.set_xticks(SX, minor = True)
# ax.tick_params(axis = "both", which = "both", direction = "in")
# ax.grid("on", which = "minor", linewidth = 0.3)
# ax.grid("on", which = "major", linewidth = 0.6)

ax.plot(F, X, 'b.-', linewidth = 0.600)
ax.plot(F, Y, 'r.-', linewidth = 0.600)

D.exportfigure("displayfigure")
D.closedocument()

