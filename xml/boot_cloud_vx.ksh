#!/bin/ksh
pathnam=REL_DIR/xml
pathroc=/glade/u/home/harrop/opt/rocoto/1.2.4-p1

cycle=201811010000
metatask="point_stat"

pwd
${pathroc}/bin/rocotoboot -w ${pathnam}/cloud_vx.xml -d ${pathnam}/cloud_vx.db -c ${cycle} -m ${metatask}

#/glade/u/home/harrop/opt/rocoto/1.2.4-p1/bin/rocotoboot -w /glade/scratch/jwolff/CAF/met/draft_3rd_cs/xml/cloud_vx.xml -d /glade/scratch/jwolff/CAF/met/draft_3rd_cs/xml/cloud_vx.db -c 201811010000 -m point_stat
