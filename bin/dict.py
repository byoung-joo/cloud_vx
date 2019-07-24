#from __future__ import print_function
import os
import sys
import numpy as np
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

missing_values = -9999.0  # for MET

obsDatasets =  {
   'MERRA2'   : { 'gridType':'LatLon',   'latVar':'lat',     'latDef':[-90.0,0.50,361], 'lonVar':'lon',       'lonDef':[-180.0,0.625,576],   'flipY':True, },
   'SATCORPS' : { 'gridType':'LatLon',   'latVar':'latitude','latDef':[-90.0,0.25,721], 'lonVar':'longitude', 'lonDef':[-180.0,0.3125,1152], 'flipY':False, },
   'ERA5'     : { 'gridType':'LatLon',   'latVar':'latitude','latDef':[-89.7848769072,0.281016829130516,640], 'lonVar':'longitude', 'lonDef':[0.0,0.28125,1280],   'flipY':False, },
   #TODO:Correct one, but MET can ingest a Gaussia grid only in Grib2 format (from Randy B.)
   #'ERA5'     : { 'gridType':'Gaussian', 'nx':1280, 'ny':640, 'lon_zero':0, 'latVar':'latitude', 'lonVar':'longitude', 'flipY':False, },
}

verifVariables = {
   'binaryCloud'    : { 'MERRA2':['CLDTOT'], 'SATCORPS':['cloud_percentage_level'],      'ERA5':['TCC'], 'thresholds':'>=0.0', 'interpMethod':'nearest' },
   'totalCloudFrac' : { 'MERRA2':['CLDTOT'], 'SATCORPS':['cloud_percentage_level'],      'ERA5':['TCC'], 'thresholds':'<10.0, >=10.0, >=20.0, >=30.0, >=40.0, >=50.0, >=60.0, >=70.0, >=80.0, >=90.0', 'interpMethod':'bilin' },
   'lowCloudFrac'   : { 'MERRA2':['CLDLOW'], 'SATCORPS':['cloud_percentage_level'],      'ERA5':['LCC'], 'thresholds':'<10.0, >=10.0, >=20.0, >=30.0, >=40.0, >=50.0, >=60.0, >=70.0, >=80.0, >=90.0', 'interpMethod':'bilin' },
   'midCloudFrac'   : { 'MERRA2':['CLDMID'], 'SATCORPS':['cloud_percentage_level'],      'ERA5':['MCC'], 'thresholds':'<10.0, >=10.0, >=20.0, >=30.0, >=40.0, >=50.0, >=60.0, >=70.0, >=80.0, >=90.0', 'interpMethod':'bilin' },
   'highCloudFrac'  : { 'MERRA2':['CLDHGH'], 'SATCORPS':['cloud_percentage_level'],      'ERA5':['HCC'], 'thresholds':'<10.0, >=10.0, >=20.0, >=30.0, >=40.0, >=50.0, >=60.0, >=70.0, >=80.0, >=90.0', 'interpMethod':'bilin' },
   'cloudTopTemp'   : { 'MERRA2':['CLDTMP'], 'SATCORPS':['cloud_temperature_top_level'], 'ERA5':['']   , 'thresholds':'NA', 'interpMethod':'bilin'},
   'cloudTopPres'   : { 'MERRA2':['CLDPRS'], 'SATCORPS':['cloud_pressure_top_level'],    'ERA5':['']   , 'thresholds':'NA', 'interpMethod':'bilin'},
}

# to read in an environmental variable
#x = os.getenv('a') # probably type string no matter what

###########

def getThreshold(variable):
   x = verifVariables[variable]['thresholds']
   return x

def getInterpMethod(variable):
   x = verifVariables[variable]['interpMethod'].upper()
   return x

def getTotalCloudFrac(source,data):
   if source == 'SATCORPS':
      x = data[0][0,:,:,0] * 1.0E-2  # scaling
   #  y = data[0]
   #  x = np.sum( y[:,:,:,1:4],axis=3)
   elif source == 'MERRA2':
