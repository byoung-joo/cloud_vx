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
import pygrib
#####

###########################################

missing_values = -9999.0  # for MET

griddedDatasets =  {
   'MERRA2'   : { 'gridType':'LatLon',   'latVar':'lat',     'latDef':[-90.0,0.50,361], 'lonVar':'lon',       'lonDef':[-180.0,0.625,576],   'flipY':True, },
   'SATCORPS' : { 'gridType':'LatLon',   'latVar':'latitude','latDef':[-90.0,0.25,721], 'lonVar':'longitude', 'lonDef':[-180.0,0.3125,1152], 'flipY':False, },
   'ERA5'     : { 'gridType':'LatLon',   'latVar':'latitude','latDef':[-89.7848769072,0.281016829130516,640], 'lonVar':'longitude', 'lonDef':[0.0,0.28125,1280], 'flipY':False, },
   'GFS'      : { 'gridType':'LatLon',   'latVar':'latitude','latDef':[90.0,0.25,721], 'lonVar':'longitude',  'lonDef':[0.0,0.25,1440],   'flipY':False, },
   'GALWEM'   : { 'gridType':'LatLon',   'latVar':'latitude','latDef':[-89.921875,0.156250,1152], 'lonVar':'longitude',  'lonDef':[0.117187,0.234375,1536],   'flipY':False, },
}
   #TODO:Correct one, but MET can ingest a Gaussian grid only in Grib2 format (from Randy B.)
   #'ERA5'     : { 'gridType':'Gaussian', 'nx':1280, 'ny':640, 'lon_zero':0, 'latVar':'latitude', 'lonVar':'longitude', 'flipY':False, },

#GALWEM
lowCloudFrac_GALWEM  =  { 'parameterCategory':6, 'parameterNumber':3, 'typeOfFirstFixedSurface':10, 'shortName':'lcc' }
midCloudFrac_GALWEM  =  { 'parameterCategory':6, 'parameterNumber':4, 'typeOfFirstFixedSurface':10, 'shortName':'mcc' }
highCloudFrac_GALWEM =  { 'parameterCategory':6, 'parameterNumber':5, 'typeOfFirstFixedSurface':10, 'shortName':'hcc' }
totalCloudFrac_GALWEM = { 'parameterCategory':6, 'parameterNumber':1, 'typeOfFirstFixedSurface':10, 'shortName':'tcc' }

#GFS
lowCloudFrac_GFS  =  { 'parameterCategory':6, 'parameterNumber':1, 'typeOfFirstFixedSurface':214, 'shortName':'tcc' }
midCloudFrac_GFS  =  { 'parameterCategory':6, 'parameterNumber':1, 'typeOfFirstFixedSurface':224, 'shortName':'tcc' }
highCloudFrac_GFS =  { 'parameterCategory':6, 'parameterNumber':1, 'typeOfFirstFixedSurface':234, 'shortName':'tcc' }

verifVariablesModel = {
    'lowCloudFrac'   :  {'GFS':[lowCloudFrac_GFS], 'GALWEM':[lowCloudFrac_GALWEM]  },
    'midCloudFrac'   :  {'GFS':[midCloudFrac_GFS], 'GALWEM':[midCloudFrac_GALWEM]  },
    'highCloudFrac'  :  {'GFS':[highCloudFrac_GFS], 'GALWEM':[highCloudFrac_GALWEM]  },
    'totalCloudFrac' :  {'GFS':[''], 'GALWEM':[totalCloudFrac_GALWEM]},
}

