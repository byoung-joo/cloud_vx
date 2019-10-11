#!/bin/ksh -l

##########################################################################
#
# Script Name: met_point_driver.ksh
#
# Description:
#    This script runs the MET/Point-Stat tool to verify gridded output
#    from the WRF PostProcessor using point observations.  The MET/PB2NC
#    tool must be run on the PREPBUFR observation files to be used prior
#    to running this script.
#
#             START_TIME = The cycle time to use for the initial time.
#             FCST_TIME  = The two-digit forecast that is to be verified.
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
umask 002

LS=/bin/ls
MKDIR=/bin/mkdir
ECHO=/bin/echo
CUT=`which cut`
DATE=/bin/date

source /glade/u/apps/ch/modulefiles/default/localinit/localinit.sh
module purge
module use /glade/p/ral/jntp/MET/MET_releases/modulefiles
module load met/8.0
ncar_pylib

# Vars used for manual testing of the script
#export START_TIME=2018111800
#export FCST_TIME_LIST="00" 
#export VX_OBS_LIST="EPIC"
#export VX_VAR_LIST="Cloud_Mask"
#export DOMAIN_LIST="global"
#export GRID_VX="NONE"
#export MET_EXE_ROOT=/glade/p/ral/jntp/MET/MET_releases/8.0/bin  #/glade/p/ral/jnt/HRRR/retro/exec/MET
#export MET_CONFIG=REL_DIR/static/MET/met_config
#export DATAROOT=REL_DIR
#export FCST_DIR=/glade/scratch/jwolff/CAF/met/draft_1st/FCST
#export RAW_OBS=/glade/scratch/jwolff/CAF/met/draft_3rd/OBS    #/glade/scratch/jfrimel/init/obs/201510/mrms_grb2
#export MODEL="GFS"  #"hrconus"

# Print run parameters/masks
${ECHO}
${ECHO} "met_point_driver.ksh  started at `${DATE}`"
${ECHO}
${ECHO} "    START_TIME = ${START_TIME}"
${ECHO} "     FCST_TIME = ${FCST_TIME_LIST}"
${ECHO} "        VX_OBS = ${VX_OBS_LIST}"
${ECHO} "        VX_VAR = ${VX_VAR_LIST}"
${ECHO} "   DOMAIN_LIST = ${DOMAIN_LIST}"
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
${ECHO} "FCST_TIME=${FCST_TIME}"

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

########################################################################
# Compute VX date - only need to calculate once
########################################################################

# Compute the verification date
YYYYMMDD=`${ECHO} ${START_TIME} | ${CUT} -c1-8`
MMDD=`${ECHO} ${START_TIME} | ${CUT} -c5-8`
HHMMSS=`${DATAROOT}/exec/da_advance_time.exe ${START_TIME} 0 -F hhnnss`  # CSS
HH=`${ECHO} ${START_TIME} | ${CUT} -c9-10`
VDATE=`${DATAROOT}/exec/da_advance_time.exe ${START_TIME} +${FCST_TIME}`
VYYYYMMDD=`${ECHO} ${VDATE} | ${CUT} -c1-8`
VYYYY=`${ECHO} ${VDATE} | ${CUT} -c1-4`
VMM=`${ECHO} ${VDATE} | ${CUT} -c5-6`
VDD=`${ECHO} ${VDATE} | ${CUT} -c7-8`
VHH=`${ECHO} ${VDATE} | ${CUT} -c9-10`
VHHMMSS=`${DATAROOT}/exec/da_advance_time.exe ${VDATE} 0 -F hhnnss`
${ECHO} 'valid time for ' ${FCST_TIME} 'h forecast = ' ${VDATE}

########################################################################
# Run ascii2nc on EPIC files - only need to run once
########################################################################

# Go to processed nc dir
metnc=${RAW_OBS}/${VX_OBS}
${MKDIR} -p ${metnc}

# Create a ascii2nc output file name
OBS_FILE=${metnc}/${VX_OBS}_${VDATE}_${VX_VAR}.nc

if [ ! -e ${OBS_FILE} ]; then

  # List observation file to be run through ascii2nc
  ASCII_FILE=`${LS} ${RAW_OBS}/${VX_OBS}/ascii_${VDATE}_${VX_VAR}.txt | head -1`
  if [ -z "${ASCII_FILE}" ]; then
    echo "ERROR: Could not find observation file: ${ASCII_FILE}"
    exit 1
  fi

  # Call ASCII2NC
  echo "CALLING: ${MET_EXE_ROOT}/ascii2nc ${ASCII_FILE} ${OBS_FILE} -v 2"

  ${MET_EXE_ROOT}/ascii2nc ${ASCII_FILE} ${OBS_FILE} -v 2

fi

########################################################################
# Run point stat for each domain 
########################################################################

