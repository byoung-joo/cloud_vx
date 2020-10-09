#!/bin/ksh -l

##########################################################################
#
# Script Name: driver_script_with_python.ksh
#
# Description:
#    This script runs the MET/Grid-Stat and MODE tools to verify gridded
#    precipitation forecasts against gridded precipitation analyses.
#    The precipitation fields must first be placed on a common grid prior
#    to running this script.
#
#             START_TIME = The cycle time to use for the initial time.
#              FCST_TIME = The three-digit forecasts that is to be verified.
#            VX_OBS_LIST = A list of observation sources to be used.
#            VX_VAR_LIST = A list of observed variables to be used.
#            DOMAIN_LIST = A list of domains to be verified.
#                GRID_VX = Defines the grid forecast and obs will be mapped to.
#           MET_EXE_ROOT = The full path of the MET executables.
#             MET_CONFIG = The full path of the MET configuration files.
#               DATAROOT = Top-level data directory of WRF output.
#               FCST_DIR = Directory containing the forecasts to be used.
#                RAW_OBS = Directory containing observations to be used.
#                  MODEL = The model being evaluated.
#
##########################################################################

# Make sure we give other group members write access to the files we create
#umask 002

MKDIR=/bin/mkdir
ECHO=/bin/echo
CP=/bin/cp
CUT=`which cut`
DATE=/bin/date

#source /glade/u/apps/ch/modulefiles/default/localinit/localinit.sh
#module purge
#module use /glade/p/ral/jntp/MET/MET_releases/modulefiles
#module load met/8.0_python
#ncar_pylib

# MET v8.1--this is what we used prior to 18 June 2020
#source /glade/u/apps/ch/modulefiles/default/localinit/localinit.sh
#module purge
#module use /glade/p/ral/jntp/MET/MET_releases/modulefiles
#module load met/8.1_python
#ncar_pylib

# MET v9.0
source /glade/u/apps/ch/modulefiles/default/localinit/localinit.sh
module purge
module use /glade/p/ral/jntp/MET/MET_releases/modulefiles
module load met/9.0
module load ncarenv
ncar_pylib
   # specify full path to local python exectuable...needed such that MET
   # executes the python script with the user's version of python (and environment and loaded packages) rather than the python build
   # defined at MET compilation time.
export MET_PYTHON_EXE=`which python` #export MET_PYTHON_EXE=/glade/u/apps/ch/opt/python/3.6.8/gnu/8.3.0/pkg-library/20200417/bin/python

####

# Vars used for manual testing of the script
#export START_TIME=2020083100 #2017060500 #2018110100
#export FCST_TIME_LIST="06 09" # 6 9 12 24 36 48"
#export VX_OBS_LIST="WWMCA" #"SATCORPS MERRA2 ERA5" #ERA5" # WWMCA
#export VX_VAR_LIST="totalCloudFrac" #"binaryCloud" #lowCloudFrac" #"totalCloudFrac lowCloudFrac midCloudFrac highCloudFrac binaryCloud" # cloudTopTemp cloudTopPres cloudBaseHeight cloudTopHeight
#export DOMAIN_LIST="global"
#export GRID_VX="FCST"
#export MET_EXE_ROOT=/glade/p/ral/jntp/MET/MET_releases/8.1_python/bin
#export MET_EXE_ROOT=/glade/p/ral/jntp/MET/MET_releases/9.0/bin
#export MET_CONFIG=/glade/scratch/`whoami`/cloud_vx/static/MET/met_config #CSS
#export DATAROOT=/glade/scratch/`whoami`/cloud_vx # CSS
#export FCST_DIR=/gpfs/u/home/schwartz/cloud_verification/GFS_grib_0.25deg #GFS
#export FCST_DIR=/glade/scratch/schwartz/GALWEM   # GALWEM17 and GALWEM and models (GALWEM 17 is 17-km GALWEM from 2017), "GALWEM" is 0.25 degree from Air Force in 2020-2021
#export RAW_OBS=/glade/scratch/schwartz/OBS
#export MODEL="GALWEM" # Options are "GFS", "MPAS", "GALWEM17", or "GALWEM"

