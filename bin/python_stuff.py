#from __future__ import print_function
import os
import sys
import numpy as np
import datetime as dt
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

#entry for 'point' is for point-to-point comparison and is all dummy data (except for gridType) that is overwritten by point2point
griddedDatasets =  {
   'MERRA2'   : { 'gridType':'LatLon', 'latVar':'lat',     'latDef':[-90.0,0.50,361], 'lonVar':'lon',       'lonDef':[-180.0,0.625,576],   'flipY':True, },
   'SATCORPS' : { 'gridType':'LatLon', 'latVar':'latitude','latDef':[-90.0,0.25,721], 'lonVar':'longitude', 'lonDef':[-180.0,0.3125,1152], 'flipY':False, },
   'ERA5'     : { 'gridType':'LatLon', 'latVar':'latitude','latDef':[-89.7848769072,0.281016829130516,640], 'lonVar':'longitude', 'lonDef':[0.0,0.28125,1280], 'flipY':False, },
   'GFS'      : { 'gridType':'LatLon', 'latVar':'latitude','latDef':[90.0,0.25,721], 'lonVar':'longitude',  'lonDef':[0.0,0.25,1440],   'flipY':False, },
   'GALWEM'   : { 'gridType':'LatLon', 'latVar':'latitude','latDef':[-90.0,0.25,721], 'lonVar':'longitude',  'lonDef':[0.0,0.25,1440],   'flipY':True, },
   'GALWEM17' : { 'gridType':'LatLon', 'latVar':'latitude','latDef':[-89.921875,0.156250,1152], 'lonVar':'longitude',  'lonDef':[0.117187,0.234375,1536],   'flipY':False, },
   'WWMCA'    : { 'gridType':'LatLon', 'latVar':'latitude','latDef':[-90.0,0.25,721], 'lonVar':'longitude',  'lonDef':[0.0,0.25,1440],   'flipY':False, },
   'point'    : { 'gridType':'LatLon', 'latVar':'latitude','latDef':[0.0,921875,0.156250,1152], 'lonVar':'longitude',  'lonDef':[0.117187,0.234375,1536],   'flipY':False, },
}
   #TODO:Correct one, but MET can ingest a Gaussian grid only in Grib2 format (from Randy B.)
   #'ERA5'     : { 'gridType':'Gaussian', 'nx':1280, 'ny':640, 'lon_zero':0, 'latVar':'latitude', 'lonVar':'longitude', 'flipY':False, },

#GALWEM, both 17-km and 0.25-degree
lowCloudFrac_GALWEM  =  { 'parameterCategory':6, 'parameterNumber':3, 'typeOfFirstFixedSurface':10, 'shortName':'lcc' }
midCloudFrac_GALWEM  =  { 'parameterCategory':6, 'parameterNumber':4, 'typeOfFirstFixedSurface':10, 'shortName':'mcc' }
highCloudFrac_GALWEM =  { 'parameterCategory':6, 'parameterNumber':5, 'typeOfFirstFixedSurface':10, 'shortName':'hcc' }
totalCloudFrac_GALWEM = { 'parameterCategory':6, 'parameterNumber':1, 'typeOfFirstFixedSurface':10, 'shortName':'tcc' }
cloudTopHeight_GALWEM =  { 'parameterCategory':6, 'parameterNumber':12, 'typeOfFirstFixedSurface':3, 'shortName':'cdct' }
cloudBaseHeight_GALWEM =  { 'parameterCategory':6, 'parameterNumber':11, 'typeOfFirstFixedSurface':2, 'shortName':'cdcb' }

#GFS
lowCloudFrac_GFS  =  { 'parameterCategory':6, 'parameterNumber':1, 'typeOfFirstFixedSurface':214, 'shortName':'tcc' }
midCloudFrac_GFS  =  { 'parameterCategory':6, 'parameterNumber':1, 'typeOfFirstFixedSurface':224, 'shortName':'tcc' }
highCloudFrac_GFS =  { 'parameterCategory':6, 'parameterNumber':1, 'typeOfFirstFixedSurface':234, 'shortName':'tcc' }

#WWMCA
totalCloudFrac_WWMCA  = { 'parameterName':71, 'typeOfLevel':'entireAtmosphere' }

