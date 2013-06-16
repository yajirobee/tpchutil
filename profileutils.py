#! /usr/bin/env python

import sys, os, re, glob
import numpy as np

def get_mdioprof(fpath, devname):
    ioprof = []
    comppat = re.compile(r'fio[a-h]')
    tmp = None
    comp = []
    for line in open(fpath):
        val = line.split()
        if not val:
            if tmp:
                if comp:
                    ave = comp[0]
                    for arr in comp[1:]: ave += arr
                    for i in range(6, ave.size): ave[i] /= len(comp)
                    tmp[:2] = ave[:2]
                    tmp[6:] = ave[6:]
                    comp = []
                tmp[4] *= 512 * (10 ** -6) # convert read throughput from sec/s to MB/s
                tmp[5] *= 512 * (10 ** -6) # convert write throughput from sec/s to MB/s
                ioprof.append(tmp)
                tmp = None
        elif val[0] == devname:
            tmp = [float(v) for v in val[1:]]
        elif comppat.match(val[0]):
            comp.append(np.array([float(v) for v in val[1:]]))
    return ioprof

def get_normioprof(fpath, devname):
    ioprof = []
    for line in open(fpath):
        val = line.split()
        if not val: continue
        elif val[0] == devname:
            tmp = [float(v) for v in val[1:]]
            tmp[4] *= 512 * (10 ** -6) # convert read throughput from sec/s to MB/s
            tmp[5] *= 512 * (10 ** -6) # convert write throughput from sec/s to MB/s
            ioprof.append(tmp)
    return ioprof

def get_ioprof(fpath, devname):
    "get histgram of IO profile"
    if devname == "md0": return get_mdioprof(fpath, devname)
    else: return get_normioprof(fpath, devname)

def get_cpuprof(fpath, core):
    "get histgram of a CPU core usage"
    cpuprof = []
    for line in open(fpath):
        val = line.split()
        if not val:
            continue
        elif val[1] == core:
            cpuprof.append([float(v) for v in val[2:]])
    return cpuprof

def get_allcpuprof(fpath, col):
    "get histgram of one column of all CPU cores usage"
    datepat = re.compile(r"\d{2}:\d{2}:\d{2}")
    floatpat = re.compile(r"\d+(?:\.\d*)?|\.\d+")
    utilhist = []
    util = 0.
    date = None
    for line in open(fpath):
        val = line.split()
        if not val or val[1] == "all" or val[1] == "CPU":
            continue
        elif date != val[0] and datepat.search(val[0]):
            if date: utilhist.append(util)
            date = val[0]
            util = 0.
        if floatpat.search(val[col]):
            tmp = float(val[col])
            if tmp > 2.0: util += tmp
    return utilhist

def get_reliddict(relidfile):
    "get relid dictionary"
    reliddict = {0 : "temporary"}
    for line in open(relidfile):
        vals = [v.strip() for v in line.split('|')]
        if len(vals) != 2 or not vals[0].isdigit(): continue
        else: reliddict[int(vals[0])] = vals[1]
    return reliddict

def get_tblrefprof(iodumpfile):
    "get histgram of each table reference counts"
    refhist = []
    with open(iodumpfile) as fo:
        line = fo.readline()
        vals = line.split()
        stime = int(vals[0], 16)
        elapsed = 0
        refdict = {int(vals[5], 16) : 1}
        for line in fo:
            vals = line.split()
            time = (int(vals[0], 16) - stime) / 1000 ** 3
            if time == elapsed:
                relname = int(vals[5], 16)
                if relname in refdict: refdict[relname] += 1
                else: refdict[relname] = 1
            else:
                assert(time > elapsed)
                for i in range(time - elapsed):
                    refhist.append(refdict)
                    refdict = {}
                refdict[int(vals[5], 16)] = 1
                elapsed = time
    return refhist

def get_iocostprof(fpath):
    readiocount, writeiocount, readiotime, writeiotime, readioref = range(5)
    iohist = [[0, 0, 0, 0, {}]]
    interval = 10 ** 9
    prevstate = None
    for line in open(fpath):
        val = line.strip().split()
        if not val:
            continue
        if 'r' == val[1] or 'w' == val[1]:
            if val[1] == prevstate:
                sys.stderr.write("bat IO sequence : line {0}\n".format(i))
                sys.exit(1)
            stime = int(val[0], 16)
            for i in range(stime / interval - (len(iohist) - 1)):
                iohist.append([0, 0, 0, 0, {}])
            idx = readiocount if 'r' == val[1] else writeiocount
            iohist[-1][idx] += 1
            if 'r' == val[1]:
                if int(val[2], 16) in iohist[-1][readioref]:
                    iohist[-1][readioref][int(val[2], 16)] += 1
                else:
                    iohist[-1][readioref][int(val[2], 16)] = 1
        elif 'R' == val[1] or 'W' == val[1]:
            if (val[1].lower() != prevstate) or (int(val[3], 16) != prevblock):
                sys.stderr.write("bat IO sequence : line {0}\n".format(i))
                sys.exit(1)
            ftime = int(val[0], 16)
            idx = readiotime if 'R' == val[1] else writeiotime
            while stime / interval < ftime / interval:
                iohist[-1][idx] += len(iohist) * interval - stime
                stime = len(iohist) * interval
                iohist.append([0, 0, 0, 0, {}])
            iohist[-1][idx] += ftime - stime
        prevstate = val[1]
        prevblock = int(val[3], 16)
    return iohist

def get_cacheprof(fpath, corenum):
    cachehist = []
    t = 0
    interval = 5
    cycles, cacheref, cachemiss = 0, 0, 0
    corepat = "CPU{0}".format(corenum)
    for line in open(fpath):
        vals = line.strip().split()
        if not vals or len(vals) < 3: continue
        elif corepat == vals[0]:
            if "cycles" == vals[2]: cycles = int(vals[1])
            elif "cache-references" == vals[2]: cacheref = int(vals[1])
            elif "cache-misses" == vals[2]: cachemiss = int(vals[1])
        elif "time" == vals[2] and "elapsed" == vals[3]:
            cachehist.append((t, cycles, cacheref, cachemiss))
            t += interval
            cycles, cacheref, cachemiss = 0, 0, 0
    return cachehist