# Print run parameters
${ECHO}
${ECHO} "driver_script_with_python.ksh started at `${DATE}`"
${ECHO}
${ECHO} "    START_TIME = ${START_TIME}"
${ECHO} "     FCST_TIME = ${FCST_TIME_LIST}"
${ECHO} "        VX_OBS = ${VX_OBS_LIST}"
${ECHO} "        VX_VAR = ${VX_VAR_LIST}"
${ECHO} "   DOMAIN_LIST = ${DOMAIN_LIST}"
${ECHO} "       GRID_VX = ${GRID_VX}"
${ECHO} "  MET_EXE_ROOT = ${MET_EXE_ROOT}"
${ECHO} "    MET_CONFIG = ${MET_CONFIG}"
${ECHO} "      DATAROOT = ${DATAROOT}"
${ECHO} "      FCST_DIR = ${FCST_DIR}"
${ECHO} "       RAW_OBS = ${RAW_OBS}"
${ECHO} "         MODEL = ${MODEL}"

# Make sure $DATAROOT exists
if [ ! -d "${DATAROOT}" ]; then
  ${ECHO} "ERROR: DATAROOT, ${DATAROOT} does not exist"
  exit 1
fi

# Make sure $FCST_DIR exists
if [ ! -d "${FCST_DIR}" ]; then
  ${ECHO} "ERROR: FCST_DIR, ${FCST_DIR} does not exist"
  exit 1
fi

# Make sure RAW_OBS directory exists
if [ ! -d ${RAW_OBS} ]; then
  ${ECHO} "ERROR: RAW_OBS, ${RAW_OBS}, does not exist!"
  exit 1
fi

# Make sure date/time utility exists
if [ ! -e ${DATAROOT}/exec/da_advance_time.exe ]; then
  ${ECHO} "ERROR: Could not find da_advance_time.exe: in ${DATAROOT}/exec"
  exit 1
fi

export MODEL
${ECHO} "MODEL=${MODEL}"

# Set MET_NAME, which is the last portion of full MODEL name
MET_NAME=${MODEL} #`echo ${MODEL} | cut -d"_" -f4-`

# Loop through the forecast times
for FCST_TIME in ${FCST_TIME_LIST}; do
export FCST_TIME

# Go to working directory
workdir=${DATAROOT}/metprd/${START_TIME}/f${FCST_TIME}
${MKDIR} -p ${workdir}
cd ${workdir}

# Loop through the veryfing obs dataset
for VX_OBS in ${VX_OBS_LIST}; do
export VX_OBS

# Loop through the veryfing obs dataset
for VX_VAR in ${VX_VAR_LIST}; do
export VX_VAR

# Loop through the domain list
for DOMAIN in ${DOMAIN_LIST}; do
   
    export DOMAIN
    export GRID_VX
    ${ECHO} "DOMAIN=${DOMAIN}"
    ${ECHO} "GRID_VX=${GRID_VX}"
    ${ECHO} "FCST_TIME=${FCST_TIME}"

    # Compute the verification date
    YYYYMMDD=`${ECHO} ${START_TIME} | ${CUT} -c1-8` # Forecast initialization time
    MMDD=`${ECHO} ${START_TIME} | ${CUT} -c5-8`
    HHMMSS=`${DATAROOT}/exec/da_advance_time.exe ${START_TIME} 0 -F hhnnss`
    HH=`${ECHO} ${START_TIME} | ${CUT} -c9-10`
    VDATE=`${DATAROOT}/exec/da_advance_time.exe ${START_TIME} +${FCST_TIME}` # Valid time
    VYYYYMMDD=`${ECHO} ${VDATE} | ${CUT} -c1-8`
    VYYYY=`${ECHO} ${VDATE} | ${CUT} -c1-4`
    VMM=`${ECHO} ${VDATE} | ${CUT} -c5-6`
    VDD=`${ECHO} ${VDATE} | ${CUT} -c7-8`
    VHH=`${ECHO} ${VDATE} | ${CUT} -c9-10`
    VHHMMSS=`${DATAROOT}/exec/da_advance_time.exe ${VDATE} 0 -F hhnnss`
    ${ECHO} 'valid time for ' ${FCST_TIME} 'h forecast = ' ${VDATE}

   # CSS commented out...not currently used