verifVariables = {
   'binaryCloud'    : { 'MERRA2':['CLDTOT'], 'SATCORPS':['cloud_percentage_level'],      'ERA5':['TCC'], 'thresholds':'>0.0', 'interpMethod':'nearest' },
   'totalCloudFrac' : { 'MERRA2':['CLDTOT'], 'SATCORPS':['cloud_percentage_level'],      'ERA5':['TCC'], 'thresholds':'<10.0, >=10.0, >=20.0, >=30.0, >=40.0, >=50.0, >=60.0, >=70.0, >=80.0, >=90.0', 'interpMethod':'bilin' },
   'lowCloudFrac'   : { 'MERRA2':['CLDLOW'], 'SATCORPS':['cloud_percentage_level'],      'ERA5':['LCC'], 'thresholds':'<10.0, >=10.0, >=20.0, >=30.0, >=40.0, >=50.0, >=60.0, >=70.0, >=80.0, >=90.0', 'interpMethod':'bilin' },
   'midCloudFrac'   : { 'MERRA2':['CLDMID'], 'SATCORPS':['cloud_percentage_level'],      'ERA5':['MCC'], 'thresholds':'<10.0, >=10.0, >=20.0, >=30.0, >=40.0, >=50.0, >=60.0, >=70.0, >=80.0, >=90.0', 'interpMethod':'bilin' },
   'highCloudFrac'  : { 'MERRA2':['CLDHGH'], 'SATCORPS':['cloud_percentage_level'],      'ERA5':['HCC'], 'thresholds':'<10.0, >=10.0, >=20.0, >=30.0, >=40.0, >=50.0, >=60.0, >=70.0, >=80.0, >=90.0', 'interpMethod':'bilin' },
   'cloudTopTemp'   : { 'MERRA2':['CLDTMP'], 'SATCORPS':['cloud_temperature_top_level'], 'ERA5':['']   , 'thresholds':'NA', 'interpMethod':'bilin'},
   'cloudTopPres'   : { 'MERRA2':['CLDPRS'], 'SATCORPS':['cloud_pressure_top_level'],    'ERA5':['']   , 'thresholds':'NA', 'interpMethod':'bilin'},
}
#f = '/glade/u/home/schwartz/cloud_verification/GFS_grib_0.25deg/2018112412/gfs.0p25.2018112412.f006.grib2'
#grbs = pygrib.open(f)
#idx = pygrib.index(f,'parameterCategory','parameterNumber','typeOfFirstFixedSurface')
#model = 'GFS'
#variable = 'totCloudCover'
#x = verifVariablesModel[variable][model] # returns a list, whose ith element is a dictionary
# e.g., idx(parameterCategory=6,parameterNumber=1,typeOfFirstFixedSurface=234)
#idx(parameterCategory=x[0]['parameterCategory'],parameterNumber=x[0]['parameterNumber'],typeOfFirstFixedSurface=x[0]['typeOfFirstFixedSurface'])

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
   else:
      x = data[0]

   # This next line is WRONG.
   # Missing should be set to missing
   # Then, the non-missing values are 1s and 0s
   #output = np.where(x > 0.0, x, 0.0)
   #output = np.where(x < 0.0, -9999.0, x) # missing. currently used for SATCORPS
   return x

def getBinaryCloud(source,data):
   y = getTotalCloudFrac(source,data)
   # keep NaNs as is, but then set everything else to either 100% or 0%
   x = np.where( np.isnan(y), y, np.where(y > 0.0, 100.0, 0.0) )
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
   else:
      x = data[0]

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

def getDataArray(inputFile,source,variable,validTime,dataSource):
   # 1) File name--either observations or forecast
   # 2) Obsevation source (e.g., MERRA, SATCORP, etc.)
   # 3) Variable to verify
   # 4) validTime
   # 5) Data source: If 1, process forecast file. If 2 process obs file.

