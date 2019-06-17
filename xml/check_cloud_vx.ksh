#!/bin/ksh
pathnam=REL_DIR/xml
pathroc=/glade/u/home/harrop/opt/rocoto/1.2.4-p1

pwd

cycle="201811010000"
#task="grid_stat_MERRA2_lowCloudFrac_03"
#task="point_stat_EPIC_Cloud_Mask_00"
task="grid_stat_SATCORPS_totalCloudFrac_03"

${pathroc}/bin/rocotocheck -w ${pathnam}/cloud_vx.xml -d ${pathnam}/cloud_vx.db -c ${cycle} -t ${task}

#/glade/u/home/harrop/opt/rocoto/1.2.4-p1/bin/rocotocheck -w /glade/scratch/jwolff/CAF/met/draft_3rd/xml/cloud_vx.xml -d /glade/scratch/jwolff/CAF/met/draft_3rd/xml/cloud_vx.db -c 201811010000 -t grid_stat_MERRA2_lowCloudFrac_03
