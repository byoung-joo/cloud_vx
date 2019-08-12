#!/bin/ksh
pathnam=/glade/scratch/`whoami`/cloud_vx/xml
pathroc=/glade/u/home/harrop/opt/rocoto/1.2.4-p1

pwd
${pathroc}/bin/rocotorun -w ${pathnam}/cloud_vx.xml -d ${pathnam}/cloud_vx.db -v 10

#/glade/u/home/harrop/opt/rocoto/1.2.4-p1/bin/rocotorun -w /glade/scratch/jwolff/CAF/met/draft_3rd/xml/cloud_vx.xml -d /glade/scratch/jwolff/CAF/met/draft_3rd/xml/cloud_vx.db -v 10
