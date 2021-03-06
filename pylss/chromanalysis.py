'''
@package chromanalysis

chromanalysis was writen by Giuseppe Marco Randazzo <gmrandazzo@gmail.com>
Geneve January 2017

chromanalysis will analyse a chromatogram to convert this into descriptors.

Actually it contains some algorithms such as:

- Peak detection algorithm accordin the Peak-Valley Segmentation Algorithm
  [1] Reference: Eamonn J. Keogh, Selina Chu, David Hart, and Michael J. Pazzani.
  An online algorithm for segmenting time series.
  In Proceedings of the 2001 IEEE International Conference on Data Mining,
  ICDM ’01, pages 289–296, Washington, DC, USA, 2001. IEEE Computer Society.

  [2] Z. M. Nopiah, M. I. Khairir, S. Abdullah, and C. K. E. Nizwan.
  Peak-valley segmentation algorithm for fatigue time series data.
  WSEAS Trans. Math., 7:698–707, December 2008.

- Central moments calculation to describe the band broadeing (Band variance: u1, u2)
- Integration of the peak

'''

import decimal
from miscalgoritms import *

from math import sqrt, fabs
from os.path import isfile, basename

class ChromAnalysis(object):
    """ Chromatogram Analysis class """
    def __init__(self, time, signal, k=5, h=1.5):
        """ init function """
        self.time = time
        self.signal = signal
        # peak detection settings
        self.k = k
        self.h = h

    def S1(self, x, i, k):
        """ Peak function S1 """
        left = 0.
        for j in range(1, k+1):
            if x[i] - x[i-j] > left:
                left = x[i] - x[i-j]
            else:
                continue

        right = 0.
        for j in range(1, k+1):
            if x[i] - x[i+j] > right:
                right = x[i] - x[i+j]
            else:
                continue
        return (left + right) / 2.

    def S2(self, x, i, k):
        """ Peak function S2 """
        avg_left = 0.
        for j in range(1, k+1):
            avg_left += x[i] - x[i-j]
        avg_left /= float(k)

        avg_right = 0.
        for j in range(1, k+1):
            avg_right = x[i] - x[i+j]
        avg_right /= float(k)
        return (avg_left + avg_right) / 2.

    def S3(self, x, i, k):
        """ Peak function S3 """
        left = 0.
        for j in range(1, k+1):
            left +=  x[i-j]
        left /= float(k)
        left = x[i] - left

        right = 0.
        for j in range(1, k+1):
            right = x[i+j]
        right /= float(k)
        right = x[i] - right
        return (left + right) / 2.

    def getPeaks(self):
        """ Method to find peaks in chromatograms
        The algorithm implemented is the Peak-Valley algorithm
        """
        peaks = []
        #default values
        #h = 1
        #k = 5
        a = []
        for i in range(self.k, len(self.signal)-self.k):
            a.append(self.S1(self.signal, i, self.k))
            #a.append(self.S2(self.signal, i, self.k))
            #a.append(self.S3(self.signal, i, self.k))

        #Calculate the mean of only positive value of a
        n = 0
        mean = 0.
        for i in range(len(a)):
            if a[i] > 0:
                mean += a[i]
                n += 1
            else:
                continue
        mean /= float(n)

        #Calculate the standard deviation of only positive value of a
        stdev = 0.
        for i in range(len(a)):
            if a[i] > 0:
                x = (a[i] - mean)
                stdev += x*x
            else:
                continue

        stdev = sqrt(stdev/float(n-1))

        # detect the peaks
        pnlst = []
        for i in range(len(a)):
            #if a[i] > 0 and (a[i] - mean) > (self.h*stdev):
            if a[i] > 0 and a[i] > (mean+ self.h*stdev):
                pnlst.append(i)
                peaks.append([self.time[i+self.k], self.signal[i+self.k]])
            else:
                pnlst.append(i)
                peaks.append([self.time[i+self.k], 0.])

        return peaks

    def addLeftNpoints(self, peak, npnt=5):
        if npnt == 0:
            return
        else:
            tmin = peak[0][0]
            for i in range(len(self.signal)):
                if fabs(self.time[i]-tmin) < 1e-6:
                    npnt_ = npnt
                    if i-npnt_ < 0:
                        while i - npnt < 0:
                            npnt_ -= 1
                    for j in range(i-npnt_, i):
                        peak.insert(0, [self.time[j], self.signal[j]])
                else:
                    continue
            peak = sorted(peak,key=lambda l:l[0])

    def addRighNpoints(self, peak, npnt=5):
        if npnt == 0:
            return
        else:
            tmax = peak[-1][0]
            for i in range(len(self.time)):
                if fabs(self.time[i]-tmax) < 1e-6:
                    npnt_ = npnt
                    if i+npnt_ > len(self.time):
                        while i + npnt_ > len(self.time):
                            npnt_ -= 1

                    for j in range(i, i+npnt_):
                        peak.append([self.time[j], self.signal[j]])
                else:
                    continue
            peak = sorted(peak,key=lambda l:l[0])

    def peaksplit(self, signal):
        """ Method to split the peaks identified by getPeask() """
        peaklst = []
        p = [] # peak
        #pnlst = []
        #pn = [] # number in peak
        for i in range(len(signal)):
            if signal[i][-1] > 0:
                p.append(signal[i])
                #pn.append(i)
            else:
                if len(p) > 0:
                #    pnlst.append([])
                    peaklst.append([])
                    for row in p:
                        peaklst[-1].append(row)
                #    for row in pn:
                #        pnlst[-1].append(row)
                    del p[:]
                #    del pn[:]
                else:
                    continue

        #TODO: Remove adjacet peaks within window size < k

        return peaklst

    def Mu1CentralMoment(self, time_, signal_):
        """ Method to calculate the first moment """
        n = 0.
        d = 0.
        for i in range(len(time_)-1):
            n += (signal_[i]+signal_[i+1])*(time_[i]+time_[i+1])
            d += (signal_[i]+signal_[i+1])
        if d != 0.:
            return n/(2*d)
        else:
            return 0.

    def Mu2CentralMoment(self, time_, signal_, u1_):
        """ Method to calculate the second moment """
        if u1_ == 0 or u1_ == None:
            self.Mu1CentralMoment(time_, signal_)

        n = 0.
        d = 0.
        for i in range(len(time_)-1):
            n += (signal_[i]+signal_[i+1])*(((time_[i]+time_[i+1])/2.) - u1_)**2
            d += (signal_[i]+signal_[i+1])
        if d != 0.:
            return n/d
        else:
            return 0.

    def integrate(self, y_vals, h):
        """ Method to integrate according the simson rules """
        i=1
        total = y_vals[0] + y_vals[-1]
        for y in y_vals[1:-1]:
            if i%2 == 0:
                total+=2*y
            else:
                total+=4*y
            i+=1
        return total*(h/3.0)

def demo():
    """ Demo """
    signal = [ 1. ,  1. ,  1. ,  1. ,  1. ,  1. ,  1. ,  1.1,  1. ,  0.8,  0.9,
    1. ,  1.2,  0.9,  1. ,  1. ,  1.1,  1.2,  1. ,  1.5,  1. ,  3. ,
    2. ,  5. ,  3. ,  2. ,  1. ,  1. ,  1. ,  0.9,  1. ,  1. ,  3. ,
    2.6,  4. ,  3. ,  3.2,  2. ,  1. ,  1. ,  1. ,  1. ,  1. ]

    time = [1, 2, 3, 4, 5, 6, 7, 88, 9, 10, 11,
    12, 13, 14, 15, 16, 17, 18, 19, 20, 21 ,22,
    23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33,
    34, 35, 36, 37, 38, 39, 40, 41, 42, 43]

    chrom = ChromAnalysis(time, signal, k=4, h=1.5)
    peaks = chrom.getPeaks()
    peaklst = chrom.peaksplit(peaks)

    for p in peaklst:
        for row in p:
            print ("%f\t%f" % (row[0], row[1]))
        print("-"*10)

if __name__ == '__main__':
    demo()
