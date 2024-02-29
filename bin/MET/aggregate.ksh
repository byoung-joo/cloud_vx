#!/bin/ksh -l
#PBS -S /bin/ksh
#PBS -N test
#PBS -A NMMM0021
#PBS -l walltime=480:00
#PBS -q casper@casper-pbs
#PBS -o ./output_file
#PBS -j oe 
#PBS -l select=1:ncpus=1:mpiprocs=1:mem=40gb
#PBS -m n    
#PBS -M schwartz@ucar.edu
#####PBS -V
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
#              FCST_TIME = The three-digit forecasts that is to be verified.
#            VX_OBS_LIST = A list of observation sources to be used.
#            VX_VAR_LIST = A list of observed variables to be used.
#           MET_EXE_ROOT = The full path of the MET executables.
#             MET_CONFIG = The full path of the MET configuration files.
#               DATAROOT = Top-level data directory of WRF output.
#               FCST_DIR = Directory containing the forecasts to be used.
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
#source /glade/u/apps/ch/modulefiles/default/localinit/localinit.sh  # Cheyenne build
source /glade/u/apps/dav/modulefiles/default/localinit/localinit.sh  # Casper build
module purge
#module use /glade/p/ral/jntp/MET/MET_releases/modulefiles # Cheyenne build
#module load met/9.0
module use /glade/p/ral/jntp/MET/MET_releases/casper/modulefiles #Casper build
module load met/9.0.3
module load ncarenv
ncar_pylib
   # specify full path to local python exectuable...needed such that MET
   # executes the python script with the user's version of python (and environment and loaded packages) rather than the python build
   # defined at MET compilation time.
export MET_PYTHON_EXE=`which python` #export MET_PYTHON_EXE=/glade/u/apps/ch/opt/python/3.6.8/gnu/8.3.0/pkg-library/20200417/bin/python

####

# Vars used for manual testing of the script
export FCST_TIME_LIST="00 24 48 72 96 120 144 168 192" #00 06 12 18 24 30 36 42 48" #"06 09" # 6 9 12 24 36 48"
export VX_OBS_LIST="ERA5" #"SATCORPS MERRA2 ERA5 WWMCA SAT_WWMCA_MEAN"
export VX_VAR_LIST="totalCloudFrac" #"binaryCloud" #lowCloudFrac" #"totalCloudFrac lowCloudFrac midCloudFrac highCloudFrac binaryCloud" # cloudTopTemp cloudTopPres cloudBaseHeight cloudTopHeight
#export MET_EXE_ROOT=/glade/p/ral/jntp/MET/MET_releases/8.1_python/bin
#export MET_EXE_ROOT=/glade/p/ral/jntp/MET/MET_releases/9.0/bin # Cheyenne build
export MET_EXE_ROOT=/glade/p/ral/jntp/MET/MET_releases/casper/9.0.3/exec   # Casper build
export DATAROOT=/glade/scratch/`whoami`/cloud_vx
#export FCST_DIR=/gpfs/u/home/schwartz/cloud_verification/GFS_grib_0.25deg  #GFS model
expt=exp_EnVar_6h_cyc_updatedTiedtkeForcing #_cloudyRad
export FCST_DIR=${DATAROOT}/metprd/${expt}  # MPAS model, 30-km forecasts, interpolated to 0.25 degrees
#export FCST_DIR=/glade/scratch/schwartz/GALWEM                    # GALWEM17 and GALWEM and models (GALWEM 17 is 17-km GALWEM from 2017), "GALWEM" is 0.25 degree from Air Force in 2020-2021
export THRESHOLDS=">0 >=10.0 >=20.0 >=30.0 >=40.0 >=50.0 >=60.0 >=70.0 >=80.0 >=90.0 >SFP20 >SFP30 >SFP40 >SFP50 >SFP60 >SFP70 >SFP80"


# Print run parameters
${ECHO}
${ECHO} "driver_script_with_python.ksh started at `${DATE}`"
${ECHO}
${ECHO} "     FCST_TIME = ${FCST_TIME_LIST}"
${ECHO} "        VX_OBS = ${VX_OBS_LIST}"
${ECHO} "        VX_VAR = ${VX_VAR_LIST}"
${ECHO} "  MET_EXE_ROOT = ${MET_EXE_ROOT}"
${ECHO} "    MET_CONFIG = ${MET_CONFIG}"
${ECHO} "      DATAROOT = ${DATAROOT}"
${ECHO} "      FCST_DIR = ${FCST_DIR}"

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

# Loop through the forecast times
for FCST_TIME in ${FCST_TIME_LIST}; do

# Loop through the veryfing obs dataset
for VX_OBS in ${VX_OBS_LIST}; do

# Loop through the veryfing obs dataset
for VX_VAR in ${VX_VAR_LIST}; do

   ${ECHO} "FCST_TIME=${FCST_TIME}"

    # Get the forecast to verify
    if [ ${FCST_TIME} == "09" ]; then # Need some weird logic for FCST_TIME = 09
        F3=$(printf "%03d" ${FCST_TIME##+(0)})  #3-digit hour
    else
        F3=$(printf "%03d" ${FCST_TIME})  #3-digit hour
    fi


    #######################################################################
    #
    #  Run Grid-Stat
    #
    #######################################################################


	
    # Make final working directory
    outdir=${DATAROOT}/metprd/${expt}/aggregation/f${FCST_TIME}/${VX_VAR}/${VX_OBS}
    ${MKDIR} -p $outdir
    cd $outdir

    for THRESH in $THRESHOLDS; do
       # e.g., 
       #${MET_EXE_ROOT}/stat_analysis \
       #  -lookin /glade/scratch/klupo/cloud_vx/metprd/cold_start/*/f144/totalCloudFrac/ERA5/ \
       #  -job aggregate_stat -vx_mask FULL \
       #  -line_type CTC -out_line_type CTS \ 
       #  -fcst_thresh ">=80.0" -fcst_lead 1440000 -out testf144.out -log testf144.log
       #ls ${FCST_DIR}/*/f${FCST_TIME}/${VX_VAR}/${VX_OBS}
        ${MET_EXE_ROOT}/stat_analysis \
          -lookin ${FCST_DIR}/*/f${FCST_TIME}/${VX_VAR}/${VX_OBS}/ \
          -job aggregate_stat -vx_mask FULL \
          -line_type CTC -out_line_type CTS \
          -fcst_thresh "${THRESH}" -fcst_lead ${F3}0000 -out testf${F3}.out -log testf${F3}.log

	   error=$?
	   if [ ${error} -ne 0 ]; then
	       ${ECHO} "ERROR: ${MET_EXE_ROOT}/stat_analysis crashed  Exit status: ${error}"
	       exit ${error}
	   fi

	   # move the file to its final name
	   if [ `echo $THRESH | cut -c 1-2` == ">=" ]; then
	      t=`echo $THRESH | cut -c 3-`
	   elif [ `echo $THRESH | cut -c 1-4` == ">SFP" ]; then
	      t=`echo $THRESH | cut -c 2-`
	   elif [ `echo $THRESH | cut -c 1-2` == ">0" ]; then
	      t=0.0
	   fi
	   mv testf${F3}.out ./aggregate_stats_f${F3}_thresh_${t}.txt
    done

done #VX_VAR loop

done #VX_OBS loop

done #FCST_TIME loop

##########################################################################

${ECHO} "aggregate.ksh completed at `${DATE}`"

exit 0