verifVariablesModel = {
    'binaryCloud'    :  {'GFS':[''], 'GALWEM17':[totalCloudFrac_GALWEM],  'GALWEM':[totalCloudFrac_GALWEM] },
    'totalCloudFrac' :  {'GFS':[''], 'GALWEM17':[totalCloudFrac_GALWEM],  'GALWEM':[totalCloudFrac_GALWEM] },
    'lowCloudFrac'   :  {'GFS':[lowCloudFrac_GFS], 'GALWEM17':[lowCloudFrac_GALWEM], 'GALWEM':[lowCloudFrac_GALWEM] },
    'midCloudFrac'   :  {'GFS':[midCloudFrac_GFS], 'GALWEM17':[midCloudFrac_GALWEM], 'GALWEM':[midCloudFrac_GALWEM] },
    'highCloudFrac'  :  {'GFS':[highCloudFrac_GFS], 'GALWEM17':[highCloudFrac_GALWEM], 'GALWEM':[highCloudFrac_GALWEM] },
    'cloudTopHeight' :  {'GFS':['']               , 'GALWEM17':[cloudTopHeight_GALWEM], 'GALWEM':[cloudTopHeight_GALWEM] },
    'cloudBaseHeight' : {'GFS':['']               , 'GALWEM17':[cloudBaseHeight_GALWEM], 'GALWEM':[cloudBaseHeight_GALWEM] },
}

cloudFracCatThresholds = '>0, <10.0, >=10.0, >=20.0, >=30.0, >=40.0, >=50.0, >=60.0, >=70.0, >=80.0, >=90.0' # MET format string
verifVariables = {
   'binaryCloud'    : { 'MERRA2':['CLDTOT'], 'SATCORPS':['cloud_percentage_level'],      'ERA5':['TCC'], 'WWMCA':[totalCloudFrac_WWMCA], 'units':'NA',  'thresholds':'>0.0', 'interpMethod':'nearest' },
   'totalCloudFrac' : { 'MERRA2':['CLDTOT'], 'SATCORPS':['cloud_percentage_level'],      'ERA5':['TCC'], 'WWMCA':[totalCloudFrac_WWMCA], 'units':'%',   'thresholds':cloudFracCatThresholds, 'interpMethod':'bilin' },
   'lowCloudFrac'   : { 'MERRA2':['CLDLOW'], 'SATCORPS':['cloud_percentage_level'],      'ERA5':['LCC'], 'units':'%',   'thresholds':cloudFracCatThresholds, 'interpMethod':'bilin' },
   'midCloudFrac'   : { 'MERRA2':['CLDMID'], 'SATCORPS':['cloud_percentage_level'],      'ERA5':['MCC'], 'units':'%',   'thresholds':cloudFracCatThresholds, 'interpMethod':'bilin' },
   'highCloudFrac'  : { 'MERRA2':['CLDHGH'], 'SATCORPS':['cloud_percentage_level'],      'ERA5':['HCC'], 'units':'%',   'thresholds':cloudFracCatThresholds, 'interpMethod':'bilin' },
   'cloudTopTemp'   : { 'MERRA2':['CLDTMP'], 'SATCORPS':['cloud_temperature_top_level'], 'ERA5':['']   , 'units':'K',   'thresholds':'NA', 'interpMethod':'bilin'},
   'cloudTopPres'   : { 'MERRA2':['CLDPRS'], 'SATCORPS':['cloud_pressure_top_level'],    'ERA5':['']   , 'units':'hPa', 'thresholds':'NA', 'interpMethod':'bilin'},
   'cloudTopHeight' : { 'MERRA2':['']      , 'SATCORPS':['cloud_height_top_level'],      'ERA5':['']   , 'units':'m',   'thresholds':'NA', 'interpMethod':'nearest'},
   'cloudBaseHeight': { 'MERRA2':['']      , 'SATCORPS':['cloud_height_base_level'],     'ERA5':['CBH'], 'units':'m',   'thresholds':'NA', 'interpMethod':'nearest'},
   'cloudCeiling'   : { 'MERRA2':['']      , 'SATCORPS':[''],                            'ERA5':['']   , 'units':'m',   'thresholds':'NA', 'interpMethod':'bilin'},
   'brightnessTemp' : { 'MERRA2':['']      , 'SATCORPS':[''],                            'ERA5':['']   , 'units':'K',   'thresholds':'<273.15, <270.0, <260.0, <250.0, <240.0, <235.0, <230.0, <225.0, <220.0, <215.0, <210.0', 'interpMethod':'bilin'},
}