#   PVDATE=`${DATAROOT}/exec/da_advance_time.exe ${VDATE} -12`
#   PVYYYYMMDD=`${ECHO} ${PVDATE} | ${CUT} -c1-8`

    # Specify mask directory structure
    MASKS=${MET_CONFIG}/masks
    export MASKS

    # Specify the MET Grid-Stat and MODE configuration files to be used
    #GS_CONFIG_LIST="${MET_CONFIG}/GridStatConfig_trad ${MET_CONFIG}/MODEConfig_trad"  # CSS, I feel like this should be defined elsewhere...
    #GS_CONFIG_LIST="${MET_CONFIG}/GridStatConfig_trad"  # CSS, I feel like this should be defined elsewhere...
    GS_CONFIG_LIST="${MET_CONFIG}/GridStatConfig_trad ${MET_CONFIG}/GridStatConfig_nbr ${MET_CONFIG}/GridStatConfig_prob"  # CSS, I feel like this should be defined elsewhere...

    # Get the forecast to verify
    if [ ${FCST_TIME} == "09" ]; then # Need some weird logic for FCST_TIME = 09
	FCST_HRS=$(printf "%03d" ${FCST_TIME##+(0)})  #3-digit hour for GFS name
	FCST_TIME=$(printf "%01d" ${FCST_TIME##+(0)}) #1-digit...this line probably not needed
    else
        FCST_HRS=$(printf "%03d" ${FCST_TIME})  #3-digit hour for GFS name
    fi

    # TODO: add more FCST variables
        # GFS for now
            #PRESlclt   0,213,0   0,3,0,0 ** low cloud top level Pressure [Pa]
            #PRESmclt   0,223,0   0,3,0,0 ** middle cloud top level Pressure [Pa]
            #PREShclt   0,233,0   0,3,0,0 ** high cloud top level Pressure [Pa]
            #TMPlclt   0,213,0   0,0,0,0 ** low cloud top level Temperature [K]
            #TMPmclt   0,223,0   0,0,0,0 ** middle cloud top level Temperature [K]
            #TMPhclt   0,233,0   0,0,0,0 ** high cloud top level Temperature [K]
    if [[ $MODEL == "GFS" ]]; then
       if [ $VX_VAR == "totalCloudFrac" ]; then
	   export metConfName="TCDC";export metConfGribLvlTyp=10;export metConfGribLvlVal1=0
       elif [ $VX_VAR == "lowCloudFrac" ]; then
	   export metConfName="TCDC";export metConfGribLvlTyp=214;export metConfGribLvlVal1=0
       elif [ $VX_VAR == "midCloudFrac" ]; then
	   export metConfName="TCDC";export metConfGribLvlTyp=224;export metConfGribLvlVal1=0
       elif [ $VX_VAR == "highCloudFrac" ]; then
	   export metConfName="TCDC";export metConfGribLvlTyp=234;export metConfGribLvlVal1=0
       elif [ $VX_VAR == "binaryCloud"    ]; then
	   export metConfName="TCDC";export metConfGribLvlTyp=10;export metConfGribLvlVal1=0
       fi
    elif [[ $MODEL == "GALWEM17" || $MODEL == "GALWEM" ]]; then
       if [ $VX_VAR == "totalCloudFrac" ]; then
	   export metConfName="TCDC";export metConfGribLvlTyp=10;export metConfGribLvlVal1=0
       elif [ $VX_VAR == "lowCloudFrac" ]; then
	   export metConfName="LCDC";export metConfGribLvlTyp=10;export metConfGribLvlVal1=0
       elif [ $VX_VAR == "midCloudFrac" ]; then
	   export metConfName="MCDC";export metConfGribLvlTyp=10;export metConfGribLvlVal1=0
       elif [ $VX_VAR == "highCloudFrac" ]; then
	   export metConfName="HCDC";export metConfGribLvlTyp=10;export metConfGribLvlVal1=0
       elif [ $VX_VAR == "binaryCloud"    ]; then
	   export metConfName="TCDC";export metConfGribLvlTyp=10;export metConfGribLvlVal1=0
       elif [ $VX_VAR == "cloudTopHeight" ]; then
	   export metConfName="CDCTOP";export metConfGribLvlTyp=3;export metConfGribLvlVal1=0
       elif [ $VX_VAR == "cloudBaseHeight" ]; then
	   export metConfName="CDCB";export metConfGribLvlTyp=2;export metConfGribLvlVal1=0
       elif [ $VX_VAR == "cloudCeiling" ]; then
	   export metConfName="CEIL";export metConfGribLvlTyp=10;export metConfGribLvlVal1=0
       fi
    fi

    #######################################################################
    #
    #  Run Grid-Stat
    #
    #######################################################################

    for CONFIG_FILE in ${GS_CONFIG_LIST}; do

        # Make sure the Grid-Stat configuration file exists
        if [ ! -e ${CONFIG_FILE} ]; then
            ${ECHO} "ERROR: ${CONFIG_FILE} does not exist!"
            exit 1
        fi

	if [ ${MODEL} == "GFS" ]; then
	    FCST_FILE=${FCST_DIR}/${START_TIME}/gfs.0p25.${START_TIME}.f${FCST_HRS}.grib2
	elif [ ${MODEL} == "GALWEM17" ]; then
	    FCST_FILE=${FCST_DIR}/${MMDD}/GPP_17km_combined_${YYYYMMDD}_CY${HH}_FH${FCST_HRS}.GR2
	elif [ ${MODEL} == "GALWEM" ]; then
	    FCST_FILE=${FCST_DIR}/${START_TIME}/PS.557WW_SC.U_DI.C_DC.GRID_GP.GALWEM-GD_SP.COMPLEX_GR.C0P25DEG_AR.GLOBAL_PA.NCAR_DD.${YYYYMMDD}_CY.${HH}_FH.${FCST_HRS}_DF.GR2
	else
            ${ECHO} "ERROR: MODEL = $MODEL not currently supported"
            exit 1
        fi

	# Make sure FCST_FILE exists
	if [ ! -e ${FCST_FILE} ]; then
            ${ECHO} "ERROR: Could not find forecast file: ${FCST_FILE}"
            exit 1
	fi

        # Get the processed observation file 
        if [ ${VX_OBS} == "SATCORPS" ]; then
           JDAY=`${DATAROOT}/exec/da_advance_time.exe  ${VDATE} 0 -j | awk '{print $2}'`  #for SATCORPS name
           OBS_FILE=${RAW_OBS}/${VX_OBS}/prod.Global-GEO.visst-grid-netcdf.${VYYYY}${VMM}${VDD}.GEO-MRGD.${VYYYY}${JDAY}.${VHH}00.GRID.NC
	   # Format changed in 2020, if above not there, try a different format
	   if [ ! -e ${OBS_FILE} ]; then
              OBS_FILE=${RAW_OBS}/${VX_OBS}/GEO-MRGD.${VYYYY}${JDAY}.${VHH}00.GRID.NC
	   fi
	  #OBS_FILE=${RAW_OBS}/${VX_OBS}/GEO-MRGD.${VYYYY}${JDAY}.${VHH}00.GRID.NC
        elif  [ ${VX_OBS} == "MERRA2" ]; then
          TMP=`${DATAROOT}/exec/da_advance_time.exe ${VDATE} +30min`  #TODO: 30 min offset
          TMP_YYYYMMDD=`echo ${TMP} | cut -c1-8`
          TMP_HHMM=`echo ${TMP} | cut -c9-12`
	  OBS_FILE=${RAW_OBS}/${VX_OBS}/${VX_OBS}_400.tavg1_2d_${TMP_YYYYMMDD}_${TMP_HHMM}.nc4
        elif  [ ${VX_OBS} == "ERA5" ]; then
          OBS_FILE=${RAW_OBS}/${VX_OBS}/${VX_OBS}_${VDATE}.nc
        elif  [ ${VX_OBS} == "WWMCA" ]; then
          OBS_FILE=${RAW_OBS}/${VX_OBS}/WWMCA_${VDATE}00_ECE15_M.GR1
        fi

	if [ ! -e ${OBS_FILE} ]; then
	    ${ECHO} "ERROR: Could not find obs file: ${OBS_FILE}"
	    exit 1
	fi
	
        ${MKDIR} -p ${workdir}/${VX_VAR}/${VX_OBS}
	cd ${workdir}/${VX_VAR}/${VX_OBS}
        ${CP} ${DATAROOT}/bin/python_stuff.py .

        # CSS get the verification thresholds.
	# This could be done further up, but we don't copy python_stuff.py until the above line.
        export thresholds=[`python -c "import python_stuff; python_stuff.getThreshold('$VX_VAR')"`] # add brackets for MET convention for list
        export interp_method=`python -c "import python_stuff; python_stuff.getInterpMethod('$VX_VAR')"` 

	if [[ $interp_method == 'BILIN' ]]; then
	   export regrid_width=2
	elif [[ $interp_method == 'NEAREST' ]]; then
	   export regrid_width=1
	fi
        echo "THRESHOLDS = $thresholds"
        echo "INTERP_METHOD = $interp_method"

        for i in 1 2; do
	   if [ $i == 1 ]; then
	      scriptName=./python_script_fcst.py
	      dataFile=${FCST_FILE}
	      dataSource=${MODEL}
	   elif [ $i == 2 ]; then
	      scriptName=./python_script_obs.py
	      dataFile=${OBS_FILE}
	      dataSource=${VX_OBS}
	   fi
	   ${ECHO} "Python script=$scriptName"
           cat > $scriptName << EOF
import os
import numpy as np
import python_stuff  # this is where all the work is done

dataFile = '$dataFile'
dataSource = '$dataSource'
variable = '$VX_VAR'

# With the data/files/valid_time specified in this script, pass relevant variables to python function (from python_stuff.py)
met_data = python_stuff.getDataArray(dataFile,dataSource,variable,${i})

# TODO: This is for "obs". If we ingest forecast later, we need to improve this.
#attrs = python_stuff.getAttrArray(dataSource,variable,'${YYYYMMDD}','${HHMMSS}','${VYYYYMMDD}','${VHHMMSS}','${VHHMMSS}') # CSS this seems more correct???
#attrs = dict.getAttrArray(obsSource,variable,'${VYYYYMMDD}','${VHHMMSS}','${VYYYYMMDD}','${VHHMMSS}','${VHHMMSS}')
attrs = python_stuff.getAttrArray(dataSource,variable,'${START_TIME}','${VDATE}')
EOF

	   # For the forecast, run the python script OUTSIDE OF MET, while MET crashes with python pygrib routines
	   #  Within python_stuff.getDataArray, the script will output a temporary GRIB file (temp_fcst.grb2)
	   #   that can be read into MET directly, but which contains potentially derived fields.
	   if [ $i == 1 ]; then 
	      rm -f ./temp_fcst.grb2
	     #python $scriptName # Will create temp_fcst.grb2
	     #FCST_FILE=./temp_fcst.grb2
	      FCST_FILE=PYTHON_NUMPY # For MetV9.0, MET can handle pygrib.
	   fi;

        done # loop over i=1,2, once for forecast, another for obs
        
        if [[ `echo $CONFIG_FILE | grep -i "gridstat" | wc -l` == 1 ]]; then # CSS note the double brackets in the if statement
	   ${ECHO} "CALLING: ${MET_EXE_ROOT}/grid_stat ${FCST_FILE} PYTHON_NUMPY ${CONFIG_FILE} -outdir  ${workdir}/${VX_VAR}/${VX_OBS} -v 2"

	   # Run grid_stat
	   ${MET_EXE_ROOT}/grid_stat \
	     $FCST_FILE \
	     PYTHON_NUMPY \
	     ${CONFIG_FILE} \
	     -outdir ${workdir}/${VX_VAR}/${VX_OBS} \
	     -v 2

	   error=$?
	   if [ ${error} -ne 0 ]; then
	       ${ECHO} "ERROR: For ${MODEL}, ${MET_EXE_ROOT}/grid_stat crashed  Exit status: ${error}"
	       exit ${error}
	   fi

	   # TODO: This is temporary plotting using MET executable.
	   # Run plot_data_plane
	   ${MET_EXE_ROOT}/plot_data_plane PYTHON_NUMPY \
	     ${workdir}/${VX_VAR}/${VX_OBS}/${VX_OBS}_${VX_VAR}_${START_TIME}_f${FCST_HRS}.ps \
	     -title ${VX_OBS}_${VX_VAR}_${START_TIME}_f${FCST_HRS} \
	     -color_table /glade/p/ral/jntp/MET/MET_releases/8.1/met-8.1.1/data/colortables/NCL_colortables/wh-bl-gr-ye-re.ctable \
	     'name="python_script_obs.py";'
        fi

        # CSS run MODE
        if [[ `echo $CONFIG_FILE | grep -i "mode" | wc -l` == 1 ]]; then # CSS note the double brackets in the if statement
	   ${ECHO} "CALLING: ${MET_EXE_ROOT}/mode      ${FCST_FILE} PYTHON_NUMPY ${CONFIG_FILE} -outdir  ${workdir}/${VX_VAR}/${VX_OBS} -v 2"
	   ${MET_EXE_ROOT}/mode      \
	     $FCST_FILE \
	     PYTHON_NUMPY \
	     ${CONFIG_FILE} \
	     -outdir ${workdir}/${VX_VAR}/${VX_OBS} \
	     -v 2
        fi

    done #CONFIG_FILE loop

done #DOMAIN loop

done #VX_VAR loop

done #FCST_TIME loop

done #VX_OBS loop

##########################################################################

${ECHO} "driver_script_with_python.ksh completed at `${DATE}`"

exit 0
