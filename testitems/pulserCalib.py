#!/usr/bin/env python3

from iceboot.iceboot_session import getParser
import os
import sys
import numpy as np
import scope 
from addparser_iceboot import AddParser
import glob
import tables
from scipy.optimize import curve_fit
from natsort import natsorted
import matplotlib.pyplot as plt
from mkplot import plotSetting, getArrRMS


def pulserCalib(parser, path='.'):
    (options, args) = parser.parse_args()

    snum = options.mbsnum

    datapath = path + '/' + snum

    os.system('mkdir -p ' + datapath)

    modes = [1,2,3,4,6,9,12,18,36] # divisors of 36 (=48-12)
    mode = modes[1] + 1
    if int(options.dsmode) < len(modes):
        mode = modes[int(options.dsmode)] + 1

    #dacvalue = np.linspace(12,48,mode)
    #dacvalue10 = dacvalue.astype('int') * 1000 
    dacvalue = np.array([10,15,20,25,30,35,40,45,50,55,60,65])
    dacvalue10 = dacvalue * 1000

    for i in range(len(dacvalue10)):
        scope.main(parser,0,-1,path,dacvalue10[i])
        scope.main(parser,1,-1,path,dacvalue10[i])

    result, minvalues = mkplot_pc(datapath)

    return result, minvalues


def mkplot_pc(path):
    plotSetting(plt)

    plt.ion()
    plt.show()

    fig = plt.figure()
    plt.xlabel("Pulser Amplitude [LSB]",ha='right',x=1.0)
    plt.ylabel("Observed Height [LSB]",ha='right',y=1.0)

    filenames = []

    chcolors = ['blue','red']

    stackorder = 1
    for channel in range(2):

        pathdata = path + '/plscalib*ch' + str(channel) + '*.hdf5'
        filenames = glob.glob(pathdata) 

        x, y, yerr = mkDataSet(natsorted(filenames))
        popt, pcov = curve_fit(pol1, x, y, sigma=yerr)

        plt.plot(x,pol1(x,popt[0],popt[1]),ls='solid',color=chcolors[channel],zorder=stackorder)
        stackorder += 1 
        plt.errorbar(x,y,yerr,capsize=2,marker='o',ms=5,color=chcolors[channel],elinewidth=1,linewidth=0,label=f'Ch{channel}',zorder=stackorder)
        stackorder += 1
    
    plt.legend()
    fig.canvas.draw()
    plt.pause(0.001)
    plt.savefig(path+'/PlsrCalibPlot.pdf')

    return 0, 0 

def pol1(x, p0, p1):
    return p0 + p1 * np.array(x)

def mkDataSet(filenames): 
    x = []
    y = []
    yerr = []

    for i in range(len(filenames)):
        x_1,y_1,yerr_1 = getData(filenames[i])
        x.append(x_1)
        y.append(y_1)
        yerr.append(yerr_1)

    return x, y, yerr

def getData(filename):
    f = tables.open_file(filename)

    data = f.get_node('/data')
    event_ids = data.col('event_id')
    times = data.col('time')
    waveforms = data.col('waveform')

    nsamples = len(waveforms[0])

    x = int((filename.split('_')[2]).split('.')[0]) 

    y = []
    yerr = []
    for i in range(len(waveforms)):
        waveform = waveforms[i]
        baseline = np.mean(waveform[0:120])
        maxwf = max(waveform)
        y.append(maxwf - baseline)
        yerr.append(getArrRMS(waveform[0:120]))
    
    f.close()

    return x, np.mean(y), np.mean(yerr)

if __name__ == "__main__":
    parser = getParser()
    scope.AddParser(parser)
    pulserCalib(parser,'.')