# Combine the two dictionaries
#for key in verifVariablesModel.keys():
#  x = verifVariablesModel[key]
#  for key1 in x.keys():
#     verifVariables[key][key1] = x[key1]

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
   print(x) # needed for python 3 to read variable into csh variable
   return x

def getInterpMethod(variable):
   x = verifVariables[variable]['interpMethod'].upper()
   print(x) # needed for python 3 to read variable into csh variable
   return x

def getTotalCloudFrac(source,data):
   if source == 'SATCORPS':
    # x = data[0][0,:,:,0] * 1.0E-2  # scaling
      x = (data[0][0,:,:,1]  + data[0][0,:,:,2] + data[0][0,:,:,3])*1.0E-2  # scaling
   #  y = data[0]
   #  x = np.sum( y[:,:,:,1:4],axis=3)
   elif source == 'MERRA2':
#      x = ( data[0][0,:,:]+data[1][0,:,:]+data[2][0,:,:] ) *100.0 # the ith element of data is a numpy array
      x = data[0][0,:,:] * 100.0 # the ith element of data is a numpy array
      print(x.min(), x.max())
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
   else:
      x = data[0]
   return x

def getCloudTopPres(source,data):
   if source == 'SATCORPS':
      x = data[0][0,:,:,0] * 1.0E-1  # scaling
   elif source == 'MERRA2':
      x = data[0][0,:,:] * 1.0E-2  # scaling [Pa] -> [hPa]
   elif source == 'ERA5':
      x = data[0][0,0,:,:]
   else:
      x = data[0]
   return x

def getCloudTopHeight(source,data):
   if source == 'SATCORPS':
      x = data[0][0,:,:,0] * 1.0E+1  # scaling to [meters]
   elif source == 'MERRA2':
      x = data[0][0,:,:]     #TBD
   elif source == 'ERA5':
      x = data[0][0,0,:,:]   #TBD
   elif source == 'GALWEM17':
      x = data[0] * 1000.0 * 0.3048  # kilofeet -> meters
   else:
      x = data[0]
   return x

def getCloudBaseHeight(source,data):
   if source == 'SATCORPS':
      x = data[0][0,:,:,0] * 1.0E+1  # scaling to [meters]
   elif source == 'MERRA2':
      x = data[0][0,:,:]     #TBD
   elif source == 'ERA5':
      x = data[0][0,0,:,:]
   elif source == 'GALWEM17':
      x = data[0] * 1000.0 * 0.3048  # kilofeet -> meters
   else:
      x = data[0]
   return x

def getCloudCeiling(source,data):
   if source == 'SATCORPS':
      x = data[0][0,:,:,0]   #TBD
   elif source == 'MERRA2':
      x = data[0][0,:,:]     #TBD
   elif source == 'ERA5':
      x = data[0][0,0,:,:]   #TBD
   return x

# add other functions for different variables

###########

def getDataArray(inputFile,source,variable,dataSource):
   # 1) inputFile:  File name--either observations or forecast
   # 2) source:     Obsevation source (e.g., MERRA, SATCORP, etc.)
   # 3) variable:   Variable to verify
   # 4) dataSource: If 1, process forecast file. If 2 process obs file.

