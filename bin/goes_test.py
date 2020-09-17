#from __future__ import print_function
import os
import sys
import numpy as np
import datetime as dt
from netCDF4 import Dataset  # http://code.google.com/p/netcdf4-python/
from scipy.interpolate import LinearNDInterpolator
from scipy.interpolate import NearestNDInterpolator
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

inputDir = '/glade/scratch/guerrett/pandac/guerrett_3denvar_conv_clramsua_120km/VF/bg/2018041500/Data'
satellite = 'abi_g16'
channel = 8
goesFile = '/glade/u/home/schwartz/cloud_verification/goes/2020082500/L2-CTP/OR_ABI-L2-CTPF-M6_G16_s20202380010211_e20202380019519_c20202380021232.nc'

#### functions ####
def getGOES16LatLon(g16_data_file):

   # Start timer
   startTime = dt.datetime.utcnow()
 
   # designate dataset
   g16nc = Dataset(g16_data_file, 'r')

   # GOES-R projection info and retrieving relevant constants
   proj_info = g16nc.variables['goes_imager_projection']
   lon_origin = proj_info.longitude_of_projection_origin
   H = proj_info.perspective_point_height+proj_info.semi_major_axis
   r_eq = proj_info.semi_major_axis
   r_pol = proj_info.semi_minor_axis

   # Data info
   lat_rad_1d = g16nc.variables['x'][:]
   lon_rad_1d = g16nc.variables['y'][:]

   # close file when finished
   g16nc.close()
   g16nc = None

   # create meshgrid filled with radian angles
   lat_rad,lon_rad = np.meshgrid(lat_rad_1d,lon_rad_1d)

   # lat/lon calc routine from satellite radian angle vectors

   lambda_0 = (lon_origin*np.pi)/180.0

   a_var = np.power(np.sin(lat_rad),2.0) + (np.power(np.cos(lat_rad),2.0)*(np.power(np.cos(lon_rad),2.0)+(((r_eq*r_eq)/(r_pol*r_pol))*np.power(np.sin(lon_rad),2.0))))
   b_var = -2.0*H*np.cos(lat_rad)*np.cos(lon_rad)
   c_var = (H**2.0)-(r_eq**2.0)

   r_s = (-1.0*b_var - np.sqrt((b_var**2)-(4.0*a_var*c_var)))/(2.0*a_var)

   s_x = r_s*np.cos(lat_rad)*np.cos(lon_rad)
   s_y = - r_s*np.sin(lat_rad)
   s_z = r_s*np.cos(lat_rad)*np.sin(lon_rad)

   lat = (180.0/np.pi)*(np.arctan(((r_eq*r_eq)/(r_pol*r_pol))*((s_z/np.sqrt(((H-s_x)*(H-s_x))+(s_y*s_y))))))
   lon = (lambda_0 - np.arctan(s_y/(H-s_x)))*(180.0/np.pi)

   # End timer
   endTime = dt.datetime.utcnow()
   time = (endTime - startTime).microseconds / (1000.0*1000.0)

   print('took %f4.1 seconds to get GOES16 lat/lon'%(time))

   return lon,lat # lat/lon are 2-d arrays

#### main code below here ####

# Static Variables for QC and obs from JEDI/UFO/IODA output
qcVar  = 'brightness_temperature_'+str(channel)+'@EffectiveQC0' # QC variable
obsVar = 'brightness_temperature_'+str(channel)+'@ObsValue'  # Observation variable

# Get list of radiance OMB files.  There is one file per processor.
files = os.listdir(inputDir)
inputFiles = fnmatch.filter(files,'obsout*_'+satellite+'*nc4') # returns relative path names
inputFiles = [inputDir+'/'+s for s in inputFiles] # add on directory name
if len(inputFiles) == 0:
   print('no input files. exit')
   sys.exit()

#  if dataSource == 1: v = 'brightness_temperature_'+str(channel)+'@depbg' # OMB
#  if dataSource == 2: v = obsVar
v = obsVar

# Get GOES-16 retrieval file with auxiliary information
if not os.path.exists(goesFile):
  print(goesFile+' not there. exit')
  sys.exit()
goesLon2d, goesLat2d = getGOES16LatLon(goesFile) # 2-d arrays
goesLon = goesLon2d.flatten() # 1-d arrays
goesLat = goesLat2d.flatten()

nc_goes = Dataset(goesFile, "r", format="NETCDF4")