#   # specifying names here temporarily. file names should be passed in to python from shell script
#   if source == 'merra':
#      nc_file = '/gpfs/fs1/scratch/schwartz/MERRA/MERRA2_400.tavg1_2d_rad_Nx.20181101.nc4'
#   elif source == 'satcorp':
#      nc_file = '/glade/scratch/bjung/met/test_satcorps/GEO-MRGD.2018334.0000.GRID.NC'
#   elif source == 'era5':
#      nc_file = '/glade/scratch/bjung/met/test_era5/e5.oper.fc.sfc.instan.128_164_tcc.regn320sc.2018111606_2018120112.nc'

   source = source.upper().strip()  # Force uppercase and get rid of blank spaces, for safety

   if dataSource == 1:  # dataSource == 1 means forecast
      varsToRead = verifVariablesModel[variable][source] # returns a list whose ith element is a dictionary
     #grbs = pygrib.open(inputFile)
      idx = pygrib.index(inputFile,'parameterCategory','parameterNumber','typeOfFirstFixedSurface')
     #grbs.close()

   if dataSource == 2:  # dataSource == 2 means obs
      varsToRead = verifVariables[variable][source] # returns a list
      # Open the file
      nc_fid = Dataset(inputFile, "r", format="NETCDF4") #Dataset is the class behavior to open the file
      #nc_fid.set_auto_scale(True)

   print 'Trying to read ',inputFile

   # Get lat/lon information--currently not used
  #latVar = griddedDatasets[source]['latVar']
  #lonVar = griddedDatasets[source]['lonVar']
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
   for v in varsToRead:
      if dataSource == 1:  # dataSource == 1 means forecast
         # e.g., idx(parameterCategory=6,parameterNumber=1,typeOfFirstFixedSurface=234)
	 x = idx(parameterCategory=v['parameterCategory'],parameterNumber=v['parameterNumber'],typeOfFirstFixedSurface=v['typeOfFirstFixedSurface'])[0] # by getting element 0, you get a pygrib message
	 print 'here 0'
	 if x.shortName != v['shortName']: print 'Name mismatch!'
	 print 'here 1'
	 read_var = x.values # x.data()[0] # x.values
	 print 'here 2'
	 read_missing = x.missingValue
	 print 'here 3'
	 print 'Reading ', x.shortName, 'at level ', x.typeOfFirstFixedSurface

      if dataSource == 2:  # dataSource == 2 means obs
	 read_var = nc_fid.variables[v]         # extract/copy the data
	 read_missing = read_var.missing_value  # get variable attributes. Each dataset has own missing values.
	 print 'Reading ', v

      this_var = np.array( read_var )        # to numpy array
     #print read_missing, np.nan
      this_var = np.where( this_var==read_missing, np.nan, this_var )
     #print this_var.shape
      data.append(this_var) # ith element of the list is a NUMPY ARRAY for the ith variable
     #print type(this_var)
     #print type(data)

   # Call a function to get the variable of interest.
   # Add a new function for each variable
   if variable == 'binaryCloud':     raw_data = getBinaryCloud(source,data)
   if variable == 'totalCloudFrac':  raw_data = getTotalCloudFrac(source,data)
   if variable == 'lowCloudFrac':    raw_data = getLayerCloudFrac(source,data,'low')
   if variable == 'midCloudFrac':    raw_data = getLayerCloudFrac(source,data,'mid')
   if variable == 'highCloudFrac':   raw_data = getLayerCloudFrac(source,data,'high')
   if variable == 'cloudTopTemp':    raw_data = getCloudTopTemp(source,data)
   if variable == 'cloudTopPres':    raw_data = getCloudTopPres(source,data)

   raw_data = np.where(np.isnan(raw_data), missing_values, raw_data) # replace np.nan to missing_values (for MET)

   # Array met_data is passed to MET
   # Graphics should plot $met_data to make sure things look correct
   if griddedDatasets[source]['flipY']: 
      print 'flipping ',source,' data about y-axis'
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
#   title=source+"_"+variable+"_"+str(validTime)
#   plt.title(title)
#   plt.colorbar(orientation='horizontal')
#   plt.savefig(title+".png")

   if dataSource == 1: idx.close()    # Close the GRIB file
   if dataSource == 2: nc_fid.close() # Close the netCDF file

   return met_data

###########
def getGridInfo(source,gridType):

   if gridType == 'LatLon':
      latDef = griddedDatasets[source]['latDef']
      lonDef = griddedDatasets[source]['lonDef']
      gridInfo = {
         'type':      gridType,
         'name':      source,
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
        'name':     source,
        'nx':       griddedDatasets[source]['nx'],
        'ny':       griddedDatasets[source]['ny'],
        'lon_zero': griddedDatasets[source]['lon_zero'],
      }
 
   return gridInfo

def getAttrArray(source,variable,initialTimeYMD,initialTimeHMS,validTimeYMD,validTimeHMS,forecastHMS):

   attrs = {

      'valid': validTimeYMD+'_'+validTimeHMS,
      'init':  initialTimeYMD+'_'+initialTimeHMS,
      'lead':  forecastHMS,
      'accum': '000000',

      'name':      source,  #'MERRA2_Cloud_Percentage'
      'long_name': variable,  #'Cloud Percentage Levels',
      'level':     'ALL',
      'units':     '%',

      'grid': getGridInfo(source,griddedDatasets[source]['gridType'])
   }

   #print attrs
   #print griddedDatasets[source]

   return attrs

######## END FUNCTIONS   ##########