#   # specifying names here temporarily. file names should be passed in to python from shell script
#   if source == 'merra':      nc_file = '/gpfs/fs1/scratch/schwartz/MERRA/MERRA2_400.tavg1_2d_rad_Nx.20181101.nc4'
#   elif source == 'satcorp':  nc_file = '/glade/scratch/bjung/met/test_satcorps/GEO-MRGD.2018334.0000.GRID.NC'
#   elif source == 'era5':     nc_file = '/glade/scratch/bjung/met/test_era5/e5.oper.fc.sfc.instan.128_164_tcc.regn320sc.2018111606_2018120112.nc'

   source = source.upper().strip()  # Force uppercase and get rid of blank spaces, for safety

   print('dataSource = ',dataSource)

   if dataSource == 1:  # dataSource == 1 means forecast
      varsToRead = verifVariablesModel[variable][source] # returns a list whose ith element is a dictionary
     #grbs = pygrib.open(inputFile)
      idx = pygrib.index(inputFile,'parameterCategory','parameterNumber','typeOfFirstFixedSurface')
     #grbs.close()

   if dataSource == 2:  # dataSource == 2 means obs
      varsToRead = verifVariables[variable][source] # returns a list
      if source == 'WWMCA':
         idx2 = pygrib.index(inputFile,'parameterName','typeOfLevel')
      else:
         # Open the file
         nc_fid = Dataset(inputFile, "r", format="NETCDF4") #Dataset is the class behavior to open the file
         #nc_fid.set_auto_scale(True)

   print('Trying to read ',inputFile)

   # Get lat/lon information--currently not used
  #latVar = griddedDatasets[source]['latVar']
  #lonVar = griddedDatasets[source]['lonVar']
  #lats = np.array(nc_fid.variables[latVar][:])   # extract/copy the data
  #lons = np.array(nc_fid.variables[lonVar][:] )

   #print(lats.max())
   #print(lons.max())

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
         if variable == 'cloudTopHeight' or variable == 'cloudBaseHeight' and source == 'GALWEM17': 
            x = idx(parameterCategory=v['parameterCategory'],parameterNumber=v['parameterNumber'],typeOfFirstFixedSurface=v['typeOfFirstFixedSurface'])[1] # by getting element 1, you get a pygrib message
         else:
            x = idx(parameterCategory=v['parameterCategory'],parameterNumber=v['parameterNumber'],typeOfFirstFixedSurface=v['typeOfFirstFixedSurface'])[0] # by getting element 0, you get a pygrib message
	 
         if x.shortName != v['shortName']: print('Name mismatch!')
         read_var = x.values # same x.data()[0]
         read_missing = x.missingValue
         print('Reading ', x.shortName, 'at level ', x.typeOfFirstFixedSurface)
         
	 # The missing value (read_missing) for GALWEM17 and GALWEM cloud base/height is 9999, which is not the best choice because
	 # those could be actual values. So we need to use the masked array part (below) to handle which
	 # values are missing.  We also set read_missing to something unphysical to essentially disable it.
	 # Finally, if we don't change the 'missingValue' property in the GRIB2 file we are eventually outputting,
	 # the bitmap will get all messed up, because it will be based on 9999 instead of $missing_values
         if variable == 'cloudTopHeight' or variable == 'cloudBaseHeight':
            read_missing = -9999.
            x['missingValue'] = read_missing
            if source == 'GALWEM17':
	       #These are masked numpy arrays, with mask = True where there is a missing value (no cloud)
	       #Use np.ma.filled to create an ndarray where mask = True values are set to np.nan
               read_var = np.ma.filled(read_var.astype(read_var.dtype), np.nan)

      if dataSource == 2:  # dataSource == 2 means obs
         if source == 'WWMCA':
            x = idx2(parameterName=v['parameterName'],typeOfLevel=v['typeOfLevel'])[0] # by getting element 0, you get a pygrib message
            read_var = x.values # same x.data()[0]
            read_missing = x.missingValue
         else:
            read_var = nc_fid.variables[v]         # extract/copy the data
            read_missing = read_var.missing_value  # get variable attributes. Each dataset has own missing values.
         print('Reading ', v)

      this_var = np.array( read_var )        # to numpy array
     #print(read_missing, np.nan)
      this_var = np.where( this_var==read_missing, np.nan, this_var )
     #print(this_var.shape)
      data.append(this_var) # ith element of the list is a NUMPY ARRAY for the ith variable
     #print(type(this_var))
     #print(type(data))

   # Call a function to get the variable of interest.
   # Add a new function for each variable
   if variable == 'binaryCloud':     raw_data = getBinaryCloud(source,data)
   if variable == 'totalCloudFrac':  raw_data = getTotalCloudFrac(source,data)
   if variable == 'lowCloudFrac':    raw_data = getLayerCloudFrac(source,data,'low')
   if variable == 'midCloudFrac':    raw_data = getLayerCloudFrac(source,data,'mid')
   if variable == 'highCloudFrac':   raw_data = getLayerCloudFrac(source,data,'high')
   if variable == 'cloudTopTemp':    raw_data = getCloudTopTemp(source,data)
   if variable == 'cloudTopPres':    raw_data = getCloudTopPres(source,data)
   if variable == 'cloudTopHeight':  raw_data = getCloudTopHeight(source,data)
   if variable == 'cloudBaseHeight': raw_data = getCloudBaseHeight(source,data)
   if variable == 'cloudCeiling':    raw_data = getCloudCeiling(source,data)

   raw_data = np.where(np.isnan(raw_data), missing_values, raw_data) # replace np.nan to missing_values (for MET)

   # Array met_data is passed to MET
   # Graphics should plot $met_data to make sure things look correct
   if griddedDatasets[source]['flipY']: 
      print('flipping ',source,' data about y-axis')
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

   # If a forecast file, output a GRIB file with 
   # 1 record containing the met_data
   # This is a hack, because right now, MET python embedding doesn't work with pygrib,
   #    so output the data to a temporary file, and then have MET read the temporary grib file.
   # Starting with version 9.0 of MET, the hack isn't needed, and MET python embedding works with pygrib
   outputFcstFile = True  # MUST be True for MET version < 9.0.  For MET 9.0+, optional
   if dataSource == 1: 
      if outputFcstFile:
         grbtmp = x
         grbtmp['values']=met_data
         grbout = open('temp_fcst.grb2','ab')
         grbout.write(grbtmp.tostring())
         grbout.close() # Close the outfile GRIB file
         print('Successfully output temp_fcst.grb2')

   # Close files
   if dataSource == 1: idx.close()    # Close the input GRIB file
   if dataSource == 2:
      if source == 'WWMCA': idx2.close()
      else: nc_fid.close() # Close the netCDF file

   return met_data