# If the next line is true (it should be), this indicates the variable needs to be treated
#  as an "unsigned 16-bit integer". This is a pain.  So we must use the "astype" method
#  to change the variable type BEFORE applying scale_factor and add_offset.  After the conversion
#  we then can manually apply the scale factor and offset
goesVar = 'PRES'
if nc_goes.variables[goesVar]._Unsigned.lower().strip()  == 'true':
   nc_goes.set_auto_scale(False) # Don't automatically apply scale_factor and add_offset to variable
   goesCTP2d = np.array( nc_goes.variables[goesVar]).astype(np.uint16)
   goesCTP2d = goesCTP2d * nc_goes.variables[goesVar].scale_factor + nc_goes.variables[goesVar].add_offset
   goesQC2d  = np.array( nc_goes.variables['DQF']).astype(np.uint8)
else:
   goesCTP2d = np.array( nc_goes.variables[goesVar])
   goesQC2d  = np.array( nc_goes.variables['DQF'])

# Make variables 1-d
goesQC  = goesQC2d.flatten()
goesCTP = goesCTP2d.flatten()
nc_goes.close()

# Get rid of NaNs; base it oon longitude
goesCTP = goesCTP[~np.isnan(goesLon)] # Handle data arrays first before changing lat/lon itself
goesQC  = goesQC[~np.isnan(goesLon)] 
goesLon = goesLon[~np.isnan(goesLon)] # ~ is "logical not", also np.logical_not
goesLat = goesLat[~np.isnan(goesLat)] 
if goesLon.shape != goesLat.shape:
   print('GOES lat/lon shape mismatch')
   sys.exit()

# If goesQC == 0, good QC and there was a cloud with a valid pressure.
# If goesQC == 4, no cloud; probably clear sky.
# All other QC means no data, and we want to remove those points
idx = np.logical_or( goesQC == 0, goesQC == 4) # Only keep QC == 0 or 4
goesLon = goesLon[idx]
goesLat = goesLat[idx]
goesCTP = goesCTP[idx]
goesQC  = goesQC[idx]

# Only QC with 0 or 4 are left; now set QC == 4 to missing to indicate clear sky
goesCTP = np.where( goesQC != 0, -999., goesCTP)

# Get longitude to between (0,360) for consistency with JEDI files (add check to JEDI files, too)
goesLon = np.where( goesLon < 0, goesLon + 360.0, goesLon )

print('Min GOES Lon = ',np.min(goesLon))
print('Max GOES Lon = ',np.max(goesLon))

lonlatGOES = np.array( zip(goesLon, goesLat)) #np.transpose( np.vstack((goesLon,goesLat)) ) # lat/lon pairs for each GOES ob (nobs_GOES, 2)
print('shape lonlatGOES = ',lonlatGOES.shape)
my_funcCTP = NearestNDInterpolator(lonlatGOES,goesCTP)
#my_funcCTP = LinearNDInterpolator(lonlatGOES,goesCTP)

# Read the OMB files and put data in array
allData, allDataQC = [], []
allLats, allLons   = [], []
for inputFile in inputFiles:
   nc_fid = Dataset(inputFile, "r", format="NETCDF4") #Dataset is the class behavior to open the file
  #print('Trying to read ',v,' from ',inputFile)

   # Read forecast/obs data
   read_var = nc_fid.variables[v]         # extract/copy the data
#  read_missing = read_var.missing_value  # get variable attributes. Each dataset has own missing values.
   this_var  = np.array( read_var )        # to numpy array
#  this_var = np.where( this_var==read_missing, np.nan, this_var )

  #if dataSource == 1: # If true, we read in OMB data
  #   obsData = np.array( nc_fid.variables[obsVar])
  #   this_var = obsData - this_var # get background/forecast value (O - OMB = B)

   #Read QC data
   qcData = np.array(nc_fid.variables[qcVar])

   #Read lat/lon for these radiances
   lats = np.array(nc_fid.variables['latitude@MetaData'])
   lons = np.array(nc_fid.variables['longitude@MetaData'])
 # lonlat = np.transpose( np.vstack((lats,lons)) ) # lat/lon pairs for each ob (nobs, 2)
 # goesCTP_points(lonlat) # return GOES-16 retrieval information at the observation locations in this file

   # Sanity check
   if qcData.shape != this_var.shape:
      print('shape mismatch qcData')
      sys.exit()

   # Append to arrays
   allData.append(this_var)
   allDataQC.append(qcData)
   allLats.append(lats)
   allLons.append(lons)

   nc_fid.close() # done with the file, so close it before going to next file in loop

