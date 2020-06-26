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
CP=/bin/cp
CUT=`which cut`
DATE=/bin/date

source /glade/u/apps/ch/modulefiles/default/localinit/localinit.sh
module purge
module use /glade/p/ral/jntp/MET/MET_releases/modulefiles
module load met/8.1_python
ncar_pylib

# Vars used for manual testing of the script
#export START_TIME=2017060506
#export FCST_TIME_LIST="00" #"06 12" 
#export VX_OBS_LIST="EPIC"
#export VX_VAR_LIST="Cloud_Mask"
#export DOMAIN_LIST="global"
#export GRID_VX="NONE"
#export MET_EXE_ROOT=/glade/p/ral/jntp/MET/MET_releases/8.1_python/bin
#export MET_CONFIG=/glade/scratch/`whoami`/cloud_vx/static/MET/met_config
#export DATAROOT=/glade/scratch/`whoami`/cloud_vx
#export FCST_DIR=/glade/scratch/schwartz/GALWEM
#export RAW_OBS=/glade/scratch/schwartz/OBS
#export MODEL="ERA5" #"GALWEM" # or even "ERA5" "SATCORPS" "MERRA2" , "GFS" #"hrconus"

#export DO_MPR="BOTH" # BOTH, STAT, NONE for MPR line_type
export DO_MPR=${DO_MPR:-"NONE"}

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

if [ ${VX_OBS} == "EPIC" ]; then

  # Go to processed nc dir
  metnc=${RAW_OBS}/${VX_OBS}
  ${MKDIR} -p ${metnc}

  # Create a ascii2nc output file name
  OBS_FILE=${metnc}/${VX_OBS}_${VDATE}_${VX_VAR}.nc

  if [ ! -e ${OBS_FILE} ]; then

    # List observation file to be run through ascii2nc
    ASCII_FILE=`${LS} ${RAW_OBS}/${VX_OBS}/ascii_${VDATE}_${VX_VAR}.txt | head -1`
    if [ -z "${ASCII_FILE}" ]; then
      ${ECHO} "ERROR: Could not find observation file: ${ASCII_FILE}"
      exit 1
    fi

    # Call ASCII2NC
    ${ECHO} "CALLING: ${MET_EXE_ROOT}/ascii2nc ${ASCII_FILE} ${OBS_FILE} -v 2"

    ${MET_EXE_ROOT}/ascii2nc ${ASCII_FILE} ${OBS_FILE} -v 2
  fi