def getFcstCloudFrac(cfr,pmid): # cfr is cloud fraction(%), pmid is pressure(Pa), code from UPP ./INITPOST.F
   PTOP_LOW  = 64200. # UPP layer bounds
   PTOP_MID  = 35000.
   PTOP_HIGH = 15000.

   if pmid.shape != cfr.shape:  # sanity check
      print('dimension mismatch')
      sys.exit()

   nlocs, nlevs = pmid.shape

   cfracl = np.zeros(nlocs)
   cfracm = np.zeros(nlocs)
   cfrach = np.zeros(nlocs)

   for i in range(0,nlocs):
      idxLow  = np.where(   pmid[i,:] >= PTOP_LOW)[0] # using np.where with just 1 argument returns tuple
      idxMid  = np.where(  (pmid[i,:] <  PTOP_LOW) & (pmid[i,:] >= PTOP_MID))[0]
      idxHigh = np.where(  (pmid[i,:] <  PTOP_MID) & (pmid[i,:] >= PTOP_HIGH))[0]

      # use conditions incase all indices are missing
      if (len(idxLow) >0 ):  cfracl[i] = np.max( cfr[i,idxLow] )
      if (len(idxMid) >0 ):  cfracm[i] = np.max( cfr[i,idxMid] )
      if (len(idxHigh) >0 ): cfrach[i] = np.max( cfr[i,idxHigh] )

   tmp = np.vstack( (cfracl,cfracm,cfrach)) # stack the rows into one 2d array
   cldfraMax = np.max(tmp,axis=0) # get maximum value across low/mid/high for each pixel

   # This is the fortran code put into python format...double loop unnecessary and slow
   #for i in range(0,nlocs):
   #   for k in range(0,nlevs):
   #      if pmid(i,k) >= PTOP_LOW:
   #	 cfracl(i) = np.max( [cfracl(i),cfr(i,k)] ) # Low
   #      elif pmid(i,k) < PTOP_LOW and pmid(i,k) >= PTOP_MID:
   #	 cfracm(i) = np.max( [cfracm(i),cfr(i,k)] ) # Mid
   #      elif pmid(i,k) < PTOP_MID and pmid(i,k) >= PTOP_HIGH: # High
   #	 cfrach(i) = np.max( [cfrach(i),cfr(i,k)] )

   return cfracl, cfracm, cfrach, cldfraMax

