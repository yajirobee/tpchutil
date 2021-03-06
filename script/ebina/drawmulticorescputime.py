#! /usr/bin/env python

import sys, os, Gnuplot, sqlite3, math
import numpy as np
from plotutil import query2data

slide = False | True

def plot_multicores_cputime(dbpaths, output, terminaltype = "png"):
    gp = Gnuplot.Gnuplot()
    if terminaltype == "png":
        settermcmd = 'set terminal png font "Times-Roman, 20" size 2880,810'
    elif terminaltype == "eps":
        settermcmd = 'set terminal postscript eps color "Times-Roman, 30"'
        gp('set size 2,1')
    else:
        sys.stdout.write("wrong terminal type\n")
        sys.exit(1)
    gp(settermcmd)
    gp('set output "{0}"'.format(output))
    gp('set style fill solid border lc rgb "black"')
    #gp('set boxwidth 0.1 relative')
    gp('set logscale x 2')
    #gp('set key inside top left')
    gp('set key outside width -3')
    gp('set xrange [{min}:{max}]'.format(min = 3 * (1 << 14), max = 3 * (1 << 28)))
    gp('set yrange [0:*]')
    gp('set xlabel "work\_mem [byte]" offset 0,0.3')
    gp('set ylabel "Time [s]" offset 2')
    if terminaltype == "png":
        gp('set label 1 "1    8   64" at 51000,-8')
    elif terminaltype == "eps":
        gp('set label 1 "1      8     64" at 50000,-10 font "Times-Roman,28"')
    gp('set label 1 font "Times-Roman, 14"')
    gp('set format x "%.0b%B"')
    gp('set grid')
    keys = ("workmem", "exectime", "usr", "sys", "iowait", "irq", "soft", "idle")
    colors = ("red", "dark-magenta", "light-blue", "green", "blue", "orange")
    gds = []
    numres = len(dbpaths)
    step = 0.12
    margin = numres / 2 - 0.5 if numres % 2 == 0 else numres / 2
    for i, dbpath in enumerate(dbpaths):
        conn = sqlite3.connect(dbpath)
        maxperquery = "select max(usr + sys + iowait + idle + irq + soft) from cpu"
        maxper = int(round(conn.execute(maxperquery).fetchone()[0], -2))
        query = ("select workmem, avg(exectime) as exectime, "
                 "avg(usr) / {maxper} as usr, avg(sys) / {maxper} as sys, "
                 "avg(iowait) / {maxper} as iowait, "
                 "avg(irq) / {maxper} as irq, avg(soft) / {maxper} as soft, "
                 "avg(idle) / {maxper} as idle "
                 "from measurement, cpu "
                 "where measurement.id = cpu.id "
                 "group by workmem order by workmem"
                 .format(maxper = maxper))
        datas = query2data(conn, query)
        conn.close()
        xlist = np.array(datas[0])
        xlist *= np.exp2(step * (i - margin))
        widthlist = [v / 20 for v in xlist]
        exectimes = np.array(datas[1])
        piledatas = [np.array(datas[2])]
        for d in datas[3:]: piledatas.append(np.array(d) + piledatas[-1])
        for d in piledatas: d *= exectimes
        piledatas = [d.tolist() for d in piledatas]
        if i == 0:
            for k, dat, color in zip(keys[:0:-1], piledatas[::-1], colors):
                gds.append(Gnuplot.Data(xlist, dat, widthlist,
                                        title = k,
                                        with_ = 'boxes lc rgb "{0}" lw 1'.format(color)))
        else:
            for k, dat, color in zip(keys[:0:-1], piledatas[::-1], colors):
                gds.append(Gnuplot.Data(xlist, dat, widthlist,
                                        with_ = 'boxes lc rgb "{0}" lw 1'.format(color)))
    gp.plot(*gds)
    sys.stdout.write("output {0}\n".format(output))

if __name__ == "__main__":
    dbpaths = ["pljoin_10_{0}/spec.db".format(2 ** i) for i in range(7)]
    terminaltype = "eps"
    output = "cputimemulti.{0}".format(terminaltype)
    plot_multicores_cputime(dbpaths, output, terminaltype)
