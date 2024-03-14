#from __future__ import print_function
import os
import sys
import numpy as np
#import datetime as dt
from netCDF4 import Dataset  # http://code.google.com/p/netcdf4-python/
#### for Plotting
#import matplotlib.cm as cm
#import matplotlib.axes as maxes
import matplotlib.pyplot as plt
#from mpl_toolkits.axes_grid1 import make_axes_locatable
#from mpl_toolkits.basemap import Basemap
import fnmatch
#import pygrib
#####

###########################################

#inputDir = '/glade/scratch/jban/pandac/120km_freerun_new1/OMF/2018050300/1/Data'
#inputDir = '/glade/scratch/wuyl/test2/pandac/test_120km/OMF_cyc6h/noAHI/2018050300/1/Data'
inputDir = '/glade/scratch/guerrett/pandac/120km_3denvar_conv_clramsua_cldabi/VF/bg/2018042100/Data'
satellite = 'abi_g16'
channels = [8,9,10]
colors = ['r-','b-','k']

##############################################

# Get list of files.  There is one file per processor
files = os.listdir(inputDir)
inputFiles = fnmatch.filter(files,'ydiag*'+satellite+'*nc4') # returns relative path names
inputFiles = [inputDir+'/'+s for s in inputFiles] # add on directory name

geovalFiles = fnmatch.filter(files,'geoval*'+satellite+'*nc4') # returns relative path names
geovalFiles = [inputDir+'/'+s for s in geovalFiles] # add on directory name

obsoutFiles = fnmatch.filter(files,'obsout*'+satellite+'*nc4') # returns relative path names
obsoutFiles = [inputDir+'/'+s for s in obsoutFiles] # add on directory name

if len(geovalFiles) != len(inputFiles) != len(obsoutFiles):
   print('unequal files. exit')
   sys.exit()

# Initialize figure up here
fig, (ax,ax2) = plt.subplots(1,2,sharey=True)

# Loop over files and max plots
for j, inputFile in enumerate(inputFiles):

   nc_fid = Dataset(inputFile, "r", format="NETCDF4") 
   nc_fid2 = Dataset(geovalFiles[j], "r", format="NETCDF4") 
   nc_fid3 = Dataset(obsoutFiles[j], "r", format="NETCDF4") 

   # get pressures
   pressures = np.array(nc_fid2.variables['air_pressure'])*0.01 # get into hPa...pressure from background
   pressures = pressures.astype('int')
   nlocs = pressures.shape[0]
   nlevs = pressures.shape[1]
   yvals = np.arange(0,nlevs,1)

   # get cloud fraction from background--same dimensions as pressure
   cldfraFcst = np.array(nc_fid2.variables['cloud_area_fraction_in_atmosphere_layer'])*100.0 # get into percent
   qcloud = np.array(nc_fid2.variables['mass_content_of_cloud_liquid_water_in_atmosphere_layer'])
   qice   = np.array(nc_fid2.variables['mass_content_of_cloud_ice_in_atmosphere_layer'])
   qtot   = (qice + qcloud) # already in g/kg???

   # get cloud fraction from obs--same dimensions as pressure
   cldfraObs = np.array(nc_fid3.variables['cloud_area_fraction@MetaData'])*100.0 # get into percent

   weightingFunction = [] # ith element will be a numpy array for ith channel
   weightingFunctionPMax = [] 
   clearSkyRad = [] 
   allSkyRad   = [] 
   for channel in channels:

      # get weighting function profile
      v = 'weightingfunction_of_atmosphere_layer_'+str(channel)
      print('Trying to read ',v,' from ',inputFile)
      read_var = np.array(nc_fid.variables[v])
      weightingFunction.append(read_var)

      # get pressure at peak of weighting function
      v = 'pressure_level_at_peak_of_weightingfunction_'+str(channel) 
      weightingFunctionPeak = np.array(nc_fid.variables[v]).astype('int') # this is the INDEX of the max pressure level
      weightingFunctionPMax.append(weightingFunctionPeak)

      # get clear-sky radiance
      v = 'brightness_temperature_assuming_clear_sky_'+str(channel)
      read_var = np.array(nc_fid.variables[v])
      clearSkyRad.append(read_var)

      # get all-sky radiance
      v1 = 'brightness_temperature_'+str(channel)+'@ObsValue'
      v2 = 'brightness_temperature_'+str(channel)+'@depbg'
      read_var = np.array(nc_fid3.variables[v1]) - np.array(nc_fid3.variables[v2])
      allSkyRad.append(read_var)

   for i in range(0,nlocs,10): # only plot every 10th profile
      print('about to plot for i = ',i)
      for c, channel in enumerate(channels):
         weightMaxIdx = weightingFunctionPMax[c][i]-1 # subtract 1 because indices start at 0
         pres = pressures[i,weightMaxIdx]
         labelString = 'channel '+str(channel)+': peak = '+str(pres)+' hPa'
         this_var = weightingFunction[c]
         ax.plot(np.flip(this_var[i,:],axis=0),yvals,colors[c],label=labelString) # flip because index 0 is top of model, and we want it to be bottom

        #clearBT  = clearSkyRad[c]
        #allSkyBT = allSkyRad[c]
        #diff = clearBT[i] - allSkyBT[i]
        #print(diff)

      ax.set_xlabel('Weighting function')
      ax.set_ylabel('Pressure (hPa)')
      ax.set_yticks( yvals[0::2])
      ax.set_yticklabels(np.flip(pressures[i,0::2],axis=0)) # flip because index 0 is top of model, and we want it to be bottom
     #ax.title.set_text( 'Peak is %s hPa'%(pres) )
      ax.grid(True)
      ax.legend()

     #ax2.plot(np.flip(qtot[i,:],axis=0),yvals,'k-')
     #ax2.plot(np.flip(qcloud[i,:],axis=0),yvals,'k-',label='qcloud')
     #ax2.plot(np.flip(qice[i,:],axis=0),yvals,'r-',label='qice')
      ax2.plot(np.flip(cldfraFcst[i,:],axis=0),yvals,'k-',label='cldfraFcst')
      ax2.plot(cldfraObs[i],yvals[30],'ro',label='cldfraObs')
     #ax2.set_xlabel('Total cloud (g/kg)')
      ax2.set_xlabel('Cloud fraction (%)')
      ax2.grid(True)
      ax2.legend()
     #ax2.set_ylabel('Pressure (hPa)')
     #ax2.set_yticks( yvals[0::2])
     #ax2.set_yticklabels(np.flip(pressures[i,0::2],axis=0)) # flip because index 0 is top of model, and we want it to be bottom

      for this_ax in [ax,ax2]:
         this_ax.label_outer()

      # save the figure
      outname = satellite+'_profile_'+str(i)+'.pdf'
      fig.savefig(outname,format='pdf')

      # clear axes so next time through we're not just adding lines
      ax.clear()
      ax2.clear()

   sys.exit() # no need to loop over more than 1 file. 
