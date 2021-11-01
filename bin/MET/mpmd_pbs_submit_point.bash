#!/bin/bash
#PBS -A NMMM0015
#PBS -N MET_verification_point
#PBS -j oe
#PBS -k eod
#PBS -m abe
#PBS -q regular
#PBS -l walltime=01:00:00
### Request one chunk with ncpus and mpiprocs set to
### the number of lines in the command file
#PBS -l select=1:ncpus=9:mpiprocs=9

export TMPDIR=/glade/scratch/$USER/temp
mkdir -p $TMPDIR

# yyyy-mm-dd Context: Cheyenne MPT command file job. 
# Do not propagate this use of MPI_SHEPHERD
# to other MPT jobs as it may cause
# significant slowdown or timeout.
# Contact the CISL Consulting Services Group
# if you have questions about this.
export MPI_SHEPHERD=true

mkdir -p log
mpiexec_mpt launch_cf.sh mpmd_cmdfile_point