def point2point(source,inputDir,satellite,channel,dataSource):

   # Static Variables for QC and obs
   qcVar  = 'brightness_temperature_'+str(channel)+'@EffectiveQC0' # QC variable
   obsVar = 'brightness_temperature_'+str(channel)+'@ObsValue'  # Observation variable

   # Get list of files.  There is one file per processor
   files = os.listdir(inputDir)
   inputFiles = fnmatch.filter(files,'obsout*_'+satellite+'*nc4') # returns relative path names
   inputFiles = [inputDir+'/'+s for s in inputFiles] # add on directory name
   if len(inputFiles) == 0: return -99999, -99999 # if no matching files, force a failure

   # Variable to pull for brightness temperature
#  if dataSource == 1: v = 'brightness_temperature_'+str(channel)+'@GsiHofXBc' # Forecast variable
   if dataSource == 1: v = 'brightness_temperature_'+str(channel)+'@depbg' # OMB
   if dataSource == 2: v = obsVar

   # Read the files and put data in array
   allData, allDataQC = [], []
   for inputFile in inputFiles:
      nc_fid = Dataset(inputFile, "r", format="NETCDF4") #Dataset is the class behavior to open the file
      print('Trying to read ',v,' from ',inputFile)

      # Read forecast/obs data
      read_var = nc_fid.variables[v]         # extract/copy the data
   #  read_missing = read_var.missing_value  # get variable attributes. Each dataset has own missing values.
      this_var  = np.array( read_var )        # to numpy array
   #  this_var = np.where( this_var==read_missing, np.nan, this_var )

      if dataSource == 1: # If true, we read in OMB data
         obsData = np.array( nc_fid.variables[obsVar])
         this_var = obsData - this_var # get background/forecast value (O - OMB = B)

      #Read QC data
      qcData = np.array(nc_fid.variables[qcVar])

      # Sanity check
      if qcData.shape != this_var.shape: return -99999, -99999 # shapes should match.

      if 'abi' in satellite or 'ahi' in satellite:
         cldfraThresh = 20.0 # percent
         obsCldfra = np.array( nc_fid.variables['cloud_area_fraction@MetaData'] )*100.0 # Get into %...observed cloud fraction (AHI/ABI only)

         geoValsFile = inputFile.replace('obsout','geoval')
         if not os.path.exists(geoValsFile):
            print(geoValsFile+' not there. exit')
            sys.exit()

         nc_fid2 = Dataset(geoValsFile, "r", format="NETCDF4")
         fcstCldfra = np.array( nc_fid2.variables['cloud_area_fraction_in_atmosphere_layer'])*100.0 # Get into %
         pressure   = np.array( nc_fid2.variables['air_pressure']) # Pa
         low,mid,high,fcstTotCldFra = getFcstCloudFrac(fcstCldfra,pressure) # get low/mid/high/total cloud fractions
         nc_fid2.close()

	 # modify QC data based on correspondence between forecast and obs. qcData used to select good data later
         condition = 'any'
         yes = 2.0
         no  = 0.0
         if qcData.shape == obsCldfra.shape == fcstTotCldFra.shape:  # these should all match
            print('Checking F/O correspondence for ABI/AHI')
            if   condition.lower().strip() == 'clearOnly'.lower():
               qcData = np.where( (fcstTotCldFra < cldfraThresh) & (obsCldfra < cldfraThresh), qcData, missing_values) # clear in both F and O
            elif condition.lower().strip() == 'cloudyOnly'.lower():
               qcData = np.where( (fcstTotCldFra >= cldfraThresh) & (obsCldfra >= cldfraThresh), qcData, missing_values) # cloudy in both F and O
            elif condition.lower().strip() == 'cloudEventLow'.lower():
               if dataSource == 1: this_var = np.where( low           > cldfraThresh, yes, no ) # set cloudy points to 2, clear points to 0, use threshold of 1 in MET
               if dataSource == 2: this_var = np.where( obsCldfra     > cldfraThresh, yes, no ) 
            elif condition.lower().strip() == 'cloudEventMid'.lower():
               if dataSource == 1: this_var = np.where( mid           > cldfraThresh, yes, no ) # set cloudy points to 2, clear points to 0, use threshold of 1 in MET
               if dataSource == 2: this_var = np.where( obsCldfra     > cldfraThresh, yes, no ) 
            elif condition.lower().strip() == 'cloudEventHigh'.lower():
               if dataSource == 1: this_var = np.where( high          > cldfraThresh, yes, no ) # set cloudy points to 2, clear points to 0, use threshold of 1 in MET
               if dataSource == 2: this_var = np.where( obsCldfra     > cldfraThresh, yes, no ) 
            elif condition.lower().strip() == 'cloudEventTot'.lower():
               if dataSource == 1: this_var = np.where( fcstTotCldFra > cldfraThresh, yes, no ) # set cloudy points to 2, clear points to 0, use threshold of 1 in MET
               if dataSource == 2: this_var = np.where( obsCldfra     > cldfraThresh, yes, no ) 

            print('number removed = ', (qcData==missing_values).sum())
           #print('number passed   = ', qcData.shape[0] - (qcData==missing_values).sum())
         else:
            print('shape mismatch')
            return -99999, -99999
	   
      # Append to arrays
      allData.append(this_var)
      allDataQC.append(qcData)

      nc_fid.close() # done with the file, so close it before going to next file in loop

   # Get the indices with acceptable QC
   allQC = np.concatenate(allDataQC) # Put list of numpy arrays into a single long 1-D numpy array.  All QC data.
   idx = np.where(allQC==0) # returns indices

   # Now get all the forecast/observed brightness temperature data with acceptable QC
   this_var = np.concatenate(allData)[idx] # Put list of numpy arrays into a single long 1-D numpy array. This is all the forecast/obs data with good QC
   numObs = this_var.shape[0] # number of points for one channel
   print('Number of obs :',numObs)

   # Assume all the points actually fit into a square grid. Get the side of the square (use ceil to round up)
   l = np.ceil(np.sqrt(numObs)).astype('int') # Length of the side of the square

   # Make an array that can be reshaped into the square 
   raw_data1D = np.full(l*l,np.nan) # Initialize 1D array of length l**2 to np.nan
   raw_data1D[0:numObs] = this_var[:] # Fill data to the extent possible. There will be some np.nan values at the end
   raw_data = np.reshape(raw_data1D,(l,l)) # Reshape into "square grid"

   raw_data = np.where(np.isnan(raw_data), missing_values, raw_data) # replace np.nan to missing_values (for MET)

   met_data=raw_data.astype(float) # Give MET this info

   # Now need to tell MET the "grid" for the data
   # Make a fake lat/lon grid going from 0.0 to 50.0 degrees, with the interval determined by number of points
   griddedDatasets[source]['latDef'][0] = 0.0 # starting point
   griddedDatasets[source]['latDef'][1] = np.diff(np.linspace(0,50,l)).round(6)[0] # interval (degrees)
   griddedDatasets[source]['latDef'][2] = l # number of points
   griddedDatasets[source]['lonDef'][0:3] = griddedDatasets[source]['latDef']

   gridInfo = getGridInfo(source, griddedDatasets[source]['gridType']) # 'LatLon' gridType

   return met_data, gridInfo

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

def getAttrArray(source,variable,initTime,validTime):

   init = dt.datetime.strptime(initTime,"%Y%m%d%H")
   valid = dt.datetime.strptime(validTime,"%Y%m%d%H")
   lead, rem = divmod((valid-init).total_seconds(), 3600)

   attrs = {

      'valid': valid.strftime("%Y%m%d_%H%M%S"),
      'init':  init.strftime("%Y%m%d_%H%M%S"),
      'lead':  str(int(lead)),
      'accum': '000000',

      'name':      source,  #'MERRA2_Cloud_Percentage'
      'long_name': variable,  #'Cloud Percentage Levels',
      'level':     'ALL',
      'units':     verifVariables[variable]['units'],

      'grid': getGridInfo(source,griddedDatasets[source]['gridType'])
   }

   #print(attrs)
   #print(griddedDatasets[source])

   return attrs

######## END FUNCTIONS   ##########
