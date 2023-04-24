# file: qtfscan.py
# create: 2023 04 24
# author: Roch Schanen

# todo: include time thread
# todo: add more device setup parameters
# todo: add setup per forks




#####################################################################

# debug

DEBUG_FLAGS = [ # all flags must be upper case
    # "ALL",
    # "GPIB",
    # "DOC"
    # "SHOWDATA",
    ]

# setup

ga = f"GPIB0::10::INSTR"
la = f"GPIB0::14::INSTR"

# scan

fp = "./TO_QTF_"
fs = 32640  # start frequency
fe = 32700  # stop frequency
fn = 100    # number of steps
ti = 300    # full time interval
dl = 3      # initial delay [fast sweep]
da = 1.000  # drive amplitude

#####################################################################

# LIBRARIES

# standard libraries
from sys import exit
from datetime import datetime
from time import sleep, time, strftime, localtime

# from package: "https://numpy.org/"
from numpy import linspace, logspace
# from numpy import ceil, floor
# from numpy import log, log10, exp
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

#                                                            # HEADER

HEADER_TEXT = ""
def writeheadertext(t):
    HEADER_TEXT += f"# {t}\n"
    return
#                                                             # DEBUG

def debug(*flags):
    for f in flags: 
        if f.upper() in DEBUG_FLAGS:
            return True
    if "ALL" in DEBUG_FLAGS:
        return True
    return False

#                                                              # VISA

import pyvisa

# get resource manager instance
rm = pyvisa.ResourceManager()
if debug("gpib"): print(rm)

# get list of all visa ressources
rs = rm.list_resources()
if debug("gpib"): print(rs)

if not ga in rs:
    print(f"failed to find instrument at generator address {ga}.")
    exit()
gh = rm.open_resource(ga)

if not la in rs:
    print(f"failed to find instrument at lockin address {la}.")
    exit()
lh = rm.open_resource(la)

def set_generator_amplitude(value):
    w = f"VOLT {value:E}V"
    if debug("gpib"): print(f"{ga} write '{w}'")
    gh.write(w)
    return

def set_generator_frequency(value):
    w = f"FREQ {value:E}HZ"
    if debug("gpib"): print(f"{ga} write '{w}'")
    gh.write(w)
    return

def set_generator_output(value):
    if value.upper() in ["ON", "1", "TRUE"]: w = f"OUTPUT ON"
    if value.upper() in ["OFF", "0", "FALSE"]: w = f"OUTPUT OFF"
    if debug("gpib"): print(f"{ga} write '{w}'")
    gh.write(w)
    return

def get_lockin_XY():
    w = f"SNAP?1,2"
    if debug("gpib"): print(f"{la} query '{w}'")
    s = lh.query(w)
    X, Y = s.strip().split(",")
    return float(X), float(Y)

#                                                            # FIGURE

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

#                                                          # DOCUMENT

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

#                                                              # time

#####################################################################

# get file time stamp
ts = strftime("%Y%m%dT%H%M%S", localtime())
# open file
fh = open(f"{fp}{ts}.dat", 'w')
# init tables
f, T, F, X, Y = fs, [], [], [], []
df, dt = (fe-fs)/(fn-1), ti/fn
# setup devices
set_generator_amplitude(da)
set_generator_frequency(f)
set_generator_output("on")
sleep(dl)
# start measurement loop
while f < fe:
    
    # set next frequency
    set_generator_frequency(f)
    
    # settling time
    sleep(dt)
    
    # acquire data
    t = time()
    x, y = get_lockin_XY()
    
    # record data
    T.append(t)
    F.append(f)
    X.append(x)
    Y.append(y)
    
    # get time stamp
    ts = datetime.now().strftime('%H:%M:%S.%f')
    
    # export data
    w = f"{ts}\t{f:.6f}\t{x:+.6E}\t{y:+.6E}\n"
    if debug("showdata"): print(w, end = "")
    fh.write(w)
    fh.flush()
    
    # export figure    
    xf =  0.1*(fe-fs)
    D = Document()
    D.opendocument("./display.pdf")
    fg, ax = selectfigure("figurename")
    ax.set_xlim(fs-xf, fe+xf)
    ax.plot(F, X, 'b.-', linewidth = 0.300)
    ax.plot(F, Y, 'r.-', linewidth = 0.300)
    D.exportfigure("figurename")
    D.closedocument()
    
    # setup next point
    f += df

# shutdown
set_generator_output("off")
fh.close()
