#from __future__ import print_function
import os
import sys
import numpy as np
from datetime import *
from netCDF4 import Dataset  # http://code.google.com/p/netcdf4-python/
#### for Plotting
import matplotlib.cm as cm
import matplotlib.axes as maxes
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.basemap import Basemap
import fnmatch
#####

###########################################

fhrs = list(range(24,192+1,24))
topDir = '/glade/scratch/schwartz/cloud_vx/metprd/exp_EnVar_6h_cyc_updatedTiedtkeForcing/aggregation'
#variable = 'totalCloudFrac'
#obsSources = ['ERA5']

experiments = [topDir]

metric = 'GSS' # this needs to be in the .stat file. If not, code will fail

#thresholds = [40.0, 50.0, 60.0 ]
thresholds = [ 'SFP20', 'SFP30', 'SFP40']

######
nexpts = len(experiments)
nfhrs = len(fhrs)
nthreshs = len(thresholds)

fake_x = np.arange(0,nfhrs,1)

######

fig, axs = plt.subplots( nthreshs, 1, sharex=True)

for t, thresh in enumerate(thresholds):

   for i, expt in enumerate(experiments):

      plot_data = []
      for fhr in fhrs:

         fname = '%s/f%d/totalCloudFrac/ERA5/aggregate_stats_f%03d_thresh_%s.txt'%(expt,fhr,fhr,str(thresh))
         if not os.path.exists(fname):
            print(fname+" is missing. exit")
            sys.exit()
         print("Reading "+fname)

         fin = open(fname,'r')
         lines = fin.readlines() # read all the lines; 1st line we don't need; 2nd is headers; 3rd is data
         headers = lines[1].split() # using split without an argument ignores the amount of white space between strings
         data    = lines[2].split() # using split without an argument ignores the amount of white space between strings
         fin.close()

         # can loop over the metrics here and store data
         try:
           #e.g., col = headers.index('GSS')
           col = headers.index(metric.upper()) # column in the file for the metric we chose
         except:
            print('GSS not in headers')
            print(headers)
            sys.exit()

         my_score = data[col]
         plot_data.append(my_score)

      ax = axs[t]
      ax.plot(fake_x,plot_data)
      ax.set_xticks(fake_x)
      ax.set_xticklabels(fhrs)
      ax.set_xlabel('Forecast hour')
      ax.set_ylabel(metric.upper())
      if thresh == thresholds[-1]: ax.set_title(thresh) # just set title the last time through loop

fig.tight_layout()
fig.savefig('test.pdf',type='pdf')

