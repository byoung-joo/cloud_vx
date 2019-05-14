#from __future__ import print_function
import os
import sys
import numpy as np
import dict
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

init='2018110100'
fhrs = [6,12]
topDir = '/gpfs/fs1/scratch/schwartz/met/draft_3rd/OBS'
variable = 'binaryCloud'
obsSources = ['merra2','satcorps','era5']

######
if variable not in dict.verifVariables:
   print 'variable ',variable,'not valid. try again'
   print 'exit'
   sys.exit()
######

for fhr in fhrs:

   validTime = ( datetime.strptime(init,'%Y%m%d%H') + timedelta(hours=fhr)).strftime('%Y%m%d%H')
   julianDay = datetime.strptime(validTime,'%Y%m%d%H').strftime('%j')

   print 'Plotting',fhr,'forecast valid at',validTime

   for obsSource in obsSources:

      # Make uppercase
      obsSource = obsSource.upper().strip()

      # specifying names here temporarily. file names should be passed in to python from shell script
      if obsSource.lower().strip() == 'merra2':
         nc_file = topDir+'/MERRA2/MERRA2_400.tavg1_2d_'+validTime[0:8]+'_'+validTime[8:10]+'30.nc4' # MERRA2_400.tavg1_2d_20181115_0630.nc4
      elif obsSource.lower().strip() == 'satcorps':
         nc_file = topDir+'/SATCORPS/GEO-MRGD.'+validTime[0:4]+julianDay+'.'+validTime[8:10]+'00.GRID.NC' # GEO-MRGD.2018316.0300.GRID.NC
      elif obsSource.lower().strip() == 'era5':
         nc_file = topDir+'/ERA5/ERA5_'+validTime+'.nc' # ERA5_2018111100.nc

      # Open the file
      nc_fid = Dataset(nc_file, "r", format="NETCDF4") #Dataset is the class behavior to open the file
      #nc_fid.set_auto_scale(True)

      # Get lat/lon/time information--currently not used
      latVar = dict.obsDatasets[obsSource]['latVar']
      lonVar = dict.obsDatasets[obsSource]['lonVar']
      lats = np.array(nc_fid.variables[latVar][:])   # extract/copy the data
      lons = np.array(nc_fid.variables[lonVar][:] )
      #print lats.max()
      #print lons.max()

      # one way to deal with scale factors
      # probably using something like nc_fid.set_auto_scale(True) is better...
      latMax = lats.max()
      while latMax > 90.0:
	 lons = lons * 0.1
	 lats = lats * 0.1
	 latMax = lats.max()

      data = dict.getDataArray(nc_file,nc_file,obsSource,variable,validTime)

      # Make plotting optional or Just use plot_data_plane
   #  plt_data=np.where(met_data<0, np.nan, met_data)
      map=Basemap(projection='cyl',llcrnrlat=-90,urcrnrlat=90,llcrnrlon=-180,urcrnrlon=180,resolution='c')
      map.drawcoastlines()
      map.drawcountries()
      map.drawparallels(np.arange(-90,90,30),labels=[1,1,0,1])
      map.drawmeridians(np.arange(0,360,60),labels=[1,1,0,1])
      plt.contourf(lons,lats,data,20,origin='upper',cmap=cm.Greens) #cm.gist_rainbow)
      title=obsSource+"_"+variable+"_"+init+'_f'+'%03d'%fhr
      plt.title(title)
      plt.colorbar(orientation='horizontal')
      plt.savefig(title+".png")
      plt.clf()

