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
#         FCST_TIME_LIST = The three-digit forecasts that is to be verified.
#            VX_VAR_LIST = A list of observed variables to be used.
#            DOMAIN_LIST = A list of domains to be verified.
#           MET_EXE_ROOT = The full path of the MET executables.
#             MET_CONFIG = The full path of the MET configuration files.
#               DATAROOT = Top-level data directory of WRF output.
#               FCST_DIR = Directory containing the forecasts to be used.
#                RAW_OBS = Directory containing observations to be used.
#              SATELLITE = The satellite being evaluated.
#           CHANNEL_LIST = A list of observation sources to be used.
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

source /glade/u/apps/ch/modulefiles/default/localinit/localinit.sh
module purge
module use /glade/p/ral/jntp/MET/MET_releases/modulefiles
module load met/8.1_python
ncar_pylib

# Vars used for manual testing of the script
export START_TIME=2018051100 #2018110100
export FCST_TIME_LIST="24" # "12 09" # 6 9 12 24 36 48"
export VX_VAR_LIST="brightnessTemp"
export DOMAIN_LIST="global"  # Probably don't need
export MET_EXE_ROOT=/glade/p/ral/jntp/MET/MET_releases/8.1_python/bin
export MET_CONFIG=/glade/scratch/`whoami`/cloud_vx/static/MET/met_config 
export DATAROOT=/glade/scratch/`whoami`/cloud_vx 
export FCST_DIR=/glade/scratch/schwartz/pandac_output/junmei
export RAW_OBS=$FCST_DIR
export SATELLITE="amsua_n19" # format is important and must match filename format
export CHANNEL_LIST="5 6 7 8 9"
export GS_CONFIG_LIST="${MET_CONFIG}/point2point_all" # MET Grid-Stat and MODE configuration files to be used

# Print run parameters
${ECHO}
${ECHO} "driver_script_with_python.ksh started at `${DATE}`"
${ECHO}
${ECHO} "    START_TIME = ${START_TIME}"
${ECHO} "     FCST_TIME = ${FCST_TIME_LIST}"
${ECHO} "        VX_VAR = ${VX_VAR_LIST}"
${ECHO} "   DOMAIN_LIST = ${DOMAIN_LIST}"
${ECHO} "  MET_EXE_ROOT = ${MET_EXE_ROOT}"
${ECHO} "    MET_CONFIG = ${MET_CONFIG}"
${ECHO} "      DATAROOT = ${DATAROOT}"
${ECHO} "      FCST_DIR = ${FCST_DIR}"
${ECHO} "       RAW_OBS = ${RAW_OBS}"
${ECHO} "     SATELLITE = ${SATELLITE}"
${ECHO} "      CHANNELS = ${CHANNEL_LIST}"

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

# Satellite we're verifying against
export SATELLITE
${ECHO} "SATELLITE=${SATELLITE}"

# Loop through the forecast times
for FCST_TIME in ${FCST_TIME_LIST}; do
export FCST_TIME

# Go to working directory
workdir=${DATAROOT}/metprd/${START_TIME}/f${FCST_TIME}
${MKDIR} -p ${workdir}
cd ${workdir}

# Loop through the veryfing obs dataset
for CHANNEL in ${CHANNEL_LIST}; do
export CHANNEL

# Loop through the veryfing obs dataset
for VX_VAR in ${VX_VAR_LIST}; do
export VX_VAR