# Get the indices with acceptable QC
allQC = np.concatenate(allDataQC) # Put list of numpy arrays into a single long 1-D numpy array.  All QC data.
idx = np.where(allQC==0) # returns indices

# Now get all the forecast/observed brightness temperature data with acceptable QC
this_var  = np.concatenate(allData)[idx] # Put list of numpy arrays into a single long 1-D numpy array. This is all the forecast/obs data with good QC
good_lats = np.concatenate(allLats)[idx] 
good_lons = np.concatenate(allLons)[idx]
lonlat = np.array( zip(good_lons,good_lats)) #np.transpose( np.vstack((good_lons,good_lats)) ) # lat/lon pairs for each ob (nobs, 2)
print('lonlat shape : ',lonlat.shape)
print('this_var shape : ',this_var.shape)

# Now plot
fig, (ax1,ax2) = plt.subplots(2,1, figsize=(8,11) ,sharex=True)

# GOES plotting
print('getting corresponing GOES-16 values at %i points'%(good_lons.shape))
this_var_interp = my_funcCTP(lonlat)
print('min native/interp value = ',np.min(goesCTP), np.min(this_var_interp))
print('max native/interp value = ',np.max(goesCTP), np.max(this_var_interp))

print(this_var_interp)
print(this_var_interp.shape)

goesLevels = np.arange(100,1050,50)

goesCTP2d = np.where( goesQC2d != 0 , np.nan, goesCTP2d)
#cntr = ax1.imshow(goesCTP2d,vmin=goesLevels[0],vmax=goesLevels[-1],cmap='terrain')
cntr = ax1.tricontourf(goesLon, goesLat, goesCTP, levels=goesLevels,cmap='terrain') #, levels=14, linewidths=0.5, colors='k')
#ax1.plot(goesLon,goesLat,'ko',ms=0.05)
cb = fig.colorbar(cntr,ax=ax1)
cb.set_label('hPa')
ax1.set_title('Native values')
ax1.set_ylabel('Latitude')

cntr2 = ax2.tricontourf(good_lons, good_lats, this_var_interp, levels=goesLevels,cmap='terrain') #, levels=14, linewidths=0.5, colors='k')
#ax2.plot(good_lons,good_lats,'ko',ms=0.1)
cb = fig.colorbar(cntr2,ax=ax2)
cb.set_label('hPa')
ax2.set_title('Interpolated values')
ax2.set_xlabel('Longitude')
ax2.set_ylabel('Latitude')

# Testing that interpolation function works, based on input JEDI data and selected points

# Define the interpolation function
#my_func = LinearNDInterpolator(lonlat,this_var)
#my_func2 = NearestNDInterpolator(lonlat,this_var)

# Pick some points we want to interpolate to, and interpolate
#x = np.linspace(225,345,61).astype('float')
#y = np.linspace(-60,60,61).astype('float')
#lon2d, lat2d = np.meshgrid(x,y) # make 2d arrays
#dataPoints = np.array( [lon2d.flatten(), lat2d.flatten()]).T
#print('shape dataPoints = ',dataPoints.shape)

# Do the interpolation. 
#this_var_interp = my_func(dataPoints)
#this_var_interp = np.where( np.isnan(this_var_interp), 0, this_var_interp)
#this_var_interp = np.where( np.isnan(this_var_interp), my_func2(dataPoints), this_var_interp)
#levels = np.arange(190,270,10)

#cntr = ax1.tricontourf(good_lons, good_lats, this_var, levels=levels)  #, linewidths=0.5, colors='k')
#ax1.plot(lon2d.flatten(), lat2d.flatten(),'ko',ms=0.5)
#fig.colorbar(cntr,ax=ax1)

#cntr2 = ax2.tricontourf(lon2d.flatten(), lat2d.flatten(), this_var_interp, levels=levels) #, levels=14, linewidths=0.5, colors='k')
#ax2.plot(lon2d.flatten(), lat2d.flatten(),'ko',ms=0.5)
#fig.colorbar(cntr2,ax=ax2)

# To add a common colorbar...range based on the plot specified in fig.colorbar
#fig.subplots_adjust(right=0.8) # adjust the subplot positions
#cbar_ax = fig.add_axes([0.85, 0.15, 0.05, 0.7])
#fig.colorbar(cntr, cax=cbar_ax)

fig.savefig('test.pdf',format='pdf')