#      x = ( data[0][0,:,:]+data[1][0,:,:]+data[2][0,:,:] ) *100.0 # the ith element of data is a numpy array
      x = data[0][0,:,:] * 100.0 # the ith element of data is a numpy array
      print x.min(), x.max()
   elif source == 'ERA5':
      x = data[0][0,0,:,:] * 100.0

   # This next line is WRONG.
   # Missing should be set to missing
   # Then, the non-missing values are 1s and 0s
   #output = np.where(x > 0.0, x, 0.0)
   #output = np.where(x < 0.0, -9999.0, x) # missing. currently used for SATCORPS
   return x

def getBinaryCloud(source,data):
   y = getTotalCloudFrac(source,data)
   # keep NaNs as is, but then set everything else to either a 1 or 0
   x = np.where( np.isnan(y), y, np.where(y > 0.0, 1.0, 0.0) )
   return x

def getLayerCloudFrac(source,data,layer):
   if source == 'SATCORPS':
      if layer.lower().strip() == 'low'  : i = 1
      if layer.lower().strip() == 'mid'  : i = 2
      if layer.lower().strip() == 'high' : i = 3
      x = data[0][0,:,:,i] * 1.0E-2  # scaling
   elif source == 'MERRA2':
      x = data[0][0,:,:] * 100.0
   elif source == 'ERA5':
      x = data[0][0,0,:,:] * 100.0
   return x

def getCloudTopTemp(source,data):
   if source == 'SATCORPS':
      x = data[0][0,:,:,0] * 1.0E-2  # scaling
   elif source == 'MERRA2':
      x = data[0][0,:,:] 
   elif source == 'ERA5':
      x = data[0][0,0,:,:]
   return x

def getCloudTopPres(source,data):
   if source == 'SATCORPS':
      x = data[0][0,:,:,0] * 1.0E-1  # scaling
   elif source == 'MERRA2':
      x = data[0][0,:,:] * 1.0E-2  # scaling [Pa] -> [hPa]
   elif source == 'ERA5':
      x = data[0][0,0,:,:]
   return x

# add other functions for different variables

###########

def getDataArray(fcstFile,obsFile,obsSource,variable,validTime):
   ## Ideally, pass 5 pieces of information to python:
   # 1) Forecast file name
   # 2) Observations file name
   # 3) Obsevation source (e.g., MERRA, SATCORP, etc.)
   # 4) Variable to verify
   # With these 5 pieces of information, everything else
   # is probably derivable within this script

#   # specifying names here temporarily. file names should be passed in to python from shell script
#   if obsSource == 'merra':
#      nc_file = '/gpfs/fs1/scratch/schwartz/MERRA/MERRA2_400.tavg1_2d_rad_Nx.20181101.nc4'
#   elif obsSource == 'satcorp':
#      nc_file = '/glade/scratch/bjung/met/test_satcorps/GEO-MRGD.2018334.0000.GRID.NC'
#   elif obsSource == 'era5':
#      nc_file = '/glade/scratch/bjung/met/test_era5/e5.oper.fc.sfc.instan.128_164_tcc.regn320sc.2018111606_2018120112.nc'

   obsSource = obsSource.upper().strip()  # Force uppercase and get rid of blank spaces, for safety

   nc_file=obsFile
   print 'Trying to read ',nc_file

   # Open the file
   nc_fid = Dataset(nc_file, "r", format="NETCDF4") #Dataset is the class behavior to open the file
   #nc_fid.set_auto_scale(True)

   # Get lat/lon information--currently not used
  #latVar = obsDatasets[obsSource]['latVar']
  #lonVar = obsDatasets[obsSource]['lonVar']
  #lats = np.array(nc_fid.variables[latVar][:])   # extract/copy the data
  #lons = np.array(nc_fid.variables[lonVar][:] )

   #print lats.max()
   #print lons.max()

   # one way to deal with scale factors
   # probably using something like nc_fid.set_auto_scale(True) is better...
  #latMax = lats.max()
  #while latMax > 90.0:
  #   lons = lons * 0.1
  #   lats = lats * 0.1
  #   latMax = lats.max()

   # get data
   data = []
   varsToRead = verifVariables[variable][obsSource] # returns a list
   for v in varsToRead:
      print 'Reading ', v
      read_var = nc_fid.variables[v]         # extract/copy the data
      read_missing = read_var.missing_value  # get variable attributes. Each dataset has own missing values.
      this_var = np.array( read_var )        # to numpy array
     #print read_missing, np.nan
      this_var = np.where( this_var==read_missing, np.nan, this_var )
     #print this_var.shape
      data.append(this_var) # ith element of the list is a NUMPY ARRAY for the ith variable
     #print type(this_var)
     #print type(data)

   # Call a function to get the variable of interest.
   # Add a new function for each variable
   if variable == 'binaryCloud':     raw_data = getBinaryCloud(obsSource,data)
   if variable == 'totalCloudFrac':  raw_data = getTotalCloudFrac(obsSource,data)
   if variable == 'lowCloudFrac':    raw_data = getLayerCloudFrac(obsSource,data,'low')
   if variable == 'midCloudFrac':    raw_data = getLayerCloudFrac(obsSource,data,'mid')
   if variable == 'highCloudFrac':   raw_data = getLayerCloudFrac(obsSource,data,'high')
   if variable == 'cloudTopTemp':    raw_data = getCloudTopTemp(obsSource,data)
   if variable == 'cloudTopPres':    raw_data = getCloudTopPres(obsSource,data)

   raw_data = np.where(np.isnan(raw_data), missing_values, raw_data) # replace np.nan to missing_values (for MET)

   # Array met_data is passed to MET
   # Graphics should plot $met_data to make sure things look correct
   if obsDatasets[obsSource]['flipY']: 
      print 'flipping ',obsSource,' data about y-axis'
      met_data=np.flip(raw_data,axis=0).astype(float)
   else:
      met_data=raw_data.astype(float)

   # Make plotting optional or Just use plot_data_plane