# Loop through the domain list
for DOMAIN in ${DOMAIN_LIST}; do
   
   export DOMAIN
   export ${GRID_VX}
   ${ECHO} "DOMAIN=${DOMAIN}"
   ${ECHO} "GRID_VX=${GRID_VX}"
   ${ECHO} "FCST_TIME=${FCST_TIME}"

   # Specify new mask directory structure
   MASKS=${MET_CONFIG}/masks
   export MASKS

   # Specify the MET Point-Stat configuration files to be used
   CONFIG_TCDC="${MET_CONFIG}/PointStatConfig_TCDC"
   CONFIG_TCDC_MPR="${MET_CONFIG}/PointStatConfig_TCDC_MPR"

   # Make sure the Point-Stat configuration files exists
   if [ ! -e ${CONFIG_TCDC} ]; then
       ${ECHO} "ERROR: ${CONFIG_TCDC} does not exist!"
       exit 1
   fi

   if [ ! -e ${CONFIG_TCDC_MPR} ]; then
       ${ECHO} "ERROR: ${CONFIG_TCDC_MPR} does not exist!"
       exit 1
   fi

   # Check the observation file (created from previous command to run ascii2nc)
   ${ECHO} "OBS_FILE: ${OBS_FILE}"

   if [ ! -e ${OBS_FILE} ]; then
     ${ECHO} "ERROR: Could not find observation file: ${OBS_FILE}"
     exit 1
   fi

   # Get the forecast to verify
   if [ ${FCST_TIME} == "09" ]; then
       if [ ${MODEL} == "GFS" ]; then
	   FCST_HRS=$(printf "%03d" ${FCST_TIME##+(0)})  #for GFS name
	   FCST_FILE=${FCST_DIR}/${START_TIME}/gfs.0p25.${START_TIME}.f${FCST_HRS}.grib2
	   FCST_TIME=$(printf "%01d" ${FCST_TIME##+(0)})
       elif [ ${MODEL} == "GALWEM" ]; then
	   FCST_HRS=$(printf "%03d" ${FCST_TIME})
	   FCST_FILE=${FCST_DIR}/${MMDD}/GPP_17km_combined_${YYYYMMDD}_CY${HH}_FH${FCST_HRS}.GR2
       else
           ${ECHO} "ERROR: MODEL = $MODEL not currently supported"
           exit 1
       fi
   else
       if [ ${MODEL} == "GFS" ]; then
           FCST_HRS=$(printf "%03d" ${FCST_TIME})
	   FCST_FILE=${FCST_DIR}/${START_TIME}/gfs.0p25.${START_TIME}.f${FCST_HRS}.grib2
       elif [ ${MODEL} == "GALWEM" ]; then
           FCST_HRS=$(printf "%03d" ${FCST_TIME})
	   FCST_FILE=${FCST_DIR}/${MMDD}/GPP_17km_combined_${YYYYMMDD}_CY${HH}_FH${FCST_HRS}.GR2
       else
           ${ECHO} "ERROR: MODEL = $MODEL not currently supported"
           exit 1
       fi
   fi
   
   if [ ! -e ${FCST_FILE} ]; then
     ${ECHO} "ERROR: Could not find forecast file: ${FCST_FILE}"
     exit 1
   fi

   #######################################################################
   #
   #  Run Point-Stat
   #
   #######################################################################

   # Verify TCDC variables for each forecast hour
   CONFIG_FILE=${CONFIG_TCDC}

   ${MKDIR} -p ${workdir}/${VX_VAR}/${VX_OBS}
   cd ${workdir}/${VX_VAR}/${VX_OBS}

   ${ECHO} "CALLING: ${MET_EXE_ROOT}/point_stat ${FCST_FILE} ${OBS_FILE} ${CONFIG_FILE} -outdir . -v 2"

   /usr/bin/time ${MET_EXE_ROOT}/point_stat ${FCST_FILE} ${OBS_FILE} ${CONFIG_FILE} \
      -outdir . -v 2

   error=$?
   if [ ${error} -ne 0 ]; then
     ${ECHO} "ERROR: For ${MODEL}, ${MET_EXE_ROOT}/point_stat ${CONFIG_FILE} crashed  Exit status: ${error}"
     exit ${error}
   fi

   # Create MPR file for TCDC variables for each forecast hour
   CONFIG_FILE=${CONFIG_TCDC_MPR}

   ${MKDIR} -p ${workdir}/${VX_VAR}/${VX_OBS}
   cd ${workdir}/${VX_VAR}/${VX_OBS}

   ${ECHO} "CALLING: ${MET_EXE_ROOT}/point_stat ${FCST_FILE} ${OBS_FILE} ${CONFIG_FILE} -outdir . -v 2"

   /usr/bin/time ${MET_EXE_ROOT}/point_stat ${FCST_FILE} ${OBS_FILE} ${CONFIG_FILE} \
      -outdir . -v 2

   error=$?
   if [ ${error} -ne 0 ]; then
     ${ECHO} "ERROR: For ${MODEL}, ${MET_EXE_ROOT}/point_stat ${CONFIG_FILE} crashed  Exit status: ${error}"
     exit ${error}
   fi

done # Domain loop

done #VX_VAR loop

done #VX_OBS loop

done #FCST_TIME loop

##########################################################################

${ECHO} "met_point_driver.ksh completed at `${DATE}`"

exit 0

