# file: qtfscan.py
# create: 2023 04 24
# author: Roch Schanen

# todo: include time thread
# todo: add more device setup parameters
# todo: add setup per forks

#                                                         # LIBRARIES

# standard libraries
from sys import exit
from os import remove
from datetime import datetime
from time import sleep, time, strftime, localtime

# from package: "https://numpy.org/"
from numpy import linspace, logspace
from numpy import array

# from package: "https://matplotlib.org/"
from matplotlib.pyplot import figure, close
from matplotlib.pyplot import fignum_exists
from matplotlib.backends.backend_pdf import PdfPages

#####################################################################

#                                                             # SETUP

DEBUG_FLAGS = [ # all flags must be upper case
    # "ALL",
    # "GPIB",
    # "DOC"
    # "SHOWDATA",
    ]

# GPIB

ga = f"GPIB0::10::INSTR"
la = f"GPIB0::14::INSTR"

# SCAN

fp = "./QTF_TO_"
fs = 32640      # start frequency
fe = 32700      # stop frequency
fn = 100        # number of steps
ti = 100        # full time interval
dl = 5          # initial delay [fast sweep]
da = 1.000      # drive amplitude
at = "-20dB"    # attenuator value
gn = 1E5        # I/V gain

#####################################################################

#                                                            # HEADER

HEADER_TEXT = ""

def writeheadertext(t):
    global HEADER_TEXT
    HEADER_TEXT += f"# {t}\n"
    return

def flushheader(fh):
    fh.write(HEADER_TEXT)
    return

# get file time stamp
ts = strftime("%Y%m%dT%H%M%S", localtime())
ts = "20230425T000000"

# build filename
fpn = f"{fp}{ts}.dat"

writeheadertext(f"file         :  {fpn.split('/')[-1]}")
writeheadertext(f"start        :  {fs}Hz")
writeheadertext(f"stop         :  {fe}Hz")
writeheadertext(f"steps        :  {fn}")
writeheadertext(f"delay        :  {dl}s")
writeheadertext(f"duration     :  {ti}s")
writeheadertext(f"attenuation  :  {at}")
writeheadertext(f"gain         :  {gn:.0E}V/A")
writeheadertext(f"drive        :  {da}V")

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

def get_lockin_phase():
    w = f"PHAS?"
    if debug("gpib"): print(f"{la} query '{w}'")
    s = lh.query(w)
    P = s.strip()
    return float(P)

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
    tx.set_horizontalalignment('center')
    tx.set_verticalalignment('center')
    tx.set_fontsize("large")
    return tx

#                                                          # DOCUMENT

class Document():

    def __init__(self, pathname = None):
        if pathname is not None:
            self.opendocument(pathname)
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

# add extra configuration to data header
p = get_lockin_phase()
writeheadertext(f"phase        :  {p}deg")

# open file
fh = open(fpn, 'w')

# flush header
flushheader(fh)

# init tables
f, T, F, X, Y = fs, [], [], [], []
df, dt = (fe-fs)/(fn-1), ti/fn

# setup devices
set_generator_amplitude(da)
set_generator_frequency(f)
set_generator_output("on")
sleep(dl)

# start measurement loop
for i in range(fn):
    
    # compute next frequency set point
    f = fs+i*df

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
    w = f"{ts[:-3]}\t{f:.6f}\t{x:+.6E}\t{y:+.6E}\n"
    if debug("showdata"): print(w, end = "")
    fh.write(w)
    fh.flush()
    
    # update display figure
    xf =  0.1*(fe-fs)
    D = Document()
    D.opendocument("./display.pdf")
    fg, ax = selectfigure("fig")
    ax.set_xlim(fs-xf, fe+xf)
    ax.plot(F, X, 'b.-', linewidth = 0.300)
    ax.plot(F, Y, 'r.-', linewidth = 0.300)
    headerText(fpn, fg)
    D.exportfigure("fig")
    D.closedocument()
    # close to prevent overwriting
    close(fg)

    # setup next point
    f += df

# shutdown
set_generator_output("off")
fh.close()