elif [ ${VX_OBS} == "CALIPSO" ]; then
# echo BJJ
 # ADD lidar2nc and NCL pre-processing here ?
 # it might be hard...
 # put as a separate script in github...

  # Set OBS_FILE
  OBS_FILE=`${LS} -d /glade/scratch/bjung/calipso/hourly/${VDATE}/*.nc | xargs -n1`
  # TODO: BJJ~ Use metnc to be /glade/scratch/schwartz/OBS/ CALIPSO 
  #            then OBS_FILE =`${LS} ${metnc}/hourly/${VDATE}/*.nc`
  ## Go to processed nc dir
  #metnc=${RAW_OBS}/${VX_OBS}

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

   # Specify new mask directory structure #BJJ: Not used in point_stat config.
   MASKS=${MET_CONFIG}/masks
   export MASKS

   # Specify the MET Point-Stat configuration files to be used
   CONFIG_TCDC="${MET_CONFIG}/PointStatConfig_TCDC.${VX_OBS}"

   # Make sure the Point-Stat configuration files exists
   if [ ! -e ${CONFIG_TCDC} ]; then
       ${ECHO} "ERROR: ${CONFIG_TCDC} does not exist!"
       exit 1
   fi

   # Check the observation file (created from previous command to run ascii2nc)
   ${ECHO} "OBS_FILE: ${OBS_FILE}"

   if [ ${VX_OBS} == "EPIC" ]; then
       if [ ! -e ${OBS_FILE} ]; then
       ${ECHO} "ERROR: Could not find observation file: ${OBS_FILE}"
       exit 1
       fi
   elif [ ${VX_OBS} == "CALIPSO" ]; then
       for f in $( ${LS} ${OBS_FILE} )
       do
           if [ ! -e $f ]; then
           ${ECHO} "ERROR: Could not find observation file: $f"
           exit 1
           fi
       done
   fi

   # Get the forecast to verify
   if [ ${FCST_TIME} == "09" ]; then # Need some weird logic for FCST_TIME = 09
       FCST_HRS=$(printf "%03d" ${FCST_TIME##+(0)})  #3-digit hour for GFS name
       FCST_TIME=$(printf "%01d" ${FCST_TIME##+(0)}) #1-digit...this line probably not needed
   else
       FCST_HRS=$(printf "%03d" ${FCST_TIME})  #3-digit hour for GFS name
   fi

   if [ ${MODEL} == "GFS" ]; then
       FCST_FILE=${FCST_DIR}/${START_TIME}/gfs.0p25.${START_TIME}.f${FCST_HRS}.grib2
   elif [ ${MODEL} == "GALWEM" ]; then
       FCST_FILE=${FCST_DIR}/${MMDD}/GPP_17km_combined_${YYYYMMDD}_CY${HH}_FH${FCST_HRS}.GR2
   elif  [ ${MODEL} == "SATCORPS" ]; then
       JDAY=`${DATAROOT}/exec/da_advance_time.exe  ${VDATE} 0 -j | awk '{print $2}'`  #for SATCORPS name
       FCST_FILE=${RAW_OBS}/${MODEL}/prod.Global-GEO.visst-grid-netcdf.${VYYYY}${VMM}${VDD}.GEO-MRGD.${VYYYY}${JDAY}.${VHH}00.GRID.NC
   elif  [ ${MODEL} == "MERRA2" ]; then
       TMP=`${DATAROOT}/exec/da_advance_time.exe ${VDATE} +30min`  #TODO: 30 min offset
       TMP_YYYYMMDD=`${ECHO} ${TMP} | cut -c1-8`
       TMP_HHMM=`${ECHO} ${TMP} | cut -c9-12`
       FCST_FILE=${RAW_OBS}/${MODEL}/${MODEL}_400.tavg1_2d_${TMP_YYYYMMDD}_${TMP_HHMM}.nc4
   elif  [ ${MODEL} == "ERA5" ]; then
       FCST_FILE=${RAW_OBS}/${MODEL}/${MODEL}_${VDATE}.nc
   else
       ${ECHO} "ERROR: MODEL = $MODEL not currently supported"
       exit 1
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

   # Do we need python embedding?
   if [ ${MODEL} == "GALWEM" ]; then  # process as GRIB2
       FCST_FILE_ARG="${FCST_FILE}"
       export FCST_FIELD_NAME="TCDC"
   else                               # Do python embedding
       scriptName=./python_embedding.py
       FCST_FILE_ARG="PYTHON_NUMPY"
       export FCST_FIELD_NAME=$scriptName #"python_embedding.py"

       if [ ${VX_OBS} == "EPIC" ]; then
           VX_VAR_PYEMBED='binaryCloud' #BJJ hard-wired.
       else
           VX_VAR_PYEMBED=${VX_VAR}
       fi

       dataFile=${FCST_FILE}
       dataSource=${MODEL}
       ${CP} ${DATAROOT}/bin/python_stuff.py .
       ${ECHO} "Python script=$scriptName"
       cat > $scriptName << EOF
import os
import numpy as np
import datetime as dt
import python_stuff  # this is where all the work is done

dataFile = '$dataFile'
dataSource = '$dataSource'
variable = '$VX_VAR_PYEMBED'

met_data = python_stuff.getDataArray(dataFile,dataSource,variable,2)

# TODO: This is for "obs". If we ingest forecast later, we need to improve this.
#attrs = python_stuff.getAttrArray(dataSource,variable,'${YYYYMMDD}','${HHMMSS}','${VYYYYMMDD}','${VHHMMSS}','${VHHMMSS}') # CSS this seems more correct???
attrs = python_stuff.getAttrArray(dataSource,variable,'${START_TIME}','${VDATE}')
EOF
   fi

   # run point-stat according to VX_OBS
   if [ ${VX_OBS} == "EPIC" ]; then
       ${ECHO} "CALLING: ${MET_EXE_ROOT}/point_stat ${FCST_FILE_ARG} ${OBS_FILE} ${CONFIG_FILE} -outdir . -v 3"
       /usr/bin/time ${MET_EXE_ROOT}/point_stat ${FCST_FILE_ARG} ${OBS_FILE} ${CONFIG_FILE} -outdir . -v 3

       error=$?
       if [ ${error} -ne 0 ]; then
         ${ECHO} "ERROR: For ${MODEL}, ${MET_EXE_ROOT}/point_stat ${CONFIG_FILE} crashed  Exit status: ${error}"
         exit ${error}
       fi

   elif [ ${VX_OBS} == "CALIPSO" ]; then
#!----big chunk
       #Search Obs Files
       ls_ofile=`${LS} -d /glade/scratch/bjung/calipso/hourly/${VDATE}/*.nc | xargs -n1` # multiple obs files are related to single model file at valid time.
                 #BJJ: TODO use same syntax with OBS_FILE in line 176
       ${ECHO} $ls_ofile

       rm -rf out1 out2 out3
       nofile=1  # Index for files starts from "1", ALSO Assuming there are up-to three calipso files for each hourly time slot.
       for ofile in $ls_ofile; do
          export OBS_FILE=${ofile}
          ${ECHO} $FCST_FILE $OBS_FILE

          mkdir -p out$nofile

          ${ECHO} "CALLING: ${MET_EXE_ROOT}/point_stat ${FCST_FILE_ARG} ${OBS_FILE} ${CONFIG_FILE} -outdir out$nofile -v 3"
          /usr/bin/time ${MET_EXE_ROOT}/point_stat ${FCST_FILE_ARG} $OBS_FILE ${CONFIG_FILE} -outdir out$nofile -v 3

       ((nofile++))
       done

       #Aggregate
       LEADHRS=`python -c "print ( \"%02d\" % int(\"$FCST_TIME\") )"`"0000"
       #echo $LEADHRS
       fname_head=point_stat_${MODEL}_F${FCST_TIME}_${VX_VAR}_${LEADHRS}L_${VYYYYMMDD}_${VHHMMSS}V
       #stat_analysis -lookin out1 out2 out3 -job aggregate      -line_type MPR -out_line_type MPR -by FCST_LEAD,VX_MASK -out_stat out_${MODEL}/${fname_head}_mpr.txt #BJJ THIS DOES NOT WORK.
       mv out1/${fname_head}_mpr.txt ./${fname_head}_mpr.txt1 2>/dev/null
       mv out2/${fname_head}_mpr.txt ./${fname_head}_mpr.txt2 2>/dev/null
       mv out3/${fname_head}_mpr.txt ./${fname_head}_mpr.txt3 2>/dev/null
       stat_analysis -lookin out1 out2 out3 -job aggregate      -line_type PCT -out_line_type PCT -by FCST_LEAD,VX_MASK -out_stat ./${fname_head}_pct.txt
       stat_analysis -lookin out1 out2 out3 -job aggregate_stat -line_type PCT -out_line_type PRC -by FCST_LEAD,VX_MASK -out_stat ./${fname_head}_prc.txt
       rm -rf out1 out2 out3

#!----end chunk
   fi


done # Domain loop

done #VX_VAR loop

done #VX_OBS loop

done #FCST_TIME loop

##########################################################################

${ECHO} "met_point_driver.ksh completed at `${DATE}`"

exit 0