#   plt_data=np.where(met_data<0, np.nan, met_data)
#   map=Basemap(projection='cyl',llcrnrlat=-90,urcrnrlat=90,llcrnrlon=-180,urcrnrlon=180,resolution='c')
#   map.drawcoastlines()
#   map.drawcountries()
#   map.drawparallels(np.arange(-90,90,30),labels=[1,1,0,1])
#   map.drawmeridians(np.arange(0,360,60),labels=[1,1,0,1])
#   plt.contourf(lons,lats,plt_data,20,origin='upper',cmap=cm.Greens) #cm.gist_rainbow)
#   title=obsSource+"_"+variable+"_"+str(validTime)
#   plt.title(title)
#   plt.colorbar(orientation='horizontal')
#   plt.savefig(title+".png")

   return met_data

###########
def getGridInfo(obsSource,gridType):

   if gridType == 'LatLon':
      latDef = obsDatasets[obsSource]['latDef']
      lonDef = obsDatasets[obsSource]['lonDef']
      gridInfo = {
         'type':      gridType,
         'name':      obsSource,
         'lat_ll':    latDef[0], #-90.000,
         'lon_ll':    lonDef[0], #-180.000,
         'delta_lat': latDef[1], #0.5000,
         'delta_lon': lonDef[1], #0.625,
         'Nlat':      latDef[2], #361,
         'Nlon':      lonDef[2], #576,
      }
   elif gridType == 'Gaussian':
      gridInfo = {
        'type':     gridType,
        'name':     obsSource,
        'nx':       obsDatasets[obsSource]['nx'],
        'ny':       obsDatasets[obsSource]['ny'],
        'lon_zero': obsDatasets[obsSource]['lon_zero'],
      }
 
   return gridInfo

def getAttrArray(obsSource,variable,initialTimeYMD,initialTimeHMS,validTimeYMD,validTimeHMS,forecastHMS):

   attrs = {

      'valid': validTimeYMD+'_'+validTimeHMS,
      'init':  initialTimeYMD+'_'+initialTimeHMS,
      'lead':  forecastHMS,
      'accum': '000000',

      'name':      obsSource,  #'MERRA2_Cloud_Percentage'
      'long_name': variable,  #'Cloud Percentage Levels',
      'level':     'ALL',
      'units':     '%',

      'grid': getGridInfo(obsSource,obsDatasets[obsSource]['gridType'])
   }

   #print attrs
   #print obsDatasets[obsSource]

   return attrs

######## END FUNCTIONS   ##########