# Loop through the domain list
for DOMAIN in ${DOMAIN_LIST}; do
   
    export DOMAIN
    ${ECHO} "DOMAIN=${DOMAIN}"
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

    # Specify mask directory structure
    MASKS=${MET_CONFIG}/masks
    export MASKS

    # Get the forecast to verify
    if [ ${FCST_TIME} == "09" ]; then # Need some weird logic for FCST_TIME = 09
	FCST_HRS=$(printf "%03d" ${FCST_TIME##+(0)})  #3-digit hour for GFS name
	FCST_TIME=$(printf "%01d" ${FCST_TIME##+(0)}) #1-digit...this line probably not needed
    else
        FCST_HRS=$(printf "%03d" ${FCST_TIME})  #3-digit hour for GFS name
    fi

    #FCST_FILE=${FCST_DIR}/${START_TIME}/gfs.0p25.${START_TIME}.f${FCST_HRS}.grib2
   #FCST_FILE="/glade/scratch/wuyl/test2/Lekima/da/obserr/plot/diag/diags_himawari-8-ahi_2019081100.nc"
   #FCST_FILE="/glade/scratch/wuyl/test2/pandac/mw/15km_mpas/6hfcst_thomp_DA_bc_noqc_thomp_ocean/2018041806/Data/obsout_3dvar_amsua_n19--hydro_0252.nc4"
    THIS_FCST_DIR=${FCST_DIR}/${START_TIME}/f${FCST_TIME}

    # Make sure the directory exists
    if [ ! -d ${THIS_FCST_DIR} ]; then
        ${ECHO} "ERROR: Could not find forecast dir: ${THIS_FCST_DIR}"
        exit 1
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

        # Get the processed observation file 
       OBS_DIR=$THIS_FCST_DIR

	if [ ! -d ${OBS_DIR} ]; then
	    ${ECHO} "ERROR: Could not find obs dir: ${OBS_DIR}"
	    exit 1
	fi
	
	thisDir=${workdir}/${SATELLITE}/channel${CHANNEL}
        ${MKDIR} -p ${thisDir}
	cd ${thisDir}
        ${CP} ${DATAROOT}/bin/python_stuff.py .

        # CSS get the verification thresholds.
	# This could be done further up, but we don't copy python_stuff.py until the above line.
        export thresholds=[`python -c "import python_stuff; print python_stuff.getThreshold('$VX_VAR')"`] # add brackets for MET convention for list
        echo "THRESHOLDS = $thresholds"

        for i in 1 2; do
	   if [ $i == 1 ]; then
	      scriptName=./python_script_fcst.py
	      dataDir=${THIS_FCST_DIR}
	   elif [ $i == 2 ]; then
	      scriptName=./python_script_obs.py
	      dataDir=${OBS_DIR}
	   fi
	   ${ECHO} "Python script=$scriptName"
           cat > $scriptName << EOF
import os
import numpy as np
import python_stuff  # this is where all the work is done

dataDir = '$dataDir'
variable = '$VX_VAR'

met_data, gridInfo = python_stuff.point2point('point',dataDir,'${SATELLITE}',${CHANNEL},${i})
attrs = python_stuff.getAttrArray('point',variable,'${START_TIME}','${VDATE}')
attrs['grid'] = gridInfo
EOF

        done # loop over i=1,2, once for forecast, another for obs
        
	${ECHO} "CALLING: ${MET_EXE_ROOT}/grid_stat PYTHON_NUMPY PYTHON_NUMPY ${CONFIG_FILE} -outdir ${thisDir} -v 2"

	# Run grid_stat
	${MET_EXE_ROOT}/grid_stat \
	  PYTHON_NUMPY \
	  PYTHON_NUMPY \
	  ${CONFIG_FILE} \
	  -outdir ${thisDir}\
	  -v 2

	error=$?
	if [ ${error} -ne 0 ]; then
	    ${ECHO} "ERROR: For ${SATELLITE}, ${MET_EXE_ROOT}/grid_stat crashed  Exit status: ${error}"
	    exit ${error}
	fi

	# TODO: This is temporary plotting using MET executable.
	# Run plot_data_plane
	${MET_EXE_ROOT}/plot_data_plane PYTHON_NUMPY \
	  ${workdir}/${SATELLITE}/channel${CHANNEL}/${SATELLITE}_channel${CHANNEL}_${START_TIME}_f${FCST_HRS}.ps \
	  -title ${SATELLITE}_channel${CHANNEL}_${START_TIME}_f${FCST_HRS} \
	  -color_table /glade/p/ral/jntp/MET/MET_releases/8.0/met-8.0/data/colortables/NCL_colortables/wh-bl-gr-ye-re.ctable \
	  'name="python_script_obs.py";'

    done #CONFIG_FILE loop

done #DOMAIN loop

done #VX_VAR loop

done #FCST_TIME loop

done #CHANNEL loop

##########################################################################

${ECHO} "driver_script_with_python.ksh completed at `${DATE}`"

exit 0